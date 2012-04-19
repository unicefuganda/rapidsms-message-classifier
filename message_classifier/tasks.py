from celery.task import Task, task
from celery.registry import tasks
from rapidsms_httprouter.models import Message
from celery.task import PeriodicTask
import os
from django.utils.datastructures import SortedDict
from uganda_common.utils import ExcelResponse
from .models import *
import logging
from celery.contrib import rdb
from xlrd import open_workbook
from .utils import *
import datetime
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from poll.models import ResponseCategory,Poll,Response



class ProcessExcelExportTask(Task):
    #name = "message_classifier.tasks.ProcessExcelExportTask"
    routing_key = 'ureport.export'
    #ignore_result = True

    def run(self, start_date, end_date, cutoff, name, user, **kwargs):


        root_path = os.path.dirname(os.path.realpath(__file__))
        messages = Message.objects.filter(date__gte=start_date, date__lte=end_date)
        excel_file_path = os.path.join(os.path.join(os.path.join(root_path, 'static'), 'spreadsheets'), '%s.zip' % name)
        link = "/static/message_classifier/spreadsheets/" + name + ".zip"
        Report.objects.create(title=name, user=user, link=link)
        messages = Message.objects.filter(direction="I").exclude(application="script").filter(
            date__range=(start_date, end_date))
        messages_list = []
        for message in messages:
            if len(message.text) > cutoff:
                msg_export_list = SortedDict()
                msg_export_list['pk'] = message.pk
                msg_export_list['mobile'] = message.connection.identity
                msg_export_list['text'] = message.text
                msg_export_list['category'] = ''
                messages_list.append(msg_export_list)
        ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)



class HandleExcelClassification(Task):
    routing_key = 'ureport.upload'
    name = "message_classifier.tasks.HandleExcelClassification"
    ignore_result = True

    def handle_excel_file(self, file):

        if file:

            workbook = open_workbook(file_contents=file)
            worksheet = workbook.sheet_by_index(0)

            if worksheet.nrows > 1:
                validated_numbers = []
                for row in range(1, worksheet.nrows):
                    pk, mobile, text, date, category, action = worksheet.cell(row, 0).value, worksheet.cell(row,
                        1).value, worksheet.cell(row,
                        2).value, worksheet.cell(
                        row, 3).value, worksheet.cell(row, 4).value, worksheet.cell(row, 5).value
                    message = Message.objects.get(pk=pk)
                    cat, created = ClassifierCategory.objects.get_or_create(name=category)

                    sm, created = ScoredMessage.objects.get_or_create(message=message)
                    sm.trained_as = cat
                    sm.category = cat
                    sm.save()
                    classifier = FisherClassifier(getfeatures)
                    sm.train(FisherClassifier, getfeatures, cat)


            else:
                info =\
                'You seem to have uploaded an empty excel file'
        else:
            info = 'Invalid file'
        return info

    def run(self, file, **kwargs):
        print("Executing task id %r, args: %r kwargs: %r" % (
                self.request.id, self.request.args, self.request.kwargs))

        self.handle_excel_file(file)


class UploadResponsesTask(Task):
    routing_key = 'ureport.poll_upload'
    name = "message_classifier.tasks.UploadResponsesTask"
    ignore_result = True


    def handle_excel_file(self, file,poll):
        if file:

            workbook = open_workbook(file_contents=file)
            worksheet = workbook.sheet_by_index(0)

            if worksheet.nrows > 1:
                response_lst = []
                response_pks=[]
                for row in range(1, worksheet.nrows):
                    contact_pk,message_pk,  category = worksheet.cell(row, 0).value, worksheet.cell(row, 1).value, worksheet.cell(row,
                        12).value
                    rc=ResponseCategory.objects.get(response__message__pk=int(message_pk.strip()))
                    rc.category=poll.categories.get(name=category.strip())
                    rc.save()
                    response_pks.append(message_pk.strip())
                responses=poll.responses.exclude(message__pk__in=response_pks).delete()

            else:
                info =\
                'You seem to have uploaded an empty excel file'
        else:
            info = 'Invalid file'
        return info



    def run(self, file,poll, **kwargs):
        self.handle_excel_file(file)
        for rc in ResponseCategory.objects.filter(category__poll=poll):
            rc.delete()



#run every sunday at 2:30 am
@periodic_task(run_every=crontab(hour=2, minute=30, day_of_week=0))
def generate_reports():
    root_path = os.path.dirname(os.path.realpath(__file__))
    categories = ClassifierCategory.objects.all()

    for category in categories:
        excel_file_path = os.path.join(os.path.join(os.path.join(root_path, 'static'), 'spreadsheets'),
            '%s.zip' % category.name)
        messages_list = []
        messages = ScoredMessage.objects.filter(category=category)
        for message in messages:
            msg_export_list = SortedDict()
            msg_export_list['pk'] = message.pk
            msg_export_list['mobile'] = message.connection.identity
            msg_export_list['text'] = message.text
            msg_export_list['category'] = message.category.name
            messages_list.append(msg_export_list)
        ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)

#run eve
@periodic_task(run_every=crontab(hour=4, minute=30, day_of_week='*'))
def classify_messages():
    classified_messages = ScoredMessage.objects.values_list('message')
    messages = Message.objects.exclude(pk__in=classified_messages)
    classifier = FisherClassifier(getfeatures)
    for message in messages:
        if len(message.text) > 30:
            sm, created = ScoredMessage.objects.get_or_create(message=message)
            sm.category = sm.classify(FisherClassifier, getfeatures)
            sm.save()


tasks.register(ProcessExcelExportTask)
tasks.register(HandleExcelClassification)
tasks.register(UploadResponsesTask)