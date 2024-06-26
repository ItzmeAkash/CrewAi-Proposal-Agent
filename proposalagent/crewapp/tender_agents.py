import os
from crewai import Agent
from langchain_openai import ChatOpenAI
from crewai_tools import PDFSearchTool,FileReadTool
from crewapp.tools.GoogleDrive.google_drive_tools import GoogleDriveDownloaderTool
from crewapp.tools.GoogleSheetTool import GoogleSheetTool
from crewapp.tools.GoogleSheetExtractorTool import GoogleSheetExtractorTool
from dotenv import load_dotenv


load_dotenv()


class TenderPrePreparationAgents:
    def __init__(self):
        self.OpenAIGpt35 = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", api_key=os.getenv('OPENAI_API_KEY'))
        self.OpenAIGpt4o = ChatOpenAI(model_name="gpt-4o", api_key=os.getenv('OPENAI_API_KEY'))
        self.google_drive_tool = GoogleDriveDownloaderTool()
        self.google_sheet_tool = GoogleSheetTool()
        self.pdf_search_tool = PDFSearchTool()
        self.google_sheet_extractor_tool = GoogleSheetExtractorTool()
        # self.combinetextfile_tool = CombineTextFilesFromCurrentDirectoryTool()
        self.file_reader_tool = FileReadTool()
        
        
    # Google Drive Downloader Agent
    def google_drive_agent(self, folder_link):
        return Agent(
            role='Downloader',
            goal=f'Download necessary files from Google Drive on this {folder_link}',
            backstory=(
                "As a meticulous and efficient assistant, you ensure that all"
                " necessary files are retrieved from Google Drive swiftly and securely."
            ),
            verbose=True,
            memory=True,
            tools=[self.google_drive_tool],
            allow_delegation=True,
            llm=self.OpenAIGpt35
        )

    # PDF Specific Data Extraction Agent
    def pdf_extraction_agent(self, pdf_path):
        return Agent(
            role='Data Extraction Specialist',
            goal=f'Extract specific data fields from the PDF document at {pdf_path}',
            verbose=True,
            memory=True,
            backstory=(
                "As a detail-oriented analyst, you are tasked with extracting crucial information"
                " from PDF documents to support business operations and decision-making."
            ),
            tools=[self.pdf_search_tool],
            allow_delegation=True,
            llm=self.OpenAIGpt35
        )
        
    # Google Sheet Storing Agent
    def google_sheet_organiser_agent(self):
        return Agent(
            role='Data Entry Specialist',
            goal='Ensure the Google Sheet is up-to-date with the latest data entries.',
            backstory=(
                "A meticulous and detail-oriented data entry specialist committed to maintaining "
                "accurate and current records in Google Sheets."
            ),
            tools=[self.google_sheet_tool],
            verbose=True,
            memory=True,
            allow_delegation=True,
            llm=self.OpenAIGpt35
        )

    # Google Sheet Extracted Agent 
    def data_extract_specialist(self):
        return Agent(
            role='Data Extract Specialist',
            goal='Ensure extracting selected data.',
            backstory=(
                "A meticulous and detail-oriented data extractor specialist "
                "accurate and current records in Google Sheets."
            ),
            memory=True,
            verbose=True,
            tools=[self.google_sheet_extractor_tool],
            llm=self.OpenAIGpt35,
            allow_delegation=True,
            
        )
        
    # Proposal Template Agent
    def proposal_template_agent(self):
        return Agent(
            role="AI Proposal Writer",
            backstory=(
                "An expert AI Proposal Writer with years of experience crafting winning bids across various industries."
                "You have helped numerous startups and established companies secure lucrative contracts by developing compelling, well-structured proposals tailored to each unique opportunity."
            ),
            goal=(
                "Create a professionally formatted proposal template, minimum 4 pages long, with appropriate headings, subheadings, and bullet points where necessary."
                "Ensure logical structure based on the tender, with each section integrating and expanding on the relevant information."
                "Include placeholders (___) for client-specific information with brief descriptions and highlight areas needing additional information with suggestions for improvement."
                "Use clear, confident, and professional language throughout the document."
            ),
            llm=self.OpenAIGpt35,
            tools=[self.pdf_search_tool],
            verbose=True,
            memory=True,
            allow_delegation=True,

        )

    # Proposal Writer Agent
    def proposal_writer_agent(self):
        return Agent(
            role="Proposal Writer Specialist",
            backstory=(
                "You are a proposal writer specialist having specialization in crafting compelling proposals. "
                "Your expertise lies in creating documents that effectively present value propositions and align with tender requirements."
            ),
            goal=(
                "Using the provided proposal template and context, create a comprehensive and compelling proposal for the supplier."
                "Integrate all provided information and elaborate where necessary."
                "Ensure a strong executive summary, detailed sections tailored to the supplier's products, and a conclusion that reinforces why the supplier is the superior choice."
                "Fill in any gaps with your assumptions to make the proposal valid and compelling."
            ),
            verbose=True,
            memory=True,
            llm=self.OpenAIGpt35,
            allow_delegation=True,
        )
        
    def google_search_agent(self):
        return Agent(
            role="Google Search  Engine",
            backstory=(
                "You a an engine that can give an endless browsing support to google search"
            ),
            goal=(
                    "You can go to google search in depth with latest information"
            ),
            verbose=True,
            memory=True,
            llm=self.OpenAIGpt35,
            allow_delegation=True,
        )
    
    def google_search_supplier_finder_agent(self):
        return Agent(
            role="Google Search supplier Engine",
            backstory=(
                "You a an engine that can give an endless browsing support to google search"
            ),
            goal=(
                    "You can go to google search in depth with latest information"
            ),
            verbose=True,
            memory=True,
            llm=self.OpenAIGpt35,
            allow_delegation=True,
        )
        