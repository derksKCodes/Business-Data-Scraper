import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from extract_businesses import BusinessExtractor
from google_search import GoogleSearchAPI
from contact_scraper import ContactScraper
from utils.file_utils import DataExporter
from utils.proxy_manager import ProxyManager
import json
import os

# Add import at the top
from utils.input_handler import InputHandler

        
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BusinessScraperPipeline:
    def __init__(self, config: Dict[str, Any] = None):
        self.input_handler = InputHandler()
        
        self.config = config or {}
        self.use_proxies = self.config.get('use_proxies', False)
        self.proxy_manager = ProxyManager() if self.use_proxies else None
        
        # Initialize components
        self.business_extractor = BusinessExtractor(
            use_proxies=self.use_proxies,
            headless=self.config.get('headless', True)
        )
        
        self.google_searcher = GoogleSearchAPI(
            use_proxies=self.use_proxies,
            api_key=self.config.get('google_api_key'),
            search_engine_id=self.config.get('google_search_engine_id')
        )
        
        self.contact_scraper = ContactScraper(
            use_proxies=self.use_proxies,
            timeout=self.config.get('timeout', 30)
        )
        
        self.data_exporter = DataExporter()
        
        # Results storage
        self.business_names = []
        self.business_urls = {}
        self.contact_info = {}
        self.failed_businesses = []

    def run_pipeline(self, target_url: str, extraction_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the complete scraping pipeline"""
        start_time = time.time()
        results = {}
        
        try:
            # Step 1: Extract business names
            logger.info("Step 1: Extracting business names")
            self.business_names = self.business_extractor.extract_businesses(
                target_url, 
                config=extraction_config
            )
            
            if not self.business_names:
                logger.error("No business names extracted")
                return results
                
            logger.info(f"Extracted {len(self.business_names)} business names")
            self.data_exporter.save_intermediate_data(
                self.business_names, 
                "extracted_businesses.json"
            )
            
            # Step 2: Find website URLs
            logger.info("Step 2: Finding website URLs")
            location = self.config.get('location', '')
            self.business_urls = self.google_searcher.batch_search_urls(
                self.business_names, 
                location=location,
                delay=self.config.get('search_delay', 2.0),
                max_workers=self.config.get('search_workers', 3)
            )
            
            self.data_exporter.save_intermediate_data(
                self.business_urls, 
                "business_urls.json"
            )
            
            # Step 3: Scrape contact information
            logger.info("Step 3: Scraping contact information")
            self.contact_info = self.contact_scraper.batch_scrape_contacts(
                self.business_urls,
                delay=self.config.get('scrape_delay', 1.0),
                max_workers=self.config.get('scrape_workers', 5)
            )
            
            self.data_exporter.save_intermediate_data(
                self.contact_info, 
                "contact_info.json"
            )
            
            # Step 4: Prepare final data
            logger.info("Step 4: Preparing final data")
            final_data = self._prepare_final_data()
            
            # Step 5: Export results
            logger.info("Step 5: Exporting results")
            export_results = self.data_exporter.export_all_formats(final_data)
            results['export_files'] = export_results
            
            # Step 6: Generate report
            logger.info("Step 6: Generating report")
            report = self._generate_report()
            results['report'] = report
            
            # Save report
            self.data_exporter.save_intermediate_data(
                report, 
                "scraping_report.json", 
                subdir="processed"
            )
            
            total_time = time.time() - start_time
            logger.info(f"Pipeline completed in {total_time:.2f} seconds")
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            # Try to save partial results
            try:
                if self.business_names:
                    self.data_exporter.save_intermediate_data(
                        self.business_names, 
                        "partial_businesses.json"
                    )
                if self.business_urls:
                    self.data_exporter.save_intermediate_data(
                        self.business_urls, 
                        "partial_urls.json"
                    )
                if self.contact_info:
                    self.data_exporter.save_intermediate_data(
                        self.contact_info, 
                        "partial_contacts.json"
                    )
            except Exception as save_error:
                logger.error(f"Failed to save partial results: {save_error}")
                
            raise

    def _prepare_final_data(self) -> List[Dict[str, Any]]:
        """Prepare final structured data for export"""
        final_data = []
        
        for business_name, url in self.business_urls.items():
            contacts = self.contact_info.get(business_name, {})
            
            record = {
                'business_name': business_name,
                'website_url': url,
                'emails': contacts.get('emails', []),
                'phones': contacts.get('phones', []),
                'social_media': contacts.get('social_media', []),
                'source_page': contacts.get('source_url', ''),
                'scrape_timestamp': datetime.now().isoformat(),
                'errors': contacts.get('error', '')
            }
            
            # Track failed businesses
            if not url or (not contacts.get('emails') and not contacts.get('phones')):
                self.failed_businesses.append(business_name)
                
            final_data.append(record)
            
        return final_data

    def _generate_report(self) -> Dict[str, Any]:
        """Generate a summary report of the scraping process"""
        total_businesses = len(self.business_names)
        businesses_with_urls = sum(1 for url in self.business_urls.values() if url)
        businesses_with_contacts = sum(1 for contacts in self.contact_info.values() 
                                     if contacts.get('emails') or contacts.get('phones'))
        
        total_emails = sum(len(contacts.get('emails', [])) for contacts in self.contact_info.values())
        total_phones = sum(len(contacts.get('phones', [])) for contacts in self.contact_info.values())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_businesses': total_businesses,
            'businesses_with_urls': businesses_with_urls,
            'businesses_with_contacts': businesses_with_contacts,
            'success_rate': f"{(businesses_with_contacts / total_businesses * 100):.1f}%" if total_businesses else "0%",
            'total_emails_collected': total_emails,
            'total_phones_collected': total_phones,
            'failed_businesses': self.failed_businesses,
            'failed_count': len(self.failed_businesses)
        }

    def load_and_continue(self, checkpoint: str):
        """Load from a checkpoint and continue processing"""
        # Implementation for resuming from checkpoint
        pass
    
        
    def run_from_urls_file(self, input_file: str, extraction_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run pipeline starting from a file containing URLs
        """
        try:
            # Read URLs from file
            url_records = self.input_handler.read_urls_from_file(input_file)
            
            # Extract business names from each URL
            all_businesses = []
            for record in url_records:
                logger.info(f"Extracting businesses from: {record['url']}")
                businesses = self.business_extractor.extract_businesses(
                    record['url'], 
                    config=extraction_config
                )
                
                # Add location context if available
                for business in businesses:
                    all_businesses.append({
                        'business_name': business,
                        'location': record.get('location', '')
                    })
            
            # Continue with the normal pipeline
            return self._process_business_list(all_businesses)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
    
    def run_from_business_names_file(self, input_file: str) -> Dict[str, Any]:
        """
        Run pipeline starting from a file containing business names
        """
        try:
            # Read business names from file
            business_records = self.input_handler.read_business_names_from_file(input_file)
            
            # Continue with the normal pipeline
            return self._process_business_list(business_records)
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise
    
    def _process_business_list(self, business_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a list of business records through the pipeline
        """
        results = {}
        start_time = time.time()
        
        # Extract business names and locations
        business_names = [record['business_name'] for record in business_records]
        locations = [record.get('location', '') for record in business_records]
        
        # Step 2: Find website URLs
        logger.info("Step 2: Finding website URLs")
        self.business_urls = {}
        
        for i, business_name in enumerate(business_names):
            location = locations[i] if i < len(locations) else ""
            url = self.google_searcher.search_business_url(business_name, location)
            self.business_urls[business_name] = url
            time.sleep(self.config.get('search_delay', 2.0))
        
        self.data_exporter.save_intermediate_data(
            self.business_urls, 
            "business_urls.json"
        )
        
        # Continue with the rest of the pipeline (Steps 3-6)
        # ... existing code from run_pipeline method ...
        
        total_time = time.time() - start_time
        logger.info(f"Pipeline completed in {total_time:.2f} seconds")
        
        return results

# Example configuration
DEFAULT_CONFIG = {
    'use_proxies': False,
    'headless': True,
    'timeout': 30,
    'search_delay': 2.0,
    'search_workers': 3,
    'scrape_delay': 1.0,
    'scrape_workers': 5,
    'location': '',
    'google_api_key': os.getenv('GOOGLE_API_KEY'),
    'google_search_engine_id': os.getenv('GOOGLE_SEARCH_ENGINE_ID')
}

# Example usage
# Replace the example usage section at the bottom
if __name__ == "__main__":
    # Example configuration
    DEFAULT_CONFIG = {
        'use_proxies': False,
        'headless': True,
        'timeout': 30,
        'search_delay': 2.0,
        'search_workers': 1,  # Reduced for sequential processing
        'scrape_delay': 1.0,
        'scrape_workers': 5,
        'location': '',
        'google_api_key': os.getenv('GOOGLE_API_KEY'),
        'google_search_engine_id': os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    }
    
    pipeline = BusinessScraperPipeline(DEFAULT_CONFIG)
    
    # Example usage with file input
    try:
        # Option 1: Process from URLs file
        results = pipeline.run_from_urls_file("data/input/urls.csv")
        
        # Option 2: Process from business names file
        results = pipeline.run_from_business_names_file("data/input/businesses.csv")
        
        print("Pipeline completed successfully!")
        print(f"Exported files: {results.get('export_files', {})}")
        print(f"Report: {json.dumps(results.get('report', {}), indent=2)}")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")