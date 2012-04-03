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

def handle_excel_file(file):
    if file:
        excel = file.read()
        workbook = open_workbook(file_contents=excel)
        worksheet = workbook.sheet_by_index(0)

        if worksheet.nrows > 1:
            validated_numbers = []
            for row in range(1, worksheet.nrows):
                pk, mobile, text, category = worksheet.cell(row, 0), worksheet.cell(row, 1), worksheet.cell(row,
                                                                                                            2), worksheet.cell(
                    row, 3)
                message = Message.objects.create(pk=pk)
                cat, created = ClassifierCategory.objects.get_or_create(name=category)

                sm, created = ScoredMessage.objects.get_or_create(message=message)
                sm.trained_as = cat
                sm.save()
                classifier = FisherClassifier(getfeatures)
                sm.train(FisherClassifier, getfeatures, cat)


        else:
            info =\
            'You seem to have uploaded an empty excel file'
    else:
        info = 'Invalid file'
    return info


@login_required
def message_classification(request):
    if request.method == "POST":
        if request.FILES:
            upload_form = ExcelUploadForm(request.FILES)
            if upload_form.is_valid():
                message = handle_excel_file(request.FILES['excel_file'])

        if request.POST:
            form = filterForm(request.Post)

            if form.is_valid():
                result = ProcessExcelExportTask.delay(form.cleaned_data['start_date'], form.cleaned_data['end_date'],
                                                      form.cleaned_data.get('cutoff', 30))
                return  HttpResponse(status=200)

    categories = ClassifierCategory.objects.all()
    departments = Department.objects.all()
    category_form = CategoryForm()

    form = filterForm()
    upload_form = ExcelUploadForm()

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
        form=form,
        upload_form=upload_form,
        departments=departments,
        categories=categories,
        category_form=category_form,
        )


def train(request, message_pk, category_pk):
    msg = ScoredMessage.objects.get(pk=message_pk)
    cat = ClassifierCategory.objects.get(pk=category_pk)
    classifier = FisherClassifier(getfeatures)
    msg.train(FisherClassifier, getfeatures, cat)
    return HttpResponse(cat.name)


def handle_download(start_date, end_date, cutoff=30):
    messages = Message.objects.filter(date__gte=start_date, date__lte=end_date)


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


