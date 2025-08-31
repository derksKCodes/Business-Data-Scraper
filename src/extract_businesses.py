import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import time
import logging
from typing import List, Set, Tuple
from utils.proxy_manager import ProxyManager
from fake_useragent import UserAgent
from selenium.webdriver.chrome.service import Service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BusinessExtractor:
    def __init__(self, use_proxies=False, headless=True):
        self.use_proxies = use_proxies
        self.headless = headless
        self.proxy_manager = ProxyManager() if use_proxies else None
        self.ua = UserAgent()
        self.business_names = set()
        
    def setup_driver(self):
        """Setup Selenium WebDriver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")  # new headless mode is more stable
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={self.ua.random}")
        
        if self.use_proxies and self.proxy_manager:
            proxy = self.proxy_manager.get_proxy()
            chrome_options.add_argument(f'--proxy-server={proxy}')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def extract_from_static_page(self, url: str, selectors: List[str]) -> Set[str]:
        """Extract business names from a static HTML page"""
        try:
            headers = {'User-Agent': self.ua.random}
            proxy = self.proxy_manager.get_proxy() if self.use_proxies else None
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            
            response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            names = set()
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    name = element.get_text().strip()
                    if name and len(name) > 2:  # Basic validation
                        names.add(name)
            
            return names
            
        except Exception as e:
            logger.error(f"Error extracting from static page {url}: {e}")
            return set()

    def extract_from_dynamic_page(self, url: str, config: dict) -> Set[str]:
        """Extract business names from a dynamic page using Selenium"""
        driver = None
        try:
            driver = self.setup_driver()
            driver.get(url)
            
            # Handle pagination or infinite scroll
            if config.get('pagination'):
                return self._handle_pagination(driver, config)
            elif config.get('infinite_scroll'):
                return self._handle_infinite_scroll(driver, config)
            else:
                return self._extract_names_from_current_page(driver, config)
                
        except Exception as e:
            logger.error(f"Error extracting from dynamic page {url}: {e}")
            return set()
        finally:
            if driver:
                driver.quit()

    def _handle_pagination(self, driver, config) -> Set[str]:
        """Handle paginated content"""
        all_names = set()
        max_pages = config.get('max_pages', 10)
        next_selector = config.get('next_selector')
        
        for page in range(max_pages):
            try:
                # Extract names from current page
                page_names = self._extract_names_from_current_page(driver, config)
                all_names.update(page_names)
                
                # Try to go to next page
                if page < max_pages - 1:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, next_selector))
                    )
                    next_button.click()
                    time.sleep(2)  # Wait for page load
                    
            except Exception as e:
                logger.warning(f"Stopped pagination at page {page + 1}: {e}")
                break
                
        return all_names

    def _handle_infinite_scroll(self, driver, config) -> Set[str]:
        """Handle infinite scroll content"""
        all_names = set()
        scroll_pauses = config.get('scroll_pauses', 5)
        scroll_height = config.get('scroll_height', 1000)
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(scroll_pauses):
            # Scroll down
            driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(2)
            
            # Extract names
            page_names = self._extract_names_from_current_page(driver, config)
            all_names.update(page_names)
            
            # Check if we've reached the bottom
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        return all_names

    def _extract_names_from_current_page(self, driver, config) -> Set[str]:
        """Extract business names from the current page"""
        names = set()
        selectors = config.get('selectors', [])
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    name = element.text.strip()
                    if name and len(name) > 2:
                        names.add(name)
            except Exception as e:
                logger.warning(f"Failed to extract with selector {selector}: {e}")
                
        return names

    def extract_businesses(self, target_url: str, page_type: str = 'auto', config: dict = None) -> List[str]:
        """
        Main method to extract business names from a target URL
        """
        if config is None:
            config = {}
            
        logger.info(f"Extracting businesses from: {target_url}")
        
        if page_type == 'auto':
            # Try to detect page type (simple heuristic)
            try:
                response = requests.head(target_url, timeout=10)
                page_type = 'static' if 'text/html' in response.headers.get('content-type', '') else 'dynamic'
            except:
                page_type = 'dynamic'
        
        if page_type == 'static':
            selectors = config.get('selectors', ['.business-name', '.company-name', 'h2', 'h3'])
            names = self.extract_from_static_page(target_url, selectors)
        else:
            names = self.extract_from_dynamic_page(target_url, config)
        
        # Deduplicate and clean
        cleaned_names = self._clean_business_names(names)
        logger.info(f"Extracted {len(cleaned_names)} unique business names")
        
        return list(cleaned_names)

    def _clean_business_names(self, names: Set[str]) -> Set[str]:
        """Clean and normalize business names"""
        cleaned = set()
        for name in names:
            # Remove extra whitespace
            name = ' '.join(name.split())
            # Remove common prefixes/suffixes that might be part of UI
            if any(indicator in name.lower() for indicator in ['page', 'copyright', '©', 'all rights reserved']):
                continue
            if len(name) > 2:  # Minimum length
                cleaned.add(name)
        return cleaned

# Example usage
if __name__ == "__main__":
    extractor = BusinessExtractor(use_proxies=False, headless=True)
    
    # Example configuration for a specific site
    config = {
        'selectors': ['.business-name', '.company-title'],
        'pagination': True,
        'next_selector': '.next-page',
        'max_pages': 5
    }
    
    businesses = extractor.extract_businesses(
        "https://www.yellowpages.com/",
        page_type="dynamic",
        config=config
    )
    
    print(f"Found {len(businesses)} businesses:")
    for business in sorted(businesses):
        print(f" - {business}")