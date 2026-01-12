#!/usr/bin/env python3
"""
Script to clear all caches and reset the system to a fresh state.

This script clears:
1. Redis cache (Celery task queue and results)
2. Python __pycache__ directories
3. In-memory caches (e.g., PRODUCT_PRICE_CACHE)
4. Database (optional - availability slots and scraping tasks)
5. Browser cache (Playwright browser data)

Usage:
    python clear_all_cache.py                    # Clear all except database
    python clear_all_cache.py --clear-db         # Also clear database
    python clear_all_cache.py --clear-db --force # Skip confirmation prompts
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
NC = '\033[0m'  # No Color

def print_step(message):
    print(f"{BLUE}→ {message}{NC}")

def print_success(message):
    print(f"{GREEN}✓ {message}{NC}")

def print_warning(message):
    print(f"{YELLOW}⚠ {message}{NC}")

def print_error(message):
    print(f"{RED}✗ {message}{NC}")

def clear_redis_cache():
    """Clear Redis cache (Celery task queue and results)"""
    print_step("Clearing Redis cache...")
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        # Parse Redis URL
        if redis_url.startswith('redis://'):
            redis_url = redis_url.replace('redis://', '')
            if '/' in redis_url:
                host_port, db = redis_url.rsplit('/', 1)
                db = int(db)
            else:
                host_port = redis_url
                db = 0
            
            if ':' in host_port:
                host, port = host_port.split(':')
                port = int(port)
            else:
                host = host_port
                port = 6379
        else:
            host = 'localhost'
            port = 6379
            db = 0
        
        r = redis.Redis(host=host, port=port, db=db, decode_responses=False)
        
        # Flush the database
        r.flushdb()
        print_success(f"Redis cache cleared (database {db})")
        return True
    except ImportError:
        print_warning("Redis Python library not installed. Trying redis-cli command...")
        try:
            # Try using redis-cli command
            result = subprocess.run(['redis-cli', 'FLUSHDB'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print_success("Redis cache cleared using redis-cli")
                return True
            else:
                print_error(f"redis-cli failed: {result.stderr}")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print_error(f"Could not clear Redis cache: {e}")
            print_warning("Make sure Redis is running and redis-cli is available")
            return False
    except Exception as e:
        print_error(f"Error clearing Redis cache: {e}")
        return False

def clear_pycache():
    """Clear Python __pycache__ directories"""
    print_step("Clearing Python __pycache__ directories...")
    
    base_dir = Path(__file__).parent
    pycache_dirs = []
    pyc_files = []
    
    # Find all __pycache__ directories and .pyc files
    for root, dirs, files in os.walk(base_dir):
        # Skip virtual environments
        if 'venv' in root or 'env' in root or '.venv' in root:
            continue
        
        if '__pycache__' in root:
            pycache_dirs.append(root)
        
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                pyc_files.append(os.path.join(root, file))
    
    # Remove __pycache__ directories
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
        except Exception as e:
            print_warning(f"Could not remove {pycache_dir}: {e}")
    
    # Remove .pyc files
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
        except Exception as e:
            print_warning(f"Could not remove {pyc_file}: {e}")
    
    total_cleared = len(pycache_dirs) + len(pyc_files)
    if total_cleared > 0:
        print_success(f"Cleared {len(pycache_dirs)} __pycache__ directories and {len(pyc_files)} .pyc files")
    else:
        print_success("No Python cache files found")

def clear_in_memory_caches():
    """Clear in-memory caches (like PRODUCT_PRICE_CACHE)"""
    print_step("Clearing in-memory caches...")
    
    # This would require importing the modules and clearing their caches
    # For now, we'll note that a restart is needed
    print_warning("In-memory caches (e.g., PRODUCT_PRICE_CACHE) will be cleared when services restart")
    print_warning("Restart Celery workers and Flask app to clear in-memory caches")

def clear_database(force=False):
    """Clear database (availability slots and scraping tasks)"""
    print_step("Clearing database...")
    
    try:
        from app import app, db
        from models import AvailabilitySlot, ScrapingTask
        
        with app.app_context():
            # Count records before deletion
            slots_count = AvailabilitySlot.query.count()
            tasks_count = ScrapingTask.query.count()
            
            if not force:
                response = input(f"This will delete {slots_count} availability slots and {tasks_count} scraping tasks. Continue? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print_warning("Database clearing cancelled")
                    return False
            
            # Delete all records
            AvailabilitySlot.query.delete()
            ScrapingTask.query.delete()
            db.session.commit()
            
            print_success(f"Database cleared: {slots_count} slots and {tasks_count} tasks deleted")
            return True
    except Exception as e:
        print_error(f"Error clearing database: {e}")
        return False

def clear_browser_cache():
    """Clear Playwright browser cache"""
    print_step("Clearing Playwright browser cache...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        # Playwright stores browser data in user data directory
        # On Windows: %USERPROFILE%\AppData\Local\ms-playwright
        # On Linux/Mac: ~/.cache/ms-playwright
        
        if sys.platform == 'win32':
            cache_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright'
        else:
            cache_dir = Path.home() / '.cache' / 'ms-playwright'
        
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print_success(f"Playwright browser cache cleared: {cache_dir}")
            except Exception as e:
                print_warning(f"Could not remove browser cache directory: {e}")
                print_warning("You may need to manually delete it or restart the system")
        else:
            print_success("No Playwright browser cache found")
        
        return True
    except ImportError:
        print_warning("Playwright not installed or not available")
        return False
    except Exception as e:
        print_error(f"Error clearing browser cache: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Clear all caches and reset system')
    parser.add_argument('--clear-db', action='store_true', 
                       help='Also clear the database (availability slots and tasks)')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')
    args = parser.parse_args()
    
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}  Clearing All Caches - Fresh Start{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    results = {
        'redis': False,
        'pycache': False,
        'memory': True,  # Always true (just a warning)
        'database': False,
        'browser': False
    }
    
    # Clear Redis
    results['redis'] = clear_redis_cache()
    print()
    
    # Clear Python cache
    results['pycache'] = clear_pycache()
    print()
    
    # Clear in-memory caches (just a note)
    clear_in_memory_caches()
    print()
    
    # Clear browser cache
    results['browser'] = clear_browser_cache()
    print()
    
    # Clear database if requested
    if args.clear_db:
        results['database'] = clear_database(force=args.force)
        print()
    else:
        print_warning("Database not cleared (use --clear-db to also clear database)")
        print()
    
    # Summary
    print(f"{BLUE}{'='*60}{NC}")
    print(f"{BLUE}  Summary{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")
    
    for cache_type, success in results.items():
        if cache_type == 'memory':
            continue  # Skip memory (it's just a warning)
        status = "✓ Cleared" if success else "✗ Failed"
        color = GREEN if success else RED
        print(f"  {color}{status}{NC} {cache_type.replace('_', ' ').title()}")
    
    print()
    print_warning("IMPORTANT: Restart all services to ensure clean state:")
    print("  1. Stop Celery workers and beat")
    print("  2. Stop Flask app")
    print("  3. Start services again")
    print()
    
    if not args.clear_db:
        print_warning("Database was NOT cleared. Use --clear-db if you want to reset the database too.")
        print()

if __name__ == '__main__':
    main()
