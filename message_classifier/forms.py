# -*- coding: utf-8 -*-
from datetime import datetime
from django import forms
from models import IbmCategory, IbmAction, IbmMsgCategory
from poll.models import Poll
from generic.forms import FilterForm, ActionForm
from tasks import message_export


class QueueForm(forms.Form):
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

    def queue_export(self, username, host, queryset):
        # import pdb; pdb.set_trace()
        name = self.cleaned_data['name']
        queryset = queryset.filter(msg__date__range=[self.cleaned_data['startdate'], self.cleaned_data['enddate']],
                                   score__gte=0.25)
        message_export.delay(name, queryset=queryset, username=username, host=host)


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
        return queryset.filter(category__category_id=pk).order_by('-score', 'msg__date')


class ChooseActionForm(FilterForm):
    ACTIONS = [("", "-----------")] + [(pk, name.capitalize()) for pk, name in
                                       list(IbmAction.objects.values_list('action_id', 'name').order_by('name'))]

    message_action = forms.ChoiceField(choices=ACTIONS)

    def filter(self, request, queryset):
        pk = self.cleaned_data['message_action']
        if not pk or pk == "":
            return queryset
        return queryset.filter(action__action_id=pk).order_by('-score', 'msg__date')


class AssignActionForm(ActionForm):
    ACTIONS = [(pk, name.capitalize()) for pk, name in
               list(IbmAction.objects.values_list('action_id', 'name').order_by('name'))]

    message_action = forms.ChoiceField(choices=ACTIONS)
    action_label = "Set Action to Selected Messages"

    def perform(self, request, results):
        action = IbmAction.objects.get(action_id=self.cleaned_data['message_action'])
        message_ids = set([m.msg_id for m in results])
        messages = IbmMsgCategory.objects.filter(msg__pk__in=message_ids)
        messages.update(action=action)
        return "Action '%s' was Successfully set on %d Messages" % (action.name.upper(), len(message_ids)), 'success'


class DeleteMessagesForm(ActionForm):
    action_label = "Delete Selected Messages"

    def perform(self, request, results):
        message_ids = set([m.msg_id for m in results])
        messages = IbmMsgCategory.objects.filter(msg__pk__in=message_ids)
        messages.delete()
        return "%d Messages were deleted" % len(message_ids), 'success'


class QueueAllForm(ActionForm):
    action_label = "Queue all Selected Messages For Download"

    def perform(self, request, results):
        message_ids = set([m.msg_id for m in results])
        messages = IbmMsgCategory.objects.filter(msg__pk__in=message_ids, score__gte=0.25)
        name = "%s_queued_by_%s" % (str(datetime.now()), request.user.username)
        message_export.delay(name.replace(" ", "_"), queryset=messages,
                             username=request.user.username, host=request.get_host())
        return "%d Messages have been queued for download, You'll be notified by email when download is ready" \
               % len(message_ids), "success"


class NewActionForm(forms.ModelForm):
    class Meta:
        model = IbmAction
        exclude = ('action_id', )