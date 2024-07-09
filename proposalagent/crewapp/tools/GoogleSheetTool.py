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
    description: str = "Tool to store data into a Google Sheet using gspread and Google service account credentials. The input should be a list of dictionaries, each containing the data to be stored."

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
# data = [
#     {
#         "Opportunity number": "72044224RFA00004",
#         "Opportunity name": "Bridging Education Solutions for Transformation (BEST) Activity",
#         "Opportunity description": "Supplementing the intervention description as stated in the Results Framework above, USAID and the recipient may identify opportunities for improving our response through this mechanism to address specific education priority needs that cannot be precisely identified during the design process, but emerge throughout implementation. Applying the opportunity module may also allow this activity to expand geographic coverage to other provinces/districts as appropriate or expand reach within existing provinces. Subject to funding availability, USAID will work with the recipient to identify priority needs and provide technical support by bringing national and international expertise to support interventions related to existing objectives.",
#         "Location": "Cambodia",
#         "Budget": "The Budget Narrative must contain sufficient detail to allow USAID to understand the proposed costs. The applicant must ensure the budgeted costs address any additional requirements identified in Section F, such as Branding and Marking. The Budget must include Summary Budget, Detailed Budget, and Detailed Budgets for each sub-recipient.",
#         "Deadline": "August 6, 2024 at 10 a.m. Cambodia time"
#     }
# ]

# tool = GoogleSheetTool()
# print(tool._run(data))