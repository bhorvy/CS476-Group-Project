from django.http import HttpResponse
from django.template import loader
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import get_user_model
from .models import Member

from .forms import RegisterForm
from .forms import LoginForm

def matchMaker(request):
  template = loader.get_template('demo.html')
  return HttpResponse(template.render())

def signUpPage(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = RegisterForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            User = get_user_model()
            data = form.cleaned_data

            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
            )

            Member.objects.create(
                user=user,
                firstname=data["first_name"],
                lastname=data["last_name"],
                gender=data["gender"],
                DOB=data["date_of_birth"],
            )
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/loginPage/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def loginPage(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/matchMaker/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

