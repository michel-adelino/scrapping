"""
Base scraper class for Playwright-based scrapers
Provides common functionality for all scrapers
"""
from typing import Optional
from playwright.sync_api import Browser, BrowserContext, Page
import logging
from browser_utils import create_browser, create_browser_context, create_page, create_browser_with_context

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper utility class for Playwright-based scrapers"""
    
    def __init__(self, headless: bool = None):
        """
        Initialize the scraper
        
        Args:
            headless: Whether to run browser in headless mode (None = auto-detect)
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def __enter__(self):
        """Context manager entry - creates browser and context"""
        self.browser, self.context = create_browser_with_context(headless=self.headless)
        self.page = create_page(self.context)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleans up browser resources"""
        self.cleanup()
        
    def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                self.page.close()
                self.page = None
        except Exception as e:
            logger.warning(f"Error closing page: {e}")
        
        try:
            if self.context:
                self.context.close()
                self.context = None
        except Exception as e:
            logger.warning(f"Error closing context: {e}")
        
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    # def goto(self, url: str, timeout: int = 60000, wait_until: str = "networkidle"):
    #     """
    #     Navigate to a URL
        
    #     Args:
    #         url: URL to navigate to
    #         timeout: Navigation timeout in milliseconds (default 60s)
    #         wait_until: When to consider navigation successful (load, domcontentloaded, networkidle)
    #     """
    #     if not self.page:
    #         raise RuntimeError("Page not initialized. Use context manager or call setup() first.")
    #     logger.info(f"[SCRAPER] Navigating to {url}")
    #     self.page.goto(url, timeout=timeout, wait_until=wait_until)
    #     # Additional wait to ensure page is fully rendered
    #     self.page.wait_for_load_state("networkidle", timeout=10000)
    #     logger.info(f"[SCRAPER] Page loaded successfully")

    def goto(self, url: str, timeout: int = 30000, wait_until: str = "domcontentloaded"):
        """
        Navigate to a URL safely without forcing networkidle.
        """

        if not self.page:
            raise RuntimeError("Page not initialized. Use context manager or call setup() first.")

        logger.info(f"[SCRAPER] Navigating to {url}")

        try:
            # ONLY do what the caller requests
            self.page.goto(url, timeout=timeout, wait_until=wait_until)
        except Exception as e:
            logger.warning(f"[SCRAPER] goto() navigation warning: {e}")

        # ❌ REMOVE networkidle — SevenRooms NEVER reaches it
        # ❌ REMOVE load-state waits — page stays pending forever
        # ✔ Instead wait a tiny amount to stabilize DOM
        self.page.wait_for_timeout(800)

        logger.info("[SCRAPER] goto() completed (no networkidle wait)")

    
    def wait_for_selector(self, selector: str, timeout: int = 60000, state: str = "visible"):
        """
        Wait for a selector to appear
        
        Args:
            selector: CSS selector or XPath
            timeout: Timeout in milliseconds (default 60s)
            state: Wait state (visible, hidden, attached, detached)
        """
        if not self.page:
            raise RuntimeError("Page not initialized.")
        element = self.page.wait_for_selector(selector, timeout=timeout, state=state)
        # Additional wait to ensure element is stable
        if element:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        return element
    
    def wait_for_timeout(self, milliseconds: int):
        """Wait for a specified amount of time"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        self.page.wait_for_timeout(milliseconds)
    
    def click(self, selector: str, timeout: int = 30000):
        """Click an element"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        self.page.click(selector, timeout=timeout)
    
    def fill(self, selector: str, value: str, timeout: int = 30000):
        """Fill an input field"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        self.page.fill(selector, value, timeout=timeout)
    
    def type(self, selector: str, text: str, delay: int = 0, timeout: int = 30000):
        """Type text into an element"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        self.page.type(selector, text, delay=delay, timeout=timeout)
    
    def select_option(self, selector: str, value: str, timeout: int = 30000):
        """Select an option in a dropdown"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        self.page.select_option(selector, value, timeout=timeout)
    
    def evaluate(self, expression: str):
        """Execute JavaScript in the page context"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        return self.page.evaluate(expression)
    
    def query_selector(self, selector: str):
        """Query a single element"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        return self.page.query_selector(selector)
    
    def query_selector_all(self, selector: str):
        """Query multiple elements"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        return self.page.query_selector_all(selector)
    
    def locator(self, selector: str):
        """Get a locator for an element (Playwright's recommended way)"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        return self.page.locator(selector)
    
    def get_content(self) -> str:
        """Get page HTML content"""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        return self.page.content()

