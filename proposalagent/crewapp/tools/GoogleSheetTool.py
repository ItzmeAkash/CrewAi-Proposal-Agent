import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import PDFSearchTool, BaseTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import json
from typing import List,Dict

class GoogleSheetTool(BaseTool):
    name: str = "GoogleSheetTool"
    description: str = "Tool to store data into a Google Sheet using gspread and Google service account credentials"

    def _run(self, data: List[Dict[str, str]]) -> str:
        try:
            # Define the required scope
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]

            # Authenticate and create the client
            creds = Credentials.from_service_account_file("sheetcredentials.json", scopes=scopes)
            client = gspread.authorize(creds)

            # Define the Google Sheet ID
            # sheet_id = "1_k2DzIMttt7PvXg-V40_soNH6dA2-E8dG06T2uIhFgA"
            sheet_id = "106aQX0mnIjGHeRt3tVA4-0DeRbeXsZa6i47Dg3Nzvc8"

            # Open the Google Sheet
            workbook = client.open_by_key(sheet_id)

            # Data to be added or updated
            new_values = data

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