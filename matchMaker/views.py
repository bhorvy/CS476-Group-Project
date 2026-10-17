from django.http import HttpResponse
from django.template import loader

def matchMaker(request):
  template = loader.get_template('demo.html')
  return HttpResponse(template.render())

def signUpPage(request):
  template = loader.get_template('register.html')
  return HttpResponse(template.render())

def loginPage(request):
  template = loader.get_template('login.html')
  return HttpResponse(template.render())