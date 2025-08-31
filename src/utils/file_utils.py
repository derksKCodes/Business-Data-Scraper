import pandas as pd
import json
import csv
import os
from typing import List, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataExporter:
    def __init__(self, output_dir="data/outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_to_excel(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to Excel file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_contacts_{timestamp}.xlsx"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"Exported {len(data)} records to Excel: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            raise

    def export_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_contacts_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported {len(data)} records to CSV: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise

    def export_to_json(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Export data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"business_contacts_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(data)} records to JSON: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            raise

    def export_all_formats(self, data: List[Dict[str, Any]], base_filename: str = None) -> Dict[str, str]:
        """Export data to all supported formats"""
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"business_contacts_{timestamp}"
        
        results = {}
        
        try:
            results['excel'] = self.export_to_excel(data, f"{base_filename}.xlsx")
            results['csv'] = self.export_to_csv(data, f"{base_filename}.csv")
            results['json'] = self.export_to_json(data, f"{base_filename}.json")
            
            logger.info(f"Exported data to all formats: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to export all formats: {e}")
            # Try to export remaining formats if one fails
            if 'excel' not in results:
                try:
                    results['excel'] = self.export_to_excel(data, f"{base_filename}_backup.xlsx")
                except:
                    pass
            if 'csv' not in results:
                try:
                    results['csv'] = self.export_to_csv(data, f"{base_filename}_backup.csv")
                except:
                    pass
            if 'json' not in results:
                try:
                    results['json'] = self.export_to_json(data, f"{base_filename}_backup.json")
                except:
                    pass
                    
            return results

    def save_intermediate_data(self, data: Any, filename: str, subdir: str = "raw"):
        """Save intermediate data to file"""
        dir_path = os.path.join(self.output_dir, "..", subdir)
        os.makedirs(dir_path, exist_ok=True)
        
        filepath = os.path.join(dir_path, filename)
        
        try:
            if filename.endswith('.json'):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif filename.endswith('.csv'):
                if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                    df = pd.DataFrame(data)
                    df.to_csv(filepath, index=False, encoding='utf-8')
                else:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        if isinstance(data, list):
                            for item in data:
                                writer.writerow([item] if not isinstance(item, list) else item)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(data))
                    
            logger.info(f"Saved intermediate data to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save intermediate data: {e}")
            raise

    def load_intermediate_data(self, filename: str, subdir: str = "raw"):
        """Load intermediate data from file"""
        filepath = os.path.join(self.output_dir, "..", subdir, filename)
        
        try:
            if filename.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif filename.endswith('.csv'):
                return pd.read_csv(filepath).to_dict('records')
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Failed to load intermediate data: {e}")
            raise

# Example usage
if __name__ == "__main__":
    exporter = DataExporter()
    
    sample_data = [
        {
            "business_name": "Example Corp",
            "website_url": "https://example.com",
            "emails": ["contact@example.com", "info@example.com"],
            "phones": ["+1234567890"],
            "social_media": [{"platform": "twitter", "url": "https://twitter.com/example"}],
            "source_page": "https://example.com/contact"
        }
    ]
    
    # Export to all formats
    results = exporter.export_all_formats(sample_data)
    print(f"Exported files: {results}")