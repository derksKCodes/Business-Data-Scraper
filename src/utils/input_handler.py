import pandas as pd
import logging
from typing import List, Dict, Any
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InputHandler:
    def __init__(self):
        pass
    
    def read_urls_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read URLs from CSV or Excel file
        Expected columns: url, business_name (optional), location (optional)
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use CSV or Excel files.")
            
            # Convert to list of dictionaries
            records = df.to_dict('records')
            
            # Ensure required fields
            processed_records = []
            for record in records:
                if 'url' not in record:
                    logger.warning(f"Record missing 'url' field: {record}")
                    continue
                
                processed_records.append({
                    'url': record['url'],
                    'business_name': record.get('business_name', ''),
                    'location': record.get('location', '')
                })
            
            logger.info(f"Loaded {len(processed_records)} URLs from {file_path}")
            return processed_records
            
        except Exception as e:
            logger.error(f"Failed to read input file: {e}")
            raise
    
    def read_business_names_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read business names from CSV or Excel file
        Expected columns: business_name, location (optional)
        """
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use CSV or Excel files.")
            
            # Convert to list of dictionaries
            records = df.to_dict('records')
            
            # Ensure required fields
            processed_records = []
            for record in records:
                if 'business_name' not in record:
                    logger.warning(f"Record missing 'business_name' field: {record}")
                    continue
                
                processed_records.append({
                    'business_name': record['business_name'],
                    'location': record.get('location', '')
                })
            
            logger.info(f"Loaded {len(processed_records)} business names from {file_path}")
            return processed_records
            
        except Exception as e:
            logger.error(f"Failed to read input file: {e}")
            raise