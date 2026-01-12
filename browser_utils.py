"""
Playwright browser management utilities
Replaces Selenium driver creation with Playwright browser instances
"""
import threading
import platform
import logging
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional

logger = logging.getLogger(__name__)

# Semaphore to limit concurrent browser instances (prevents resource exhaustion)
# 
# IMPORTANT: Each browser instance uses ~100-200MB RAM
# Recommended limits:
#   - 100 workers: 30-40 browsers (3-4 workers per browser is safe)
#   - 50 workers: 20-25 browsers  
#   - 10 workers: 10 browsers
#
# You can increase this if you have more RAM, but watch for:
#   - Memory exhaustion (check with: free -h)
#   - File descriptor limits (check with: ulimit -n)
#   - CPU saturation
_browser_semaphore = threading.Semaphore(15)  

# Global Playwright instance (one per process)
_playwright_instance = None
_playwright_lock = threading.Lock()


def get_playwright():
    """Get or create the global Playwright instance"""
    global _playwright_instance
    with _playwright_lock:
        if _playwright_instance is None:
            _playwright_instance = sync_playwright().start()
        return _playwright_instance


def create_browser(headless: bool = None, **kwargs) -> Browser:
    """
    Create a Playwright browser instance with proper configuration.
    
    Args:
        headless: Whether to run in headless mode. If None, auto-detect based on platform.
        **kwargs: Additional browser launch arguments
    
    Returns:
        Browser instance
    """
    import time
    
    # Acquire semaphore to limit concurrent browser instances
    logger.info("[BROWSER] Waiting for available browser instance slot...")
    _browser_semaphore.acquire()
    
    try:
        # Auto-detect headless mode if not specified
        if headless is None:
            # On Linux, default to headless. On Windows/Mac, default to headed for debugging
            headless = platform.system() == 'Linux'
        
        playwright = get_playwright()
        
        # Browser launch arguments
        launch_args = {
            'headless': headless,
            'args': [
                '--no-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-software-rasterizer',
            ]
        }
        
        # Add any additional launch arguments
        launch_args.update(kwargs)
        
        logger.info(f"[BROWSER] Creating Chromium browser (headless={headless})...")
        browser = playwright.chromium.launch(**launch_args)
        
        # On Linux, wait a moment for browser to fully initialize
        if platform.system() == 'Linux':
            time.sleep(1)
        
        logger.info("[BROWSER] Browser created successfully")
        
        # Store semaphore release in browser cleanup
        original_close = browser.close
        def close_with_semaphore_release():
            try:
                original_close()
            finally:
                _browser_semaphore.release()
                logger.info("[BROWSER] Released browser instance slot")
        browser.close = close_with_semaphore_release
        
        return browser
        
    except Exception as e:
        _browser_semaphore.release()
        logger.error(f"[BROWSER] Failed to create browser: {e}")
        raise


def create_browser_context(browser: Browser, **kwargs) -> BrowserContext:
    """
    Create a browser context with default settings.
    
    Args:
        browser: Browser instance
        **kwargs: Additional context options
    
    Returns:
        BrowserContext instance
    """
    context_options = {
        'viewport': {'width': 1920, 'height': 1080},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    context_options.update(kwargs)
    
    logger.info("[BROWSER] Creating browser context...")
    context = browser.new_context(**context_options)
    logger.info("[BROWSER] Browser context created")
    
    return context


def create_page(context: BrowserContext, timeout: int = 30000) -> Page:
    """
    Create a page with default timeout settings.
    
    Args:
        context: BrowserContext instance
        timeout: Page load timeout in milliseconds (default 30 seconds)
    
    Returns:
        Page instance
    """
    page = context.new_page()
    page.set_default_timeout(timeout)
    page.set_default_navigation_timeout(timeout)
    logger.info(f"[BROWSER] Page created with timeout {timeout}ms")
    return page


def create_browser_with_context(headless: bool = None, **kwargs):
    """
    Convenience function to create both browser and context.
    
    Args:
        headless: Whether to run in headless mode
        **kwargs: Additional options for browser or context
            - Context options: user_agent, viewport, etc.
            - Browser launch options: args, etc.
    
    Returns:
        Tuple of (Browser, BrowserContext)
    """
    # Separate context options from browser launch options
    context_options = {}
    browser_options = {}
    
    # Known context options that should not be passed to browser.launch()
    context_only_keys = {'user_agent', 'viewport', 'locale', 'timezone_id', 'geolocation', 
                        'permissions', 'color_scheme', 'reduced_motion', 'forced_colors',
                        'accept_downloads', 'has_touch', 'is_mobile', 'device_scale_factor',
                        'screen', 'extra_http_headers', 'http_credentials', 'ignore_https_errors',
                        'bypass_csp', 'java_script_enabled', 'bypass_csp', 'record_video',
                        'record_har_path', 'storage_state', 'base_url', 'tracing'}
    
    for key, value in kwargs.items():
        if key in context_only_keys:
            context_options[key] = value
        else:
            browser_options[key] = value
    
    browser = create_browser(headless=headless, **browser_options)
    context = create_browser_context(browser, **context_options)
    return browser, context

