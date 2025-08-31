import requests
import random
import time
import logging
from typing import List, Optional
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyManager:
    def __init__(self, proxy_list: List[str] = None, max_retries: int = 3):
        self.proxy_list = proxy_list or self._load_proxies_from_env()
        self.max_retries = max_retries
        self.proxy_index = 0
        self.bad_proxies = set()
        self.last_rotation = time.time()
        self.rotation_interval = 300  # Rotate every 5 minutes
        
    def _load_proxies_from_env(self) -> List[str]:
        """Load proxies from environment variables"""
        proxies = []
        
        # Check for single proxy
        single_proxy = os.getenv('SCRAPER_PROXY')
        if single_proxy:
            proxies.append(single_proxy)
            
        # Check for proxy list
        proxy_list_str = os.getenv('SCRAPER_PROXY_LIST')
        if proxy_list_str:
            proxies.extend(proxy_list_str.split(','))
            
        # Check for proxy file
        proxy_file = os.getenv('SCRAPER_PROXY_FILE')
        if proxy_file and os.path.exists(proxy_file):
            try:
                with open(proxy_file, 'r') as f:
                    proxies.extend([line.strip() for line in f if line.strip()])
            except Exception as e:
                logger.error(f"Failed to load proxies from file: {e}")
                
        logger.info(f"Loaded {len(proxies)} proxies")
        return proxies

    def get_proxy(self) -> Optional[str]:
        """Get a random working proxy"""
        if not self.proxy_list:
            logger.warning("No proxies available")
            return None
            
        # Rotate proxies periodically
        current_time = time.time()
        if current_time - self.last_rotation > self.rotation_interval:
            self._rotate_proxies()
            self.last_rotation = current_time
            
        # Try to get a working proxy
        for attempt in range(self.max_retries):
            proxy = self._select_proxy()
            if self._test_proxy(proxy):
                return proxy
            else:
                self.bad_proxies.add(proxy)
                logger.warning(f"Proxy {proxy} failed test, marking as bad")
                
        logger.error("All proxies failed testing")
        return None

    def _select_proxy(self) -> str:
        """Select a proxy from the available list"""
        available_proxies = [p for p in self.proxy_list if p not in self.bad_proxies]
        
        if not available_proxies:
            # Reset bad proxies if all are marked bad
            logger.warning("All proxies marked as bad, resetting bad proxies list")
            self.bad_proxies.clear()
            available_proxies = self.proxy_list
            
        # Round-robin selection
        if self.proxy_index >= len(available_proxies):
            self.proxy_index = 0
            
        proxy = available_proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(available_proxies)
        
        return proxy

    def _test_proxy(self, proxy: str) -> bool:
        """Test if a proxy is working"""
        try:
            test_url = "http://httpbin.org/ip"
            proxies = {
                'http': proxy,
                'https': proxy
            }
            
            response = requests.get(test_url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                logger.info(f"Proxy {proxy} test successful")
                return True
                
        except Exception as e:
            logger.debug(f"Proxy test failed for {proxy}: {e}")
            
        return False

    def _rotate_proxies(self):
        """Rotate to a new set of proxies"""
        logger.info("Rotating proxies")
        # For now, just reset the index and clear some bad proxies
        self.proxy_index = 0
        # Keep only recently bad proxies (clear ones that might be working again)
        self.bad_proxies = set(list(self.bad_proxies)[-10:])  # Keep only last 10 bad proxies

    def add_proxy(self, proxy: str):
        """Add a new proxy to the list"""
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)
            logger.info(f"Added new proxy: {proxy}")

    def remove_proxy(self, proxy: str):
        """Remove a proxy from the list"""
        if proxy in self.proxy_list:
            self.proxy_list.remove(proxy)
        if proxy in self.bad_proxies:
            self.bad_proxies.remove(proxy)
        logger.info(f"Removed proxy: {proxy}")

    def get_proxy_stats(self) -> dict:
        """Get statistics about proxies"""
        return {
            'total_proxies': len(self.proxy_list),
            'working_proxies': len(self.proxy_list) - len(self.bad_proxies),
            'bad_proxies': len(self.bad_proxies),
            'rotation_interval': self.rotation_interval
        }

# Example usage
if __name__ == "__main__":
    # Example proxy list (replace with actual proxies)
    test_proxies = [
        "http://proxy1:port",
        "http://proxy2:port",
        "http://proxy3:port"
    ]
    
    proxy_manager = ProxyManager(proxy_list=test_proxies)
    
    # Get a proxy
    proxy = proxy_manager.get_proxy()
    print(f"Using proxy: {proxy}")
    
    # Get stats
    stats = proxy_manager.get_proxy_stats()
    print(f"Proxy stats: {stats}")