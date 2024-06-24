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

class GoogleSheetExtractorTool(BaseTool):
    name: str = "GoogleSheetExtractor"
    description: str = "Extract specific details from a Google Sheet based on the current date's worksheet."

    def _run(self) -> str:
        try:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            
            # Authenticate and create the client
            creds = Credentials.from_service_account_file("sheetcredentials.json", scopes=scopes)
            client = gspread.authorize(creds)
            
            # Open the Google Sheet
            # workbook = client.open_by_key("1_k2DzIMttt7PvXg-V40_soNH6dA2-E8dG06T2uIhFgA")
            workbook = client.open_by_key("106aQX0mnIjGHeRt3tVA4-0DeRbeXsZa6i47Dg3Nzvc8")
            
            # Get the current date for the worksheet name
            worksheet_name = datetime.now().strftime("%Y-%m-%d")
            
            # Get the worksheet
            worksheet = None
            try:
                worksheet = workbook.worksheet(worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                return f"Worksheet '{worksheet_name}' not found."
            
            if worksheet:
                # Read data into a pandas DataFrame
                data = worksheet.get_all_values()
                df = pd.DataFrame(data[1:], columns=data[0])  
                
                # Filter specific details
                selected_columns = df[["Opportunity number","Supplier match", "Supplier’s matching product", "Local partner requirements", "Requirement details"]]
                
                # Convert the DataFrame to a string
                result = selected_columns.to_string(index=False)
                return result
            else:
                return "No worksheet available for the current date."
        except Exception as e:
            return f"An error occurred: {e}"
