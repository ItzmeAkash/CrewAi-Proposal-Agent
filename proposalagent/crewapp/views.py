from django.shortcuts import render, redirect
from crewapp.crew import TenderCrew
from django.http import JsonResponse

def index(request):
    if request.method == "POST":
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