#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.shortcuts import HttpResponse
from forms import ChooseCategoryForm, AssignActionForm, ChooseActionForm, DeleteMessagesForm, QueueForm, QueueAllForm, \
    NewActionForm
from generic.views import generic
from generic.sorters import SimpleSorter
from django.contrib.auth.decorators import login_required
from ureport.views.utils.paginator import ureport_paginate
from models import IbmMsgCategory, IbmAction
from ureport.forms import PushToMtracForm


@login_required
def message_classification(request):
    queryset = IbmMsgCategory.objects.filter(msg__direction='I', score__gte=0.25)
    filter_forms = [ChooseCategoryForm, ChooseActionForm]
    FILTER_REQUEST_KEY = "%s_filter_request" % request.path
    if request.method == "POST" and 'startdate' in request.POST:
        filter_request_post = request.session.setdefault(FILTER_REQUEST_KEY, None)
        if filter_request_post:
            for form_class in filter_forms:
                form_instance = form_class(filter_request_post, request=request)
                if form_instance.is_valid():
                    queryset = form_instance.filter(request, queryset)
        queue_form = QueueForm(request.POST)
        if queue_form.is_valid():
            queue_form.queue_export(request.user.username, request.get_host(), queryset)
            return HttpResponse("All is good... You will receive an email when export is ready")

    msg_form = QueueForm()
    action_form = NewActionForm

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
        queryset=queryset,
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
        action_form=action_form,
        ibm_actions=IbmAction.objects.all(),
        filter_forms=filter_forms,
        action_forms=[PushToMtracForm, QueueAllForm, AssignActionForm]
    )
