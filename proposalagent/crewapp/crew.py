import os
from dotenv import load_dotenv
from crewai import Crew, Process
from crewapp.tender_agents import TenderPrePreparationAgents
from crewapp.tender_tasks import TenderTask
from textwrap import dedent
import pandas as pd
import json
import re
import logging
load_dotenv()


class TenderCrew:
    def __init__(self, folder_link):
        self.folder_link = folder_link

    def find_pdf_path(self, directory):
        """
        Traverse the directory to find the first PDF file path.
        """
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.pdf'):
                    return os.path.join(root, file)
        return None

    def extract_json_content(self, text):
        """
        Extract JSON content from text.
        """
        # Use regular expressions to find JSON content
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            print("No JSON content found.")
            return None

    def load_json(self, file_path):
        """
        Load JSON data from a file, extracting valid JSON if necessary.
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        if os.stat(file_path).st_size == 0:
            print(f"File is empty: {file_path}")
            return None

        try:
            with open(file_path, 'r') as file:
                content = file.read()
                json_content = self.extract_json_content(content)
                if json_content:
                    data = json.loads(json_content)
                    return data
                else:
                    print("Failed to extract JSON content.")
                    return None
        except json.JSONDecodeError as e:
            print(f"Error loading JSON file: {e}")
            return None

    def run_initial(self):

        agents = TenderPrePreparationAgents()
        tasks = TenderTask()

        def update_progress(message):
            print(message)

        # Google Drive Agent and Task
        google_drive_agent = agents.google_drive_agent(self.folder_link)
        google_drive_task = tasks.google_drive_task(google_drive_agent)

        # Running the initial crew to download the files from Google Drive
        initial_crew = Crew(
            agents=[google_drive_agent],
            tasks=[google_drive_task],
            verbose=True,
            process=Process.sequential,
        )
        initial_crew.kickoff()

        # Automatically detect the PDF path
        # Get the current script directory
        current_directory = os.path.dirname(__file__)

        # Specify the download directory relative to the current script directory
        download_directory = os.path.join(current_directory, 'downloaded')

        pdf_path = self.find_pdf_path(download_directory)
        update_progress("Finding PDF Path...")

        if not pdf_path:
            raise FileNotFoundError("No PDF file found in the specified directory.")

        # PDF Extraction Agent and Task
        pdf_extraction_agent = agents.pdf_extraction_agent(pdf_path)
        pdf_extraction_task = tasks.pdf_extraction_task(pdf_extraction_agent, pdf_path)

        # Google Sheet Agent and Task
        google_sheet_organiser_agent = agents.google_sheet_organiser_agent()
        google_sheet_organiser_task = tasks.google_sheet_organiser_task(google_sheet_organiser_agent)
        
        pdf_and_google_sheet_crew = Crew(
            agents=[pdf_extraction_agent, google_sheet_organiser_agent],
            tasks=[pdf_extraction_task, google_sheet_organiser_task],
            verbose=True,
            process=Process.sequential,
        )
        pdf_and_google_sheet_crew.kickoff()

        return pdf_path

    def run_final(self):

        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.debug("Starting run_final method")
        current_directory = os.path.dirname(__file__)

        # Specify the download directory relative to the current script directory
        download_directory = os.path.join(current_directory, 'downloaded')

        pdf_path = self.find_pdf_path(download_directory)
        
        agents = TenderPrePreparationAgents()
        tasks = TenderTask()

        # Proposal Template Agent and Task
        proposal_template_agent = agents.proposal_template_agent()
        proposal_template_task = tasks.proposal_template_task(proposal_template_agent, pdf_path)

        # Extract opportunity number from JSON
        json_filename = 'extracted_data.json'
        json_path = os.path.join('crewapp', json_filename)
        json_data = self.load_json(json_path)

        if json_data:
            opportunity_number = json_data.get('Opportunity number', None)
            logging.debug(f"Extracted Opportunity number: {opportunity_number}")
            print(opportunity_number)
        else:
            logging.error("Failed to load JSON data.")
            print("Failed to load JSON data.")

        # Google Sheet Extraction Agent and Task
        data_extract_specialist_agent = agents.data_extract_specialist()
        data_extract_specialist_agent_task = tasks.extract_sheet_task(data_extract_specialist_agent, opportunity_number)

        data_extraction_crew = Crew(
            agents=[
                data_extract_specialist_agent,
            ],
            tasks=[
                data_extract_specialist_agent_task
            ],
            verbose=True,
            process=Process.sequential,
        )
        
        data_extraction_crew.kickoff()
                
        # Proposal Writer Agent and Task
        proposal_writer_agent = agents.proposal_writer_agent()
        proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
        proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]

        # file_path = os.path.join('proposalagent','crewapp', 'excel.txt')

        # Define the file path
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, 'excel.txt')

        # Read the file
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Initialize a dictionary to hold the parsed data
        data = {}

        # Process each line to normalize and parse it
        for line in lines:
            line = line.strip()
            if line.startswith("**"):
                line = line[2:].strip()
            elif line.startswith("-"):
                line = line[1:].strip()

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Check if the key already exists in the dictionary
                if key not in data:
                    data[key] = value
                else:
                    # If the key exists, you can implement a rule to decide which value to keep
                    # For example, prefer the value from the "**" line over the "-" line
                    if line.startswith("**"):
                        data[key] = value

        # Convert the dictionary into a DataFrame
        exceldf = pd.DataFrame([data])
        
        exceldf.columns = exceldf.columns.str.replace(r'\W+', '', regex=True).str.lower()

        
        # Initialize result variable
        result = ""

        # Check the "Supplier match" condition
        logging.debug(f"Supplier match: {exceldf['suppliermatch']}, Local partner requirements: {exceldf['localpartnerrequirements']}")
        if exceldf['suppliermatch'].iloc[0].lower() in ['n', 'no'] and exceldf['localpartnerrequirements'].iloc[0].lower() in ['n', 'no']:
            # prompt = exceldf['Supplierâ€™s Matching Product'][0]
            prompt = exceldf['suppliersmatchingproduct'][0]

            
            google_search_supplier_finder_agent = agents.google_search_supplier_finder_agent()
            google_search_supplier_finder_task = tasks.google_search_supplier_finder_task(google_search_supplier_finder_agent, prompt)
            
            
            local_search = exceldf['requirementdetails'][0]
            google_search_agent = agents.google_search_agent()
            google_search_task = tasks.google_search_task(google_search_agent, local_search)
            
            # Run the Google Search Crew for Supplier Finder
            supplier_finder_crew = Crew(
                agents=[google_search_supplier_finder_agent],
                tasks=[google_search_supplier_finder_task],
                verbose=True,
                process=Process.sequential
            )

            supplier_result = supplier_finder_crew.kickoff()
            logging.debug(f"Supplier finder result: {supplier_result}")
            result += "\n\n########################"
            result += "\n## Google Search Supplier Finder Results"
            result += "\n########################\n"
            result += supplier_result
            
            # Run the Google Search Crew for Local Partner Requirements
            search_crew = Crew(
                agents=[google_search_agent],
                tasks=[google_search_task],
                verbose=True,
                process=Process.sequential
            )

            search_result = search_crew.kickoff()
            logging.debug(f"Google search result: {search_result}")
            result += "\n\n########################"
            result += "\n## Google Search Results"
            result += "\n########################\n"
            result += search_result
            
        elif exceldf['suppliermatch'].iloc[0].lower() not in ['n', 'no'] and  exceldf['localpartnerrequirements'].iloc[0].lower() in ['n', 'no']:
            local_search = exceldf['requirementdetails'][0]
            
            proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
            proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]
            
            google_search_agent = agents.google_search_agent()
            google_search_task = tasks.google_search_task(google_search_agent, local_search)
            # Run the Proposal Writing Crew
            proposal_crew = Crew(
                agents=[proposal_template_agent,proposal_writer_agent],
                tasks=[proposal_template_task,proposal_writer_task],
                verbose=True,
                process=Process.sequential
            )

            proposal_result = proposal_crew.kickoff()
            logging.debug(f"Proposal writing result: {proposal_result}")
            result += "\n\n########################"
            result += "\n## Proposal Writing Results"
            result += "\n########################\n"
            result += proposal_result
            
            
            # Run the Google Search Crew for Local Partner Requirements
            search_crew = Crew(
                agents=[google_search_agent],
                tasks=[google_search_task],
                verbose=True,
                process=Process.sequential
            )

            search_result = search_crew.kickoff()
            logging.debug(f"Google search result: {search_result}")
            result += "\n\n########################"
            result += "\n## Google Search Results"
            result += "\n########################\n"
            result += search_result
            
            
            
        elif exceldf['suppliermatch'].iloc[0].lower() not in ['n', 'no'] and exceldf['localpartnerrequirements'].iloc[0].lower() not in ['n', 'no']:

             # Run the Google Search Crew for Supplier Finder

            proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
            proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]

            # Run the Proposal Writing Crew
            proposal_crew = Crew(
                agents=[proposal_template_agent,proposal_writer_agent],
                tasks=[proposal_template_task,proposal_writer_task],
                verbose=True,
                process=Process.sequential
            )

            proposal_result = proposal_crew.kickoff()
            logging.debug(f"Proposal writing result: {proposal_result}")
            result += "\n\n########################"
            result += "\n## Proposal Writing Results"
            result += "\n########################\n"
            result += proposal_result


       
        logging.debug(f"Final result: {result}")
        return result   