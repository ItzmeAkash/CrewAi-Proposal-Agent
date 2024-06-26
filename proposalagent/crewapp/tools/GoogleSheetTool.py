import os
from crewai_tools import BaseTool
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import List, Dict, Union

# Define the base path to the credentials file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'googlesheetcredentials.json')

class GoogleSheetTool(BaseTool):
    name: str = "GoogleSheetTool"
    description: str = "Tool to store data into a Google Sheet using gspread and Google service account credentials"

    def _run(self, data: Union[List[Dict[str, str]], Dict[str, List[Dict[str, str]]]]) -> str:
    
        try:
            # Define the required scope
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]

            # Authenticate and create the client
            creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
            client = gspread.authorize(creds)

            # Define the Google Sheet ID
            sheet_id = "1_k2DzIMttt7PvXg-V40_soNH6dA2-E8dG06T2uIhFgA"

            # Open the Google Sheet
            workbook = client.open_by_key(sheet_id)

            # Process data based on its structure
            if isinstance(data, list):
                new_values = self._process_list_of_dicts(data)
            elif isinstance(data, dict) and 'data' in data:
                new_values = [data['data']]
            else:
                return "Invalid data format."

            # Get the current date for the worksheet name
            worksheet_name = datetime.now().strftime("%Y-%m-%d")

            # Get the list of worksheet titles
            worksheet_list = [sheet.title for sheet in workbook.worksheets()]

            # Check if the worksheet exists, otherwise create it
            if worksheet_name in worksheet_list:
                sheet = workbook.worksheet(worksheet_name)
            else:
                sheet = workbook.add_worksheet(title=worksheet_name, rows=10, cols=11)

            # Read the existing data
            existing_data = sheet.get_all_values()

            # Update the header row
            headers = ["Opportunity number", "Opportunity name", "Opportunity description", "Location", "Budget", "Deadline", "Supplier match", "Supplier’s matching product", "Local partner requirements", "Requirement details", "Related documents path"]
            sheet.update('A1:K1', [headers])
            
            # Create a dictionary of existing items based on the 'Opportunity number' column
            existing_items = {row[0]: row for row in existing_data[1:]}
            
            # Track the next available row for new data
            next_row_index = len(existing_data) + 1  # Adding 1 for zero-based index adjustment

            # Check if new rows need to be added
            required_rows = next_row_index + len(new_values) - 1  # Existing rows + new rows - header
            current_max_rows = sheet.row_count

            if required_rows > current_max_rows:
                sheet.add_rows(required_rows - current_max_rows)

            # Update or append the new values
            for new_row in new_values:
                opportunity_number = new_row["Opportunity number"]
                if opportunity_number in existing_items:
                    # Update the existing row
                    existing_row_index = existing_data.index(existing_items[opportunity_number]) + 1
                    sheet.update(f"A{existing_row_index}:K{existing_row_index}", [list(new_row.values())])
                else:
                    # Append the new row
                    sheet.append_row(list(new_row.values()))
                    next_row_index += 1

            # Format the header row to be bold
            sheet.format("A1:K1", {"textFormat": {"bold": True}})

            return "Google Sheet updated successfully."
        
        except Exception as e:
            return f"An error occurred: {e}"

    def _process_list_of_dicts(self, data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Process a list of dictionaries, each dictionary containing a single key-value pair or all fields.
        """
        processed_data = []
        if all(len(d) == 1 for d in data):
            # Convert list of single key-value pairs to a single dictionary
            combined_data = {}
            for d in data:
                combined_data.update(d)
            processed_data.append(combined_data)
        else:
            # Assume data is already in the correct format
            processed_data = data
        return processed_data

# Example usage of the tool with corrected data structure
# data = {
#         "data": {
#             "Opportunity number": "PDS-004-FY2024",
#             "Opportunity name": "U.S. Embassy Ethiopia PD Request for Statement of Interest",
#             "Opportunity description": "This funding opportunity is intended for organizations or individuals to submit a statement of interest to carry out a public engagement program. The program focuses on strengthening cultural ties between the United States and Ethiopia through various programs that promote bilateral cooperation and shared values.",
#             "Location": "Ethiopia",
#             "Budget": "Total amount available is approximately $200,000, pending funding availability. Awards may range from a minimum of $25,000 to a maximum of $100,000. Exceptional proposals above $200,000 may be considered depending on funding availability.",
#             "Deadline": "April 30, 2024 (for the second round of applications)"
#         }
#     }

# tool = GoogleSheetTool()
# print(tool._run(data))