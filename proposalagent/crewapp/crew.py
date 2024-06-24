import os
from dotenv import load_dotenv
from crewai import Crew, Process
from tender_agents import TenderPrePreparationAgents
from tender_tasks import TenderTask
from textwrap import dedent
import pandas as pd

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

    def run(self):
        agents = TenderPrePreparationAgents()
        tasks = TenderTask()

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
        download_directory = 'downloaded' 
        pdf_path = self.find_pdf_path(download_directory)
        print(pdf_path)

        if not pdf_path:
            raise FileNotFoundError("No PDF file found in the specified directory.")

        # PDF Extraction Agent and Task
        pdf_extraction_agent = agents.pdf_extraction_agent(pdf_path)
        pdf_extraction_task = tasks.pdf_extraction_task(pdf_extraction_agent, pdf_path)

        # Google Sheet Agent and Task
        google_sheet_organiser_agent = agents.google_sheet_organiser_agent()
        google_sheet_organiser_task = tasks.google_sheet_organiser_task(google_sheet_organiser_agent)

        # Google Sheet Extraction Agent and Task
        data_extract_specialist_agent = agents.data_extract_specialist()
        data_extract_specialist_agent_task = tasks.extract_sheet_task(data_extract_specialist_agent)

        # Proposal Template Agent and Task
        proposal_template_agent = agents.proposal_template_agent()
        proposal_template_task = tasks.proposal_template_task(proposal_template_agent, pdf_path)

        # Proposal Writer Agent and Task
        proposal_writer_agent = agents.proposal_writer_agent()
        proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
        proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]

        # Run the initial crew
        google_sheet_crew = Crew(
            agents=[
                pdf_extraction_agent,
                google_sheet_organiser_agent,
                proposal_template_agent,
                data_extract_specialist_agent,
            ],
            tasks=[
                pdf_extraction_task,
                google_sheet_organiser_task,
                proposal_template_task,
                data_extract_specialist_agent_task
            ],
            verbose=True,
            process=Process.sequential,
        )
        
        google_sheet_crew.kickoff()
                
        # Define the file path
        file_path = 'excel.txt'

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
        
        if exceldf['suppliermatch'].iloc[0].lower() in ['n', 'no']:
            # prompt = exceldf['Supplierâ€™s Matching Product'][0]
            prompt = exceldf['supplierâsmatchingproduct'][0]
            
            
            google_search_supplier_finder_agent = agents.google_search_supplier_finder_agent()
            google_search_supplier_finder_task = tasks.google_search_supplier_finder_task(google_search_supplier_finder_agent, prompt)

            # Run the Google Search Crew for Supplier Finder
            supplier_finder_crew = Crew(
                agents=[google_search_supplier_finder_agent],
                tasks=[google_search_supplier_finder_task],
                verbose=True,
                process=Process.sequential
            )

            supplier_result = supplier_finder_crew.kickoff()
            result += "\n\n########################"
            result += "\n## Google Search Supplier Finder Results"
            result += "\n########################\n"
            result += supplier_result
            
        # Check the "Local partner requirements" 
        if exceldf['localpartnerrequirements'].iloc[0].lower() in ['n', 'no']:
            prompt = exceldf['requirementdetails'][0]
            google_search_agent = agents.google_search_agent()
            google_search_task = tasks.google_search_task(google_search_agent, prompt)

            # Run the Google Search Crew for Local Partner Requirements
            search_crew = Crew(
                agents=[google_search_agent],
                tasks=[google_search_task],
                verbose=True,
                process=Process.sequential
            )

            search_result = search_crew.kickoff()
            result += "\n\n########################"
            result += "\n## Google Search Results"
            result += "\n########################\n"
            result += search_result
        else:
            proposal_writer_task = tasks.proposal_writer_task(proposal_writer_agent)
            proposal_writer_task.context = [data_extract_specialist_agent_task, proposal_template_task]

            # Run the Proposal Writing Crew
            proposal_crew = Crew(
                agents=[proposal_writer_agent],
                tasks=[proposal_writer_task],
                verbose=True,
                process=Process.sequential
            )

            proposal_result = proposal_crew.kickoff()
            result += "\n\n########################"
            result += "\n## Proposal Writing Results"
            result += "\n########################\n"
            result += proposal_result

        # # Run the remaining crew
        # remaining_crew = Crew(
        #     agents=[
        #         pdf_extraction_agent,
        #         google_sheet_organiser_agent,
        #         proposal_template_agent,
        #         data_extract_specialist_agent,
        #     ],
        #     tasks=[
        #         pdf_extraction_task,
        #         google_sheet_organiser_task,
        #         proposal_template_task,
        #         data_extract_specialist_agent_task,
        #     ],
        #     verbose=True,
        #     process=Process.sequential,
        # )

        # result += remaining_crew.kickoff()

        return result

if __name__ == "__main__":
    print("## Welcome to Proposal Writing Crew")
    print('-------------------------------')
    folder_link = input(
        dedent("""
            Please Enter your google drive link here:
        """)
    )
    tender_crew = TenderCrew(folder_link)
    result = tender_crew.run()
    print("\n\n########################")
    print("## Here is the Final Result ")
    print("########################\n")
    print(result)
