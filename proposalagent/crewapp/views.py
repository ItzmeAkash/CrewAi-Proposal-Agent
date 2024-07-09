from django.shortcuts import render, redirect
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from datetime import datetime
from crewapp.crew import TenderCrew
from django.http import JsonResponse, HttpResponse
import os
import shutil
import zipfile
from io import BytesIO
from langchain_openai import ChatOpenAI
from django.views.decorators.csrf import csrf_exempt
from docx import Document   


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'crewapp', 'googlesheetcredentials.json')

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.6
)

def rewrite_text(input_text: str, prompt_suffix: str) -> str:
    prompt = f"""
        You are an AI assistant here to help with anything requested.

        Input text: {input_text}

        Prompt to change the input text: {prompt_suffix}

        Please combine the input text and the generated result, updating only as specified.

        expected only the combined generative results 
        """
    
    response = llm.invoke(prompt)
    return response.content

def index(request):
    error_message = None
    
    if request.method == "POST":
        try:
            dp_folder = os.path.join(BASE_DIR, 'db')
            output_folder = os.path.join(BASE_DIR, 'crewapp', 'output')
            download_folder = os.path.join(BASE_DIR, 'crewapp', 'downloaded')

            for folder in [dp_folder, output_folder, download_folder]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)

            folder_link = request.POST.get('folder_link')
            request.session['folder_link'] = folder_link
            tender_crew = TenderCrew(folder_link)
            pdf_path = tender_crew.run_initial()
            request.session['pdf_path'] = pdf_path

            return redirect('human_input')
        
        except Exception as e:
            error_message = str(e)
    return render(request, 'index.html', {'error_message': error_message})

def human_input(request):
    error_message = None
    result = None
    current_row = request.session.get('current_row', 1)

    if request.method == "POST":
        try:
            feedback = request.POST.get('feedback')
            if feedback.lower() == 'done':
                data = {
                    'Supplier match': request.POST.get('Supplier match'),
                    'Supplier’s matching product': request.POST.get('Supplier’s matching product'),
                    'Local partner requirements': request.POST.get('Local partner requirements'),
                    'Requirement details': request.POST.get('Requirement details')
                }
                store_data_in_google_sheet(data, current_row)
                folder_link = request.session.get('folder_link')
                pdf_path = request.session.get('pdf_path')
                tender_crew = TenderCrew(folder_link)
                tender_crew.pdf_path = pdf_path
                result = tender_crew.run_final()
                request.session['result'] = result
                return render(request, 'result.html', {'result': result})
            else:
                error_message = "Please type 'done' to proceed."
        except Exception as e:
            error_message = str(e)

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
        client = gspread.authorize(creds)

        workbook = client.open_by_key("1_k2DzIMttt7PvXg-V40_soNH6dA2-E8dG06T2uIhFgA")
        worksheet_name = datetime.now().strftime("%Y-%m-%d")

        try:
            worksheet = workbook.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            error_message = f"Worksheet '{worksheet_name}' not found."
            worksheet = None

        if worksheet:
            data = worksheet.get_all_values()
            df = pd.DataFrame(data[1:], columns=data[0])
            selected_columns = df[["Opportunity number", "Opportunity name", "Opportunity description", "Location", "Budget", "Deadline"]]
            result = selected_columns.to_html(index=False, classes='table table-striped table-bordered')

            current_row = len(data) - 1
            request.session['current_row'] = current_row
            
    except Exception as e:
        error_message = str(e)

    return render(request, 'human_input.html', {'error_message': error_message, 'result': result})

def store_data_in_google_sheet(data, current_row):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = "1_k2DzIMttt7PvXg-V40_soNH6dA2-E8dG06T2uIhFgA"
        workbook = client.open_by_key(sheet_id)
        worksheet_name = datetime.now().strftime("%Y-%m-%d")
        sheet = workbook.worksheet(worksheet_name)
        existing_data = sheet.get_all_values()

        if current_row > len(existing_data):
            raise IndexError("The current row index is out of range.")

        new_row = [
            existing_data[current_row][0],  # Opportunity number
            existing_data[current_row][1],  # Opportunity name
            existing_data[current_row][2],  # Opportunity description
            existing_data[current_row][3],  # Location
            existing_data[current_row][4],  # Budget
            existing_data[current_row][5],  # Deadline
            data.get("Supplier match", existing_data[current_row][6]),
            data.get("Supplier’s matching product", existing_data[current_row][7]),
            data.get("Local partner requirements", existing_data[current_row][8]),
            data.get("Requirement details", existing_data[current_row][9]),
        ]

        sheet.update(f'A{current_row + 1}:K{current_row + 1}', [new_row])
        return "Google Sheet updated successfully."
    
    except Exception as e:
        return f"An error occurred: {e}"

def agent_status_view(request):
    if request.method == "GET":
        current_agent = TenderCrew.get_current_agent()
        return JsonResponse({'agent': current_agent})

def download_files(request):
    error_message = None
    output_folder = os.path.join(BASE_DIR, 'crewapp', 'output')

    try:
        files_to_download = os.listdir(output_folder)
    except FileNotFoundError:
        files_to_download = []

    if files_to_download:
        try:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for file_name in files_to_download:
                    file_path = os.path.join(output_folder, file_name)
                    zip_file.write(file_path, file_name)
            
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=proposalcrew.zip'
            return response
        except Exception as e:
            error_message = str(e)
    else:
        error_message = 'No files to download.'

    return render(request, 'error.html', {'error_message': error_message})


@csrf_exempt
def update_proposal(request):
    if request.method == "POST":
        prompt = request.POST.get('prompt')
        result = request.session.get('result')

        if not result:
            return redirect('index')

        # Extract the proposal_result to rewrite
        proposal_result = result.get("proposal_result")
        
        print(proposal_result)
        # Combine the proposal_result with the prompt
        input_text = proposal_result
        prompt_suffix = f"{prompt}"

        # Get the rewritten text
        rewritten_text = rewrite_text(input_text, prompt_suffix)

        # Update only the proposal_result in the result dictionary
        result["proposal_result"] = rewritten_text.strip()

        # Save the updated proposal to a .docx file in the output folder
        output_folder = os.path.join(BASE_DIR, 'crewapp', 'output')
        proposal_file_path = os.path.join(output_folder, 'proposal.docx')
        document = Document()
        document.add_paragraph(result["proposal_result"])
        document.save(proposal_file_path)

        # Update the session with the modified result
        request.session['result'] = result
        
        # print(result)
        return render(request, 'result.html', {'result': result})
    
    return redirect('index')
