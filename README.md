 Business Scraper Project

A comprehensive Python-based solution for extracting business information and contact details for lead generation and market research.

## Features

- **Business Name Extraction**: Scrape business names from target websites (static or dynamic)
- **URL Discovery**: Find official business websites using Google Search
- **Contact Information Extraction**: Extract emails, phone numbers, and social media links
- **Multiple Output Formats**: Export results to Excel, CSV, and JSON
- **Error Handling & Logging**: Comprehensive error handling with detailed logging
- **Proxy Support**: Rotate proxies and user agents to avoid blocking

## Project Structure
Business-Scraper-Project/
│── data/
│ ├── raw/ # Raw scraped data (intermediate)
│ ├── processed/ # Cleaned & deduplicated data
│ ├── outputs/ # Final exports: CSV, Excel, JSON
│
│── src/
│ ├── extract_businesses.py # Scrape business names from target site
│ ├── google_search.py # Find official URLs via Google API
│ ├── contact_scraper.py # Extract emails, phones, social links
│ ├── utils/
│ │ ├── regex_patterns.py # Regex rules for emails/phones
│ │ ├── file_utils.py # Save to CSV, Excel, JSON
│ │ ├── proxy_manager.py # Handle proxies, rotation
│ └── pipeline.py # Main workflow orchestration
│
│── n8n_workflow/
│ ├── business_scraper.json # n8n export of workflow
│
│── logs/
│ ├── scraper.log # Log errors, retries, progress
│
│── requirements.txt # Python dependencies
│── README.md # Project documentation

text

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Business-Scraper-Project
Install dependencies:

bash
pip install -r requirements.txt
Set up environment variables (optional):

bash
# For Google Custom Search API
export GOOGLE_API_KEY=your_api_key
export GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# For proxies
export SCRAPER_PROXY=http://proxy:port
export SCRAPER_PROXY_LIST=proxy1,proxy2,proxy3
Usage
Basic Usage
python
from src.pipeline import BusinessScraperPipeline, DEFAULT_CONFIG

# Configure the pipeline
config = {**DEFAULT_CONFIG, 'use_proxies': True}

# Initialize pipeline
pipeline = BusinessScraperPipeline(config)

# Run the pipeline
results = pipeline.run_pipeline(
    "https://example-business-directory.com",
    extraction_config={
        'selectors': ['.business-name', '.company-title'],
        'pagination': True,
        'next_selector': '.next-page',
        'max_pages': 5
    }
)
Individual Components
Extract Business Names
python
from src.extract_businesses import BusinessExtractor

extractor = BusinessExtractor(use_proxies=False)
businesses = extractor.extract_businesses(
    "https://example.com",
    page_type="dynamic",
    config={'selectors': ['.business-name']}
)
Find Website URLs
python
from src.google_search import GoogleSearchAPI

searcher = GoogleSearchAPI()
urls = searcher.batch_search_urls(
    ["Business 1", "Business 2"],
    location="New York"
)
Scrape Contact Information
python
from src.contact_scraper import ContactScraper

scraper = ContactScraper()
contacts = scraper.batch_scrape_contacts({
    "Business 1": "https://business1.com",
    "Business 2": "https://business2.com"
})
Configuration
Google Search API
To use Google Custom Search API:

Create a project in Google Cloud Console

Enable Custom Search API

Create a Custom Search Engine

Set API key and search engine ID as environment variables

Proxies
Configure proxies via:

Environment variables: SCRAPER_PROXY, SCRAPER_PROXY_LIST, SCRAPER_PROXY_FILE

Programmatically: Pass proxy list to ProxyManager

Output Formats
The pipeline exports data in three formats:

Excel (.xlsx): Structured data with multiple sheets

CSV (.csv): Comma-separated values

JSON (.json): Structured JSON data

Error Handling
The system includes comprehensive error handling:

Retry mechanisms for failed requests

Detailed logging of errors and progress

Skip and continue functionality for large batches

Intermediate data saving for recovery

Legal Considerations
Respect robots.txt files

Add delays between requests to avoid overwhelming servers

Use proxies and rotate user agents to avoid IP blocking

Comply with terms of service of target websites

Use data ethically and in compliance with privacy regulations

Support
For issues and questions:

Check the logs in logs/ directory

Review the intermediate data in data/raw/

Ensure all dependencies are installed correctly

text

## Next Steps

This implementation provides a complete business scraper project with all the required components. To further enhance the project:

1. **Add n8n Workflow**: Create the n8n workflow JSON file to integrate with the n8n automation platform
2. **Database Integration**: Add support for storing results in databases like PostgreSQL or MongoDB
3. **Advanced Rate Limiting**: Implement more sophisticated rate limiting and request throttling
4. **CAPTCHA Handling**: Add CAPTCHA solving capabilities for difficult sites
5. **Machine Learning**: Implement ML models for better contact information extraction
6. **Web Interface**: Create a web-based dashboard for managing scraping jobs

The project is designed to be modular and extensible, allowing you to easily add new features or modify existing functionality based on your specific requirements.