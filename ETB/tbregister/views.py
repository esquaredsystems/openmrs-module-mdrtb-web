from django.shortcuts import render


def homepage(request):
    return render(request, 'tbregister/base.html')
