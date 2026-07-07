import pandas as pd
import numpy as np

class DataCleaner:
    def clean_scraped_data(self, raw_data: list) -> pd.DataFrame:
        """Очищає ціни, вираховує знижки та сортує дані."""
        if not raw_data:
            return pd.DataFrame()

        df = pd.DataFrame(raw_data)

        df['Price'] = df['Price'].apply(lambda x: float(''.join(c for c in str(x) if c.isdigit())) if x else 0.0)

        def clean_old_price(val):
            if not val:
                return ""
            cleaned = ''.join(c for c in str(val) if c.isdigit())
            return float(cleaned) if cleaned and int(cleaned) > 0 else ""

        df['Old Price'] = df['Old Price'].apply(clean_old_price)

        df['Discount %'] = 0
        for idx, row in df.iterrows():
            if isinstance(row['Old Price'], (int, float)) and row['Old Price'] > row['Price']:
                discount = round(((row['Old Price'] - row['Price']) / row['Old Price']) * 100)
                df.at[idx, 'Discount %'] = int(discount)

        df['Title'] = df['Title'].str.strip()
        df['Brand'] = df['Brand'].str.upper().str.strip()

        df = df.sort_values(by='Discount %', ascending=False).reset_index(drop=True)

        return df