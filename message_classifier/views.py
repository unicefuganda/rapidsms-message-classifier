#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import HttpResponse
from forms import ExcelUploadForm, PollUploadForm, filterForm, ChooseCategoryForm, AssignActionForm, ChooseActionForm, \
    DeleteMessagesForm
from generic.views import generic
from generic.sorters import SimpleSorter
from django.contrib.auth.decorators import login_required
from ureport.views.utils.paginator import ureport_paginate
from models import IbmMsgCategory


@login_required
def message_classification(request):
    if request.method == "POST" and not request.is_ajax():

        if request.FILES:
            upload_form = ExcelUploadForm(request.FILES)
            poll_form = PollUploadForm(request.POST, request.FILES)

            if upload_form.is_valid():
                if request.FILES.get('excel_file'):
                    # excel = request.FILES['excel_file'].read()

                    # message = classify_excel.delay(excel)
                    # print message
                    return HttpResponse("successfully uploaded file")
            if poll_form.is_valid():
                if request.FILES.get('excel'):
                    # excel = request.FILES['excel'].read()
                    # poll = poll_form.cleaned_data['poll']
                    # message = upload_responses.delay(excel, poll)
                    # print message
                    return HttpResponse("successfully uploaded file")

        if request.POST:

            msg_form = filterForm(request.POST)

            if msg_form.is_valid():
                # message_export.delay(msg_form.cleaned_data['startdate'], msg_form.cleaned_data['enddate'],
                #                      msg_form.cleaned_data.get('size', None), msg_form.cleaned_data['name'],
                #                      request.user, msg_form.cleaned_data.get('contains', None))
                return HttpResponse(status=200)

    msg_form = filterForm()
    upload_form = ExcelUploadForm()

    columns = [('Identifier', True, 'message__connection_id', SimpleSorter()),
               ('Text', True, 'msg__text', SimpleSorter()),
               ('Date', True, 'msg__date', SimpleSorter()),
               ('Score', True, 'score', SimpleSorter()),
               ('Category', True, 'category', SimpleSorter(),),
               ('Action', True, 'action', SimpleSorter(),),
               ('Rating', False, '', None)]

    return generic(
        request,
        model=IbmMsgCategory,
        queryset=IbmMsgCategory.objects.filter(msg__direction='I'),
        objects_per_page=20,
        results_title='Classified Messages',
        partial_row='message_classifier/message_row.html',
        base_template='message_classifier/message_classifier_base.html',
        paginator_template='ureport/partials/new_pagination.html',
        paginator_func=ureport_paginate,
        columns=columns,
        sort_column='score',
        sort_ascending=False,
        msg_form=msg_form,
        upload_form=upload_form,
        filter_forms=[ChooseCategoryForm, ChooseActionForm],
        action_forms=[AssignActionForm, DeleteMessagesForm]
    )
