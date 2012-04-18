#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, HttpResponse
from django.template import RequestContext

from .utils import *
from rapidsms_httprouter.models import Message
from generic.views import generic
from rapidsms_httprouter.models import Message
from generic.sorters import SimpleSorter, TupleSorter
import datetime, time
from generic.reporting.forms import DateRangeForm
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required
from xlrd import open_workbook
from .tasks import *



@login_required
def message_classification(request):

    if request.method == "POST":
        if request.FILES:
            upload_form = ExcelUploadForm(request.FILES)
            poll_form=PollUploadForm()

            if upload_form.is_valid():
                excel = request.FILES['excel_file'].read()
                message = HandleExcelClassification.delay(excel)
            if poll_form.is_valid():
                excel = request.FILES['excel'].read()
                message = HandleExcelClassification.delay(excel)
                message = UploadResponsesTask.delay(excel)



        if request.POST:
            msg_form = filterForm(request.POST)


            if msg_form.is_valid():

                result = ProcessExcelExportTask.delay(msg_form.cleaned_data['startdate'], msg_form.cleaned_data['enddate'],
                                                      msg_form.cleaned_data.get('size', 30), msg_form.cleaned_data['name'],
                                                      request.user)
                return HttpResponse(status=200)


    categories = ClassifierCategory.objects.all()
    reports=Report.objects.filter(user=request.user).order_by('-date')[5:]
    departments = Department.objects.all()
    category_form = CategoryForm()

    msg_form = filterForm()
    upload_form = ExcelUploadForm()
    poll_form=PollUploadForm()

    messages =\
    ScoredMessage.objects.all().order_by('-message__date')
    columns = [('Text', True, 'message__text', SimpleSorter()),
        ('Contact Information', True, 'message__connection__contact__name', SimpleSorter(),),
        ('Category', True, 'trained_as', SimpleSorter(),),
        ('Train', True, 'message__application', SimpleSorter(),),

    ]

    return generic(
        request,
        model=ScoredMessage,
        queryset=messages,
        objects_per_page=20,
        results_title='Trained Messages',
        selectable=False,
        partial_row='message_classifier/message_row.html',
        base_template='message_classifier/message_classifier_base.html',
        columns=columns,
        sort_column='date',
        sort_ascending=False,
        msg_form=msg_form,
        upload_form=upload_form,
        departments=departments,
        categories=categories,
        category_form=category_form,
        reports=reports,
        poll_form=poll_form,
        )


def train(request, message_pk, category_pk):
    msg = ScoredMessage.objects.get(pk=message_pk)
    cat = ClassifierCategory.objects.get(pk=category_pk)
    classifier = FisherClassifier(getfeatures)
    msg.train(FisherClassifier, getfeatures, cat)
    return HttpResponse(cat.name)




def edit_category(request, category_pk):
    category = ClassifierCategory.objects.get(pk=category_pk)
    if request.method == 'POST':
        category_form = CategoryForm(request.POST, instance=category)
        if category_form.is_valid():
            category_form.save()
            return HttpResponse("Saved")

    category_form = CategoryForm(instance=category)

    return render_to_response('message_classifier/category_partial.html',
                              dict(category_form=category_form, category=category),
                              context_instance=RequestContext(request))


