from crewai import Task
from crewai_tools import PDFSearchTool, FileReadTool
from tools.GoogleDrive.google_drive_tools import GoogleDriveDownloaderTool
from tools.GoogleSheetTool import GoogleSheetTool
from tools.GoogleSheetExtractorTool import GoogleSheetExtractorTool
from util import RepeatedHumanInputTask

class TenderTask:
    def __init__(self):
        self.pdf_search_tool = PDFSearchTool()
        self.google_drive_tools = GoogleDriveDownloaderTool()
        self.google_sheet_tools = GoogleSheetTool()
        self.google_sheet_extractor_tool = GoogleSheetExtractorTool()
        self.file_read_tool = FileReadTool()
        
    # Google Drive Downloader Task
    def google_drive_task(self, agent):
        return Task(
            description="Download the specified file from Google Drive using its file ID.",
            expected_output='Confirmation of file download with file path',
            tools=[self.google_drive_tools],
            agent=agent,
        )

    # PDF Specific Data Extraction Task
    def pdf_extraction_task(self, agent, pdf_path):
        return Task(
            description=(
                f"Extract the following data from the PDF document located at {pdf_path}: "
                "Opportunity number, Opportunity name, Opportunity description, Location, Budget, and Deadline."
            ),
            expected_output=(
                "A dictionary containing the extracted data fields: "
                "'Opportunity number', 'Opportunity name', 'Opportunity description',"
                "'Location', 'Budget', 'Deadline'"
            ),
            tools=[self.pdf_search_tool],
            agent=agent,
            output_file="extracted_data.json"
        )

    # Google Sheet Storing Task
    def google_sheet_organiser_task(self, agent):
        return RepeatedHumanInputTask(
            description="Add the extracted data to the Google Sheet using GoogleSheetTool to add the extracted data into the Google Sheet.",
            expected_output='A confirmation message stating that the Google Sheet has been updated successfully.',
            tools=[self.google_sheet_tools],
            agent=agent,
            
            
        )

    # Google Sheet Extracted Task
    def extract_sheet_task(self, agent):
        return Task(
            description="Extract the selected data from the Google Sheet.",
            expected_output=(
                "The details should include Opportunity number ,Supplier match, Supplier’s matching product,Local partner requirements,Requirement details and other relevant information present in the Google Sheet"
            ),
            agent=agent,
            tools=[self.google_sheet_extractor_tool],
            output_file='excel.txt',
            async_execution=False,
        )
         
    # Proposal Template Task
    def proposal_template_task(self, agent, pdf_file):
        return Task(
            description=(
                f"Create a comprehensive proposal template based on the tender {pdf_file} attached. "
                "The template should be a minimum of 4 pages long, structured logically, "
                "and integrate all the information from the tender. Use placeholders for client-specific information "
                "and provide descriptions for these placeholders. Highlight areas needing additional information "
                "and suggest improvements. Use clear, professional language throughout."
            ),
            expected_output=(
                "A professionally formatted proposal template, minimum 4 pages long, with appropriate headings, subheadings, "
                "and bullet points where necessary. Logical structure based on the tender attached, with each section integrating "
                "and expanding on the relevant information. Placeholders for client-specific information with brief descriptions. "
                "Highlighted areas needing additional information with suggestions for strengthening these sections. Clear, confident, "
                "and professional language throughout."
            ),
            agent=agent,
            output_file='proposal_template.txt',
            tools=[self.pdf_search_tool],
        )
        
    # Proposal Writer Task
    def proposal_writer_task(self, agent):
        return Task(
            description=(
                "Using the provided proposal template and context, create a comprehensive and compelling proposal for the supplier. "
                "Integrate all provided information and elaborate where necessary. Ensure a strong executive summary, detailed sections "
                "tailored to the supplier's products, and a conclusion that reinforces why the supplier is the superior choice. "
                "Fill in any gaps with your assumptions to make the proposal valid and compelling."
            ),
            expected_output=(
                "A polished, comprehensive proposal document that follows the provided template structure. "
                "Each section supported by provided data, research findings, and supplier's information. "
                "A strong executive summary that encapsulates the key value propositions and supplier background. "
                "Detailed sections as per the template tailored to the supplier's unique offerings. "
                "Data points illustrating the supplier's impact. "
                "Conclusion reinforcing why the supplier is the superior choice and how their goals align with the tender."
            ),
            agent=agent,
            output_file='final_proposal.txt',
        )
    
    def google_search_task(self,agent,prompt):
        return Task(
            description=(
                f"Based on give {prompt} you have to go to google search and give us the latest information"
            ),
            expected_output=(
                "Top 15 company names that match the provided details and we are expecting the company details, like website small description about company,there product and there link,website contact details, make sure only search based on provided details"
            ),
            agent=agent,
            output_file='googlesearch.txt',
        )


    def google_search_supplier_finder_task(self,agent,prompt):
        return Task(
            description=(
                f"Based on give {prompt} you have to go to google search and give us the latest information"
            ),
            expected_output=(
                "Top 15 company names who has a product that matches the provided details and can partner with us in the bidding process. We are expecting the company details, like website small description about company, their product and their link, website contact details, make sure only search based on provided details" 
            ),
            agent=agent,
            output_file='googlesearchsupplierFinder.txt',
        )
    
        c