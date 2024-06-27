from django.shortcuts import render, redirect
from crewapp.crew import TenderCrew
from django.http import JsonResponse, HttpResponse
import os
import shutil
import zipfile
from io import BytesIO

def index(request):
    if request.method == "POST":
        # Define the paths to the db and output and download folders
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dp_folder = os.path.join(BASE_DIR, 'db')
        output_folder = os.path.join(BASE_DIR, 'crewapp', 'output')
        download_folder = os.path.join(BASE_DIR, 'crewapp', 'downloaded')

        # Remove the db and output ,downloaded,folders if they exist
        try:
            if os.path.exists(dp_folder):
                shutil.rmtree(dp_folder)
        except OSError as e:
            print(f"Error: {dp_folder} : {e.strerror}")
        
        try:
            if os.path.exists(output_folder):
                shutil.rmtree(output_folder)
        except OSError as e:
            print(f"Error: {output_folder} : {e.strerror}")
        
        try:
            if os.path.exists(download_folder):
                shutil.rmtree(download_folder)
        except OSError as e:
            print(f"Error: {download_folder} : {e.strerror}")

        folder_link = request.POST.get('folder_link')
        request.session['folder_link'] = folder_link
        tender_crew = TenderCrew(folder_link)
        pdf_path = tender_crew.run_initial()
        request.session['pdf_path'] = pdf_path
        return redirect('human_input')
    return render(request, 'index.html')

def human_input(request):
    if request.method == "POST":
        feedback = request.POST.get('feedback')
        if feedback.lower() == 'done':
            folder_link = request.session.get('folder_link')
            pdf_path = request.session.get('pdf_path')
            tender_crew = TenderCrew(folder_link)
            tender_crew.pdf_path = pdf_path
            result = tender_crew.run_final()
            return render(request, 'result.html', {'result': result})
        else:
            pass
    return render(request, 'human_input.html')

def agent_status_view(request):
    if request.method == "GET":
        current_agent = TenderCrew.get_current_agent()
        return JsonResponse({'agent': current_agent})

def download_files(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_folder = os.path.join(BASE_DIR, 'crewapp', 'output')

    try:
        files_to_download = os.listdir(output_folder)
    except FileNotFoundError:
        files_to_download = []

    if files_to_download:
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for file_name in files_to_download:
                file_path = os.path.join(output_folder, file_name)
                try:
                    zip_file.write(file_path, file_name)
                except FileNotFoundError:
                    print(f"Error: {file_path} not found and skipped.")
        
        
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=proposalcrew.zip'
        return response
    else:
        return render(request, 'error.html', {'error_message': 'No files to download.'})
