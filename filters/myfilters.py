from google.appengine.ext import webapp
from django.utils.safestring import mark_safe

register = webapp.template.create_template_register()

@register.filter
def HTMLbreaks(value):
	return mark_safe(value.replace('\n','<br />'))

@register.filter
def removebreaks(value):
	return value.replace('\r\n',' ')
	
@register.filter
def ConvertToRatingPixels(value):
	# ((120px - 8px border) * value) / 5 + 4 yields 22.4 * value
	return int(round(22.4 * value)+4)
