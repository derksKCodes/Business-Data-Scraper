import requests
from googlesearch import search as google_search
from urllib.parse import urlparse
import time
import logging
import re
from typing import List, Dict, Optional
from utils.proxy_manager import ProxyManager
from fake_useragent import UserAgent
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleSearchAPI:
    def __init__(self, use_proxies=False, api_key=None, search_engine_id=None):
        self.use_proxies = use_proxies
        self.proxy_manager = ProxyManager() if use_proxies else None
        self.ua = UserAgent()
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.directory_domains = [
            'yelp.com', 'yellowpages.com', 'tripadvisor.com', 'facebook.com',
            'linkedin.com', 'twitter.com', 'instagram.com', 'pinterest.com',
            'angieslist.com', 'homeadvisor.com', 'thumbtack.com', 'bbb.org',
            'glassdoor.com', 'indeed.com', 'crunchbase.com', 'zoominfo.com',
            'manta.com', 'foursquare.com', 'tripadvisor.com', 'citysearch.com'
        ]
        
    def search_business_url(self, business_name: str, location: str = "", num_results: int = 5) -> Optional[str]:
        """
        Search for a business's official website using Google Search
        Returns the first non-directory URL found
        """
        try:
            query = self._build_query(business_name, location)
            logger.info(f"Searching for: {query}")
            
            if self.api_key and self.search_engine_id:
                results = self._search_with_api(query, num_results)
            else:
                results = self._search_with_library(query, num_results)
            
            # Filter out directory sites and find official website
            official_url = self._filter_results(results, business_name)
            
            if official_url:
                logger.info(f"Found official URL for {business_name}: {official_url}")
            else:
                logger.warning(f"No official URL found for {business_name}")
                
            return official_url
            
        except Exception as e:
            logger.error(f"Error searching for {business_name}: {e}")
            return None

    def _build_query(self, business_name: str, location: str) -> str:
        """Build Google search query"""
        query = f'"{business_name}"'
        if location:
            query += f' "{location}"'
        query += ' official website'
        return query

    def _search_with_api(self, query: str, num_results: int) -> List[str]:
        """Search using Google Custom Search JSON API"""
        try:
            from googleapiclient.discovery import build
            
            service = build("customsearch", "v1", developerKey=self.api_key)
            result = service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=min(num_results, 10)  # API limit
            ).execute()
            
            return [item['link'] for item in result.get('items', [])]
            
        except ImportError:
            logger.error("google-api-python-client not installed. Falling back to web scraping.")
            return self._search_with_library(query, num_results)
        except Exception as e:
            logger.error(f"Google API error: {e}")
            return []

    # def _search_with_library(self, query: str, num_results: int) -> List[str]:
    #     """Search using googlesearch-python library with retries and delays"""
    #     results = []
    #     try:
    #         # Add random delay to avoid blocking
    #         time.sleep(random.uniform(1, 3))
            
    #         for url in google_search(
    #             query, 
    #             num=num_results, 
    #             stop=num_results,
    #             pause=random.uniform(2, 5),  # Random pause between requests
    #             user_agent=self.ua.random
    #         ):
    #             results.append(url)
                
    #     except Exception as e:
    #         logger.error(f"Google search error: {e}")
            
    #     return results
    # Update the _search_with_library method in google_search.py
    def _search_with_library(self, query: str, num_results: int) -> List[str]:
        """Search using googlesearch-python library with retries and delays"""
        results = []
        try:
            # Add random delay to avoid blocking
            time.sleep(random.uniform(1, 3))

            # googlesearch-python signature: search(query, num_results=10, advanced=False, sleep_interval=0)
            for url in google_search(
                query,
                num_results=num_results,
                advanced=False,
                sleep_interval=random.uniform(2, 5)
            ):
                results.append(url)

        except Exception as e:
            logger.error(f"Google search error: {e}")

        return results


    def _filter_results(self, results: List[str], business_name: str) -> Optional[str]:
        """Filter search results to find the official website"""
        if not results:
            return None
            
        # Convert business name to lowercase for matching
        business_lower = business_name.lower()
        
        for url in results:
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc.lower()
                
                # Skip directory sites
                if any(dir_domain in domain for dir_domain in self.directory_domains):
                    continue
                    
                # Skip ads and tracking URLs
                if any(term in url.lower() for term in ['/ad/', '/track/', '/redirect']):
                    continue
                    
                # Prefer URLs that contain the business name
                if business_lower in domain or business_lower in url.lower():
                    return url
                    
            except Exception as e:
                logger.warning(f"Error parsing URL {url}: {e}")
                continue
                
        # If no perfect match, return the first non-directory result
        for url in results:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            if not any(dir_domain in domain for dir_domain in self.directory_domains):
                return url
                
        return None

    def batch_search_urls(self, business_names: List[str], location: str = "", 
                         delay: float = 2.0, max_workers: int = 3) -> Dict[str, str]:
        """
        Search URLs for multiple businesses with rate limiting
        Returns a dictionary mapping business names to URLs
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        results = {}
        failed_searches = []
        
        def search_single(business):
            try:
                url = self.search_business_url(business, location)
                time.sleep(delay)  # Rate limiting
                return business, url
            except Exception as e:
                logger.error(f"Failed to search for {business}: {e}")
                return business, None
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_business = {
                executor.submit(search_single, business): business 
                for business in business_names
            }
            
            for future in as_completed(future_to_business):
                business = future_to_business[future]
                try:
                    business, url = future.result()
                    results[business] = url
                    if not url:
                        failed_searches.append(business)
                except Exception as e:
                    logger.error(f"Error processing {business}: {e}")
                    failed_searches.append(business)
        
        logger.info(f"Completed URL searches. Found {len(results) - len(failed_searches)} URLs, {len(failed_searches)} failed.")
        return results

# Example usage
if __name__ == "__main__":
    # For API usage, set these environment variables:
    # GOOGLE_API_KEY=your_api_key
    # GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
    
    import os
    api_key = os.getenv('GOOGLE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    searcher = GoogleSearchAPI(
        use_proxies=True,
        api_key=api_key,
        search_engine_id=search_engine_id
    )
    
    test_businesses = ["Starbucks", "Amazon", "Microsoft"]
    results = searcher.batch_search_urls(test_businesses, location="Seattle")
    
    for business, url in results.items():
        print(f"{business}: {url}")