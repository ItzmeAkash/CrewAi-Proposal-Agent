#Crew.py
import os
from dotenv import load_dotenv
from crewai import Crew, Process
from crewapp.tender_agents import TenderPrePreparationAgents
from crewapp.tender_tasks import TenderTask
from docx import Document
import pandas as pd
import json
import re
import logging
load_dotenv()

class TenderCrew:
    def __init__(self, folder_link):
        self.folder_link = folder_link

    def find_pdf_path(self, directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.pdf'):
                    return os.path.join(root, file)
        return None

    def extract_json_content(self, text):
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            print("No JSON content found.")
            return None

    def load_json(self, file_path):
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

    def save_result_as_docx(self, result_text, file_name):
        output_folder = os.path.join(os.path.dirname(__file__), 'output')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        output_filename = os.path.join(output_folder, file_name)
        # Create a Document object
        doc = Document()
        
        # Add a paragraph with the text
        doc.add_paragraph(result_text)
        
        # Save the document
        doc.save(output_filename)
        print(f"Docx saved to {output_filename}")

    global cur
    cur = "Agents are currently Inactive..."

    def get_current_agent():
        global cur 
        return cur

    def run_initial(self):
        agents = TenderPrePreparationAgents()
        tasks = TenderTask()
        global cur
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
        cur = "Downloader: The agent is currently downloading the PDF from Drive."
        initial_crew.kickoff()

        # Automatically detect the PDF path
        current_directory = os.path.dirname(__file__)
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
        cur = "Extractor: Agent is currently retrieving data from the PDF."
        pdf_and_google_sheet_crew.kickoff()

        return pdf_path

    def run_final(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.debug("Starting run_final method")

        agents = TenderPrePreparationAgents()
        tasks = TenderTask()
        proposal_template_agent = agents.proposal_template_agent()
        proposal_template_task = tasks.proposal_template_task(proposal_template_agent, self.pdf_path)

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

        data_extract_specialist_agent = agents.data_extract_specialist()
        data_extract_specialist_agent_task = tasks.extract_sheet_task(data_extract_specialist_agent, opportunity_number)

        data_extraction_crew = Crew(
            agents=[data_extract_specialist_agent],
            tasks=[data_extract_specialist_agent_task],
            verbose=True,
            process=Process.sequential,
        )
        global cur
        cur = "Google Sheet Extractor: Currently processing data retrieval from Google Sheets."
        data_extraction_crew.kickoff()

        proposal_writer_agent = agents.proposal_writer_agent()
        proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
        proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, 'excel.txt')

        with open(file_path, 'r') as file:
            lines = file.readlines()

        data = {}
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

                if key not in data:
                    data[key] = value
                else:
                    if line.startswith("**"):
                        data[key] = value

        exceldf = pd.DataFrame([data])
        exceldf.columns = exceldf.columns.str.replace(r'\W+', '', regex=True).str.lower()

        result = ""
        result_dict ={}

        if exceldf['suppliermatch'].iloc[0].lower() in ['n', 'no'] and exceldf['localpartnerrequirements'].iloc[0].lower() in ['n', 'no']:
            prompt = exceldf['suppliersmatchingproduct'][0]
            google_search_supplier_finder_agent = agents.google_search_supplier_finder_agent()
            google_search_supplier_finder_task = tasks.google_search_supplier_finder_task(google_search_supplier_finder_agent, prompt)

            local_search = exceldf['requirementdetails'][0]
            google_search_agent = agents.google_search_agent()
            google_search_task = tasks.google_search_task(google_search_agent, local_search)

            supplier_finder_crew = Crew(
                agents=[google_search_supplier_finder_agent],
                tasks=[google_search_supplier_finder_task],
                verbose=True,
                process=Process.sequential
            )

            supplier_result = supplier_finder_crew.kickoff()
            self.save_result_as_docx(supplier_result, 'googlesupplier.docx')
            logging.debug(f"Supplier finder result: {supplier_result}")
            result_dict["Supplier_result"] = supplier_result
            result += "\n\n########################"
            result += "\n## Google Search Supplier Finder Results"
            result += "\n########################\n"
            result += supplier_result

            search_crew = Crew(
                agents=[google_search_agent],
                tasks=[google_search_task],
                verbose=True,
                process=Process.sequential
            )
            cur = "Internet Search Assistant: Actively scanning for local patterns"
            search_result = search_crew.kickoff()
            self.save_result_as_docx(search_result, 'googlelocalpartner.docx')
            logging.debug(f"Google search result: {search_result}")
            result_dict["google_local_partner"] = search_result
            result += "\n\n########################"
            result += "\n## Google Search Results"
            result += "\n########################\n"
            result += search_result

        elif exceldf['suppliermatch'].iloc[0].lower() not in ['n', 'no'] and exceldf['localpartnerrequirements'].iloc[0].lower() in ['n', 'no']:
            local_search = exceldf['requirementdetails'][0]

            proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
            proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]

            google_search_agent = agents.google_search_agent()
            google_search_task = tasks.google_search_task(google_search_agent, local_search)
            proposal_crew = Crew(
                agents=[proposal_template_agent, proposal_writer_agent],
                tasks=[proposal_template_task, proposal_writer_task],
                verbose=True,
                process=Process.sequential
            )
            cur = "Proposal Writer: Agent is crafting a compelling proposal."
            proposal_result = proposal_crew.kickoff()
            self.save_result_as_docx(proposal_result, 'proposal.docx')
            logging.debug(f"Proposal writing result: {proposal_result}")
            result_dict["proposal_result"] = proposal_result
            result += "\n\n########################"
            result += "\n## Proposal Writing Results"
            result += "\n########################\n"
            result += proposal_result

            search_crew = Crew(
                agents=[google_search_agent],
                tasks=[google_search_task],
                verbose=True,
                process=Process.sequential
            )
            cur = "Internet Search Assistant: Actively scanning for local patterns"
            search_result = search_crew.kickoff()
            self.save_result_as_docx(search_result, 'googlelocalpartner.docx')
            logging.debug(f"Google search result: {search_result}")
            result_dict["google_local_partner"] = search_result
            result += "\n\n########################"
            result += "\n## Google Search Results"
            result += "\n########################\n"
            result += search_result

        elif exceldf['suppliermatch'].iloc[0].lower() not in ['n', 'no'] and exceldf['localpartnerrequirements'].iloc[0].lower() not in ['n', 'no']:
            proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
            proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]

            proposal_crew = Crew(
                agents=[proposal_template_agent, proposal_writer_agent],
                tasks=[proposal_template_task, proposal_writer_task],
                verbose=True,
                process=Process.sequential
            )
            cur = "Proposal Writer: Agent is crafting a compelling proposal."
            proposal_result = proposal_crew.kickoff()
            self.save_result_as_docx(proposal_result, 'proposal.docx')
            logging.debug(f"Proposal writing result: {proposal_result}")
            result_dict["proposal_result"] = proposal_result
            result += "\n\n########################"
            result += "\n## Proposal Writing Results"
            result += "\n########################\n"
            result += proposal_result

        logging.debug(f"Final result: {result}")
        return result_dict