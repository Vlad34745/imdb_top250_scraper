from email import parser
import logging
# Зверни увагу на імпорт оновленого класу BookYeParser
from core.parser import TelemartParser
from core.cleaner import DataCleaner
from core.sheets import GoogleSheetsUploader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def main():
    logging.info("--- Starting E-Commerce Scraper Pipeline ---")
    
    parser = TelemartParser()
    cleaner = DataCleaner()
    uploader = GoogleSheetsUploader()
    
    raw_data = parser.scrape_all()
    
    if not raw_data:
        logging.error("No data scraped. Exiting pipeline.")
        return
        
    logging.info(f"Successfully scraped {len(raw_data)} raw products.")
    
    logging.info("Running data cleaning and analysis via Pandas...")
    cleaned_df = cleaner.clean_scraped_data(raw_data)
    
    print("\n--- Cleaned Data Preview (Sorted by Price) ---")
    print(cleaned_df.head(10))
    print("----------------------------------------------\n")
    
    logging.info("Uploading polished data to Google Sheets...")
    uploader.upload_dataframe(cleaned_df, sheet_name="Scraped Products")
    
    logging.info("--- Pipeline Finished Successfully! ---")

if __name__ == "__main__":
    main()