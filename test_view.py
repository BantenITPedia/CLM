from django.shortcuts import render

def format_test_view(request):
    return render(request, 'format_test.html')
