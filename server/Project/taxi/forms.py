# from django import newforms as forms
from django import forms
from django.db import models

from models import SearchRequest

class DescriptionForm(forms.Form):
    """
    This form only holds a description for the models.Ride
    """
    description = forms.CharField(max_length=144, required = False)
    
class RideRequestForm(forms.ModelForm):
    """
    Form to make a request. Almost the entire SearchRequest, but left some
    things to be populated by the server side

    XXX: Since items are excluded, you MUST initialize them before saving
    otherwise it will not persist
    """
    class Meta:
        model = SearchRequest
        exclude = ('submission_time', 'user', 'ride')

