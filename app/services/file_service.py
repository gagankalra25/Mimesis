import os
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from config import RESPONSES_DIR, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.responses_dir = RESPONSES_DIR
        if not os.path.exists(self.responses_dir):
            os.makedirs(self.responses_dir)
    
    def generate_filename(self, domain: str, data_format: str) -> str:
        """Generate timestamp-based filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{data_format}_{timestamp}.csv"
        return os.path.join(self.responses_dir, filename)
    
    def save_to_csv(self, data: List[Dict[str, Any]], domain: str, data_format: str) -> str:
        """Save data to CSV file"""
        try:
            if not data:
                raise ValueError("No data to save")
            
            filepath = self.generate_filename(domain, data_format)
            
            # Get expected fields for the format
            format_config = SUPPORTED_FORMATS.get(data_format, {})
            expected_fields = format_config.get("fields", list(data[0].keys()) if data else [])
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(data)
            
            # Ensure all expected fields exist
            for field in expected_fields:
                if field not in df.columns:
                    df[field] = ""
            
            # Reorder columns to match expected format
            df = df.reindex(columns=expected_fields)
            
            # Handle metadata field for rag_chunks (convert dict to JSON string)
            if data_format == "rag_chunks" and "metadata" in df.columns:
                df["metadata"] = df["metadata"].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else str(x)
                )
            
            # Save to CSV
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"Saved {len(data)} records to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save data to CSV: {str(e)}")
            raise
    
    def validate_data_format(self, data: List[Dict[str, Any]], data_format: str) -> bool:
        """Validate data matches expected format"""
        try:
            if not data:
                return False
            
            format_config = SUPPORTED_FORMATS.get(data_format, {})
            expected_fields = set(format_config.get("fields", []))
            
            for record in data:
                record_fields = set(record.keys())
                if not expected_fields.issubset(record_fields):
                    missing_fields = expected_fields - record_fields
                    logger.warning(f"Record missing fields: {missing_fields}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Data validation failed: {str(e)}")
            return False
    
    def get_file_stats(self, filepath: str) -> Dict[str, Any]:
        """Get statistics about the saved file"""
        try:
            if not os.path.exists(filepath):
                return {"exists": False}
            
            # Get file size
            file_size = os.path.getsize(filepath)
            
            # Count rows in CSV
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                row_count = sum(1 for row in reader) - 1  # Subtract header row
            
            return {
                "exists": True,
                "file_size_bytes": file_size,
                "record_count": row_count,
                "created_at": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get file stats: {str(e)}")
            return {"exists": False, "error": str(e)}
    
    def cleanup_old_files(self, days_old: int = 7) -> int:
        """Clean up files older than specified days"""
        try:
            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for filename in os.listdir(self.responses_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.responses_dir, filename)
                    if os.path.getctime(filepath) < cutoff_time:
                        os.remove(filepath)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old file: {filename}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return 0
    
    def read_csv_sample(self, filepath: str, num_rows: int = 5) -> List[Dict[str, Any]]:
        """Read a sample of rows from CSV file"""
        try:
            df = pd.read_csv(filepath, nrows=num_rows)
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Failed to read CSV sample: {str(e)}")
            return []