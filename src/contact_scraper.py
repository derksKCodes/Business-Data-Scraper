import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from utils.proxy_manager import ProxyManager
from utils.regex_patterns import EMAIL_PATTERNS, PHONE_PATTERNS, SOCIAL_MEDIA_PATTERNS
from fake_useragent import UserAgent
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContactScraper:
    def __init__(self, use_proxies=False, timeout=30):
        self.use_proxies = use_proxies
        self.timeout = timeout
        self.proxy_manager = ProxyManager() if use_proxies else None
        self.ua = UserAgent()
        
    def scrape_website_contacts(self, url: str, business_name: str) -> Dict:
        """
        Scrape a website for contact information
        Returns a dictionary with emails, phones, and social media links
        """
        if not url:
            return {
                'emails': [],
                'phones': [],
                'social_media': [],
                'error': 'No URL provided'
            }
            
        try:
            # Fetch the webpage
            html_content = self._fetch_url(url)
            if not html_content:
                return {
                    'emails': [],
                    'phones': [],
                    'social_media': [],
                    'error': 'Failed to fetch URL'
                }
            
            # Extract contact information
            emails = self._extract_emails(html_content, url)
            phones = self._extract_phones(html_content)
            social_media = self._extract_social_media(html_content, url)
            
            # Try to find contact page if no contacts found on homepage
            if not emails and not phones:
                contact_page_url = self._find_contact_page(html_content, url)
                if contact_page_url and contact_page_url != url:
                    logger.info(f"Trying contact page: {contact_page_url}")
                    contact_html = self._fetch_url(contact_page_url)
                    if contact_html:
                        emails.extend(self._extract_emails(contact_html, contact_page_url))
                        phones.extend(self._extract_phones(contact_html))
            
            # Deduplicate results
            emails = list(set(emails))
            phones = list(set(phones))
            
            return {
                'emails': emails,
                'phones': phones,
                'social_media': social_media,
                'source_url': url
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                'emails': [],
                'phones': [],
                'social_media': [],
                'error': str(e)
            }

    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with proper headers and error handling"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            proxy = self.proxy_manager.get_proxy() if self.use_proxies else None
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxies, 
                timeout=self.timeout,
                verify=False  # Warning: only for development
            )
            response.raise_for_status()
            
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _extract_emails(self, html_content: str, base_url: str) -> List[str]:
        """Extract email addresses from HTML content"""
        emails = set()
        
        # Extract using regex patterns
        for pattern in EMAIL_PATTERNS:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Handle capture groups
                email = match.lower().strip()
                if self._is_valid_email(email):
                    emails.add(email)
        
        # Extract from mailto links
        soup = BeautifulSoup(html_content, 'html.parser')
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        
        for link in mailto_links:
            href = link.get('href', '')
            email = href.replace('mailto:', '').split('?')[0].strip()
            if self._is_valid_email(email):
                emails.add(email.lower())
        
        return list(emails)

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format and filter out common false positives"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False
            
        # Filter out common false positives
        false_positives = [
            'email@example.com', 'example@example.com', 
            'your@email.com', 'user@example.com'
        ]
        if email in false_positives:
            return False
            
        # Filter out email patterns that are likely examples
        if any(term in email for term in ['example', 'domain', 'test', 'noreply']):
            return False
            
        return True

    def _extract_phones(self, html_content: str) -> List[str]:
        """Extract phone numbers from HTML content"""
        phones = set()
        
        for pattern in PHONE_PATTERNS:
            matches = re.findall(pattern, html_content)
            for match in matches:
                if isinstance(match, tuple):
                    match = ''.join(match)  # Combine capture groups
                phone = self._normalize_phone(match)
                if phone:
                    phones.add(phone)
        
        # Extract from tel links
        soup = BeautifulSoup(html_content, 'html.parser')
        tel_links = soup.find_all('a', href=re.compile(r'^tel:', re.I))
        
        for link in tel_links:
            href = link.get('href', '')
            phone = href.replace('tel:', '').strip()
            normalized = self._normalize_phone(phone)
            if normalized:
                phones.add(normalized)
        
        return list(phones)

    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number format"""
        # Remove non-digit characters except plus
        digits = re.sub(r'[^\d+]', '', phone)
        
        # Validate length
        if len(digits) < 10:
            return None
            
        # Add country code if missing (assume US for now)
        if digits.startswith('+'):
            return digits
        elif len(digits) == 10:
            return f"+1{digits}"  # US default
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        else:
            return f"+{digits}"

    def _extract_social_media(self, html_content: str, base_url: str) -> List[Dict]:
        """Extract social media links from HTML content"""
        social_links = []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        social_links_elements = soup.find_all('a', href=True)
        
        for element in social_links_elements:
            href = element['href'].lower()
            text = element.get_text().lower()
            
            for platform, patterns in SOCIAL_MEDIA_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, href) or re.search(pattern, text):
                        full_url = urljoin(base_url, href)
                        social_links.append({
                            'platform': platform,
                            'url': full_url
                        })
                        break
        
        return social_links

    def _find_contact_page(self, html_content: str, base_url: str) -> Optional[str]:
        """Try to find a contact page URL"""
        soup = BeautifulSoup(html_content, 'html.parser')
        contact_indicators = [
            'contact', 'contact-us', 'contact.html', 'contact.php',
            'about', 'about-us', 'connect', 'get-in-touch'
        ]
        
        # Look for links that might lead to contact pages
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            if any(indicator in href or indicator in text for indicator in contact_indicators):
                full_url = urljoin(base_url, href)
                return full_url
        
        return None

    def batch_scrape_contacts(self, business_urls: Dict[str, str], 
                            delay: float = 1.0, max_workers: int = 5) -> Dict[str, Dict]:
        """
        Scrape contacts for multiple businesses with rate limiting
        Returns a dictionary mapping business names to contact info
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        results = {}
        
        def scrape_single(business, url):
            try:
                contacts = self.scrape_website_contacts(url, business)
                time.sleep(delay)  # Rate limiting
                return business, contacts
            except Exception as e:
                logger.error(f"Failed to scrape {business}: {e}")
                return business, {'error': str(e)}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_business = {
                executor.submit(scrape_single, business, url): business 
                for business, url in business_urls.items() if url
            }
            
            for future in as_completed(future_to_business):
                business = future_to_business[future]
                try:
                    business, contacts = future.result()
                    results[business] = contacts
                except Exception as e:
                    logger.error(f"Error processing {business}: {e}")
                    results[business] = {'error': str(e)}
        
        return results

# Example usage
if __name__ == "__main__":
    scraper = ContactScraper(use_proxies=True)
    
    test_urls = {
        "Example Business": "https://www.google.com/maps/search/restaurants+in+seattle"
    }
    
    results = scraper.batch_scrape_contacts(test_urls)
    
    for business, contacts in results.items():
        print(f"\n{business}:")
        print(f"  Emails: {contacts.get('emails', [])}")
        print(f"  Phones: {contacts.get('phones', [])}")
        print(f"  Social: {contacts.get('social_media', [])}")