from django.shortcuts import render

def rentals_home(request):
    return render(request, "rentals/index.html")
