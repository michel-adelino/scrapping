# Concurrency Configuration Guide

## Understanding the Error: "Execution context was destroyed"

This error occurs when:
1. A page navigates/refreshes while JavaScript is being executed
2. High concurrency causes race conditions
3. Browser instances are overwhelmed

## Recommended Concurrency Settings

### For 100 Workers (Your Current Setup)

**Optimal Configuration:**
```bash
# Celery Worker Service
--concurrency=100  # You set this correctly

# Browser Semaphore (in browser_utils.py)
_browser_semaphore = threading.Semaphore(35)  # 35 browsers for 100 workers
```

**Why 35 browsers?**
- Each browser uses ~100-200MB RAM
- 35 browsers × 200MB = ~7GB RAM (safe for most servers)
- Each browser can handle 2-3 concurrent contexts efficiently
- 35 × 3 = 105 tasks can run simultaneously

### Memory Calculation

```
Total RAM needed = (Browser Count × 200MB) + (Worker Count × 50MB) + System Overhead
                 = (35 × 200MB) + (100 × 50MB) + 2GB
                 = 7GB + 5GB + 2GB = ~14GB minimum
```

**If you have less RAM:**
- Reduce browser semaphore: `_browser_semaphore = threading.Semaphore(20)`
- Reduce worker concurrency: `--concurrency=50`

### Performance vs Selenium

**Playwright is MORE efficient than Selenium:**
- ✅ Lower memory usage per browser (~100-200MB vs ~300-500MB for Selenium)
- ✅ Faster execution (better browser automation)
- ✅ Better error handling
- ✅ More stable with high concurrency

**However**, with 100 concurrent workers, you're hitting system limits, not Playwright limits.

## Troubleshooting High Concurrency

### 1. Check System Resources

```bash
# Check memory usage
free -h

# Check CPU usage
top

# Check file descriptors
ulimit -n
# If too low, increase: ulimit -n 65536
```

### 2. Monitor Browser Creation

Watch the logs for:
```
[BROWSER] Waiting for available browser instance slot...
```

If you see this frequently, increase the semaphore limit.

### 3. Handle Navigation Errors

The code now includes automatic retry for navigation errors. If you still see errors:

**Option A: Reduce Concurrency**
```bash
# In systemd service file
--concurrency=50  # Instead of 100
```

**Option B: Increase Browser Limit**
```python
# In browser_utils.py
_browser_semaphore = threading.Semaphore(50)  # More browsers
```

**Option C: Add Delays**
Add small delays between operations in scrapers to reduce race conditions.

### 4. Optimal Settings by Server Size

| Server RAM | Workers | Browsers | Semaphore |
|------------|---------|----------|-----------|
| 8GB        | 20      | 10       | 10        |
| 16GB       | 50      | 20       | 20        |
| 32GB       | 100     | 35       | 35        |
| 64GB       | 200     | 70       | 70        |

## Current Fixes Applied

1. ✅ **Increased semaphore** to 35 (from 10)
2. ✅ **Added retry logic** for navigation errors in `base_scraper.py`
3. ✅ **Better error handling** in `swingers.py` for `window.stop()`

## Testing Your Configuration

1. Start with lower concurrency:
   ```bash
   --concurrency=50
   ```

2. Monitor for errors:
   ```bash
   sudo journalctl -u backend-scraper-celery-worker -f | grep ERROR
   ```

3. Gradually increase if stable:
   ```bash
   --concurrency=75
   --concurrency=100
   ```

4. If errors persist, increase browser semaphore:
   ```python
   _browser_semaphore = threading.Semaphore(50)
   ```

## Summary

- **100 workers is aggressive** - requires ~14GB+ RAM
- **35 browsers is a good balance** for 100 workers
- **Playwright is more efficient** than Selenium
- **Navigation errors are now handled** with retry logic
- **Monitor your system resources** and adjust accordingly

