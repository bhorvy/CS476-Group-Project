from django import template

register = template.Library()

@register.filter
def getId(dictionary, key):
    return dictionary.get(key)