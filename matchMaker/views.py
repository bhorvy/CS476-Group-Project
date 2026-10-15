from django.http import HttpResponse
from django.template import loader

def matchMaker(request):
  template = loader.get_template('demo.html')
  return HttpResponse(template.render())