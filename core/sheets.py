import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GoogleSheetsUploader:
    def __init__(self):
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self.creds = Credentials.from_service_account_file("credentials.json", scopes=self.scopes)
        self.service = build("sheets", "v4", credentials=self.creds)

    def upload_dataframe(self, df: pd.DataFrame, sheet_name: str = "Scraped Products"):
        """Завантажує DataFrame до Google Sheets та стилізує його через офіційне Google Sheets API v4."""
        if df.empty:
            print("DataFrame is empty. Nothing to upload.")
            return

        # 1. Preparing the data
        header = [df.columns.tolist()]
        rows = df.values.tolist()
        values = header + rows
        body = {'values': values}
        
        range_name = f"{sheet_name}!A1"
        
        # 2. Cleaning up old data
        self.service.spreadsheets().values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=f"{sheet_name}!A1:Z1000"
        ).execute()

        # 3. Recording new data
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        
        print(f"{result.get('updatedCells')} cells successfully updated in Google Sheets!")


        try:
            # Get the sheetId of our sheet, because styling requires a numeric ID, not a string name.
            spreadsheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet_metadata.get('sheets', [])
            sheet_id = 0
            for s in sheets:
                if s.get('properties', {}).get('title') == sheet_name:
                    sheet_id = s.get('properties', {}).get('sheetId')
                    break

            end_row = len(values)

            requests = [
                # A. Freezing the first row (header)
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {"frozenRowCount": 1}
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                },
                # B. Styling the header (Navy blue background, bold white text, center alignment)
                {
                    "repeatCell": {
                        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 6},
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.1, "green": 0.22, "blue": 0.44},
                                "horizontalAlignment": "CENTER",
                                "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "fontSize": 10}
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)"
                    }
                },
                # C. Currency format for prices (Columns C and D -> indices 2 and 4)
                {
                    "repeatCell": {
                        "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": end_row, "startColumnIndex": 2, "endColumnIndex": 4},
                        "cell": {
                            "userEnteredFormat": {
                                "numberFormat": {"type": "CURRENCY", "pattern": "#,##0\" грн\""},
                                "horizontalAlignment": "RIGHT"
                            }
                        },
                        "fields": "userEnteredFormat(numberFormat,horizontalAlignment)"
                    }
                },
                # D. Center the Brand (1), Availability (4), and Discount % (5) columns.
                {
                    "repeatCell": {
                        "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": end_row, "startColumnIndex": 4, "endColumnIndex": 6},
                        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                        "fields": "userEnteredFormat.horizontalAlignment"
                    }
                },
                {
                    "repeatCell": {
                        "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": end_row, "startColumnIndex": 1, "endColumnIndex": 2},
                        "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                        "fields": "userEnteredFormat.horizontalAlignment"
                    }
                },
                # E. Conditional formatting: if the discount > 0 in column F (index 5), color the cell a soft green.
                {
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": end_row, "startColumnIndex": 5, "endColumnIndex": 6}],
                            "booleanRule": {
                                "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                                "format": {
                                    "backgroundColor": {"red": 0.85, "green": 0.93, "blue": 0.85},
                                    "textFormat": {"bold": True, "foregroundColor": {"red": 0.0, "green": 0.4, "blue": 0.0}}
                                }
                            }
                        },
                        "index": 0
                    }
                }
            ]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            print("Google Sheet dashboard successfully styled and polished! 🎨")

        except Exception as e:
            print(f"Styling failed, but data was uploaded. Error: {e}")