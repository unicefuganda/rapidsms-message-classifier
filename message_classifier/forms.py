# -*- coding: utf-8 -*-
from django import forms
from django.forms.util import ErrorList
from .models import *
from poll.models import Poll
from generic.forms import FilterForm


class filterForm(forms.Form):
    startdate = forms.DateField(('%d/%m/%Y',), label='Start Date', required=False,
                                widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                    'class': 'input',
                                    'readonly': 'readonly',
                                    'size': '15'
                                }))
    enddate = forms.DateField(('%d/%m/%Y',), label='End Date', required=False,
                              widget=forms.DateTimeInput(format='%d/%m/%Y', attrs={
                                  'class': 'input',
                                  'readonly': 'readonly',
                                  'size': '15'
                              }))
    name = forms.CharField(max_length=30, required=True)
    size = forms.IntegerField(label="message size cuttoff", required=False)
    contains = forms.CharField(max_length=200, required=False,
                               help_text="put series of words separated by or e.g hiv or aids")


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(label='Classified Messages Excel File',
                                 required=False)


class PollUploadForm(forms.Form):
    poll = forms.ModelChoiceField(queryset=Poll.objects.all().order_by('-pk'))

    excel = forms.FileField(label='Poll Excel File',
                            required=False)


class ChooseCategoryForm(FilterForm):
    CATEGORIES = [("", "-----------")] + [(pk, name.capitalize()) for pk, name in
                                          list(IbmCategory.objects.values_list('category_id', 'name').order_by('name'))]
    category = forms.ChoiceField(choices=CATEGORIES)

    def filter(self, request, queryset):
        pk = self.cleaned_data['category']
        if not pk or pk == "":
            return queryset
        return queryset.filter(category__category_id=pk)