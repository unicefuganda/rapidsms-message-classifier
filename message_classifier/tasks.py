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

@task
def add(x, y):
    print("Executing task id %r, args: %r kwargs: %r" % (
        add.request.id, add.request.args, add.request.kwargs))


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
        rdb.set_trace()
        if file:
            excel = file.read()
            workbook = open_workbook(file_contents=excel)
            worksheet = workbook.sheet_by_index(0)

            if worksheet.nrows > 1:
                validated_numbers = []
                for row in range(1, worksheet.nrows):
                    pk, mobile, text, date, category, action = worksheet.cell(row, 0), worksheet.cell(row,
                        1), worksheet.cell(row,
                        2), worksheet.cell(
                        row, 3), worksheet.cell(row, 4), worksheet.cell(row, 5)
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
        self.handle_excel_file(file)


class UploadResponsesTask(Task):
    routing_key = 'ureport.poll_upload'
    name = "message_classifier.tasks.UploadResponsesTask"
    ignore_result = True
    def reprocess_responses(self,poll):
        for rc in ResponseCategory.objects.filter(category__poll=self, is_override=False):
            rc.delete()

        for resp in self.responses.all():
            resp.has_errors = False
            for category in self.categories.all():
                for rule in category.rules.all():
                    regex = re.compile(rule.regex, re.IGNORECASE)
                    if resp.eav.poll_text_value:
                        if regex.search(resp.eav.poll_text_value.lower()) and not resp.categories.filter(category=category).count():
                            if category.error_category:
                                resp.has_errors = True
                            rc = ResponseCategory.objects.create(response=resp, category=category)
                            break
            if not resp.categories.all().count() and self.categories.filter(default=True).count():
                if self.categories.get(default=True).error_category:
                    resp.has_errors = True
                resp.categories.add(ResponseCategory.objects.create(response=resp, category=self.categories.get(default=True)))
            resp.save()
    def handle_excel_file(self, file):
        if file:
            excel = file.read()
            workbook = open_workbook(file_contents=excel)
            worksheet = workbook.sheet_by_index(0)

            if worksheet.nrows > 1:
                validated_numbers = []
                for row in range(1, worksheet.nrows):
                    pk, mobile, text, category = worksheet.cell(row, 0), worksheet.cell(row, 1), worksheet.cell(row,
                        2), worksheet.cell(row, 3)


            else:
                info =\
                'You seem to have uploaded an empty excel file'
        else:
            info = 'Invalid file'
        return info



    def run(self, file, **kwargs):
        self.handle_excel_file(file)

#run every week
@periodic_task(run_every=datetime.timedelta(seconds=604800))
def generate_reprts():
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

#run everyday at 2:30
@periodic_task(run_every=crontab(hour=2, minute=30))
def classify_messages():
    classified_messages = ScoredMessage.objects.values_list('message')
    messages = Message.objects.exclude(pk__in=classified_messages)
    classifier = FisherClassifier(getfeatures)
    for message in messages:
        if len(message.text) > 30:
            sm, created = ScoredMessage.objects.get_or_create(message=message)
            sm.category = sm.classify(classifier, getfeatures)
            sm.save()


tasks.register(ProcessExcelExportTask)
tasks.register(HandleExcelClassification)
tasks.register(UploadResponsesTask)