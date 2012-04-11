from celery.task import Task,task
from celery.registry import tasks
from rapidsms_httprouter.models import Message
import os
from django.utils.datastructures import SortedDict
from uganda_common.utils import ExcelResponse
from .models import *
import logging
from celery.contrib import rdb
from xlrd import open_workbook
from .utils import *

@task
def add(x, y):
    print("Executing task id %r, args: %r kwargs: %r" % (
        add.request.id, add.request.args, add.request.kwargs))

class ProcessExcelExportTask(Task):
   routing_key = 'ureport.export'
   def run(self, start_date,end_date,cutoff,name,user, **kwargs):
        print("Executing task id %r, args: %r kwargs: %r" % (self.request.id, self.request.args, self.request.kwargs))
        root_path=os.path.dirname(os.path.realpath(__file__))
        messages=Message.objects.filter(date__gte=start_date,date__lte=end_date)
        excel_file_path = os.path.join(os.path.join(os.path.join(root_path,'static'),'spreadsheets'),'%s.zip'%name)
        link="/static/message_classifier/spreadsheets/"+name+".zip"
        Report.objects.create(title=name,user=user,link=link)
        messages=Message.objects.filter(direction="I").exclude(application="script").filter(date__range=(start_date,end_date))
        messages_list=[]
        for message in messages:
            if len(message)>cutoff:
                msg_export_list=SortedDict()
                msg_export_list['pk'] =message.pk
                msg_export_list['mobile'] =message.connection.identity
                msg_export_list['text'] =message.text
                msg_export_list['category'] =''
                messages_list.append(msg_export_list)
        ExcelResponse(messages_list,output_name=excel_file_path,write_to_file=True)


tasks.register(ProcessExcelExportTask)

class GenerateReportsTask(Task):
    routing_key = 'ureport.report'

    def run(self):
        root_path=os.path.dirname(os.path.realpath(__file__))
        categories=ClassifierCategory.objects.all()

        for category in categories:
            excel_file_path = os.path.join(os.path.join(os.path.join(root_path,'static'),'spreadsheets'),'%s.zip'%category.name)
            messages_list=[]
            messages=ScoredMessage.objects.filter(category=category)
            for message in messages:

                msg_export_list=SortedDict()
                msg_export_list['pk'] =message.pk
                msg_export_list['mobile'] =message.connection.identity
                msg_export_list['text'] =message.text
                msg_export_list['category'] =message.category.name
                messages_list.append(msg_export_list)
            ExcelResponse(messages_list,output_name=excel_file_path,write_to_file=True)


class ClassifyMessagesTask(Task):
    routing_key = 'ureport.classify'

    def run(self):
        classified_messages=ScoredMessage.objects.values_list('message')
        messages=Message.objects.exclude(pk__in=classified_messages)
        classifier = FisherClassifier(getfeatures)
        for message in messages:
            sm, created = ScoredMessage.objects.get_or_create(message=message)
            sm.category=sm.classify(classifier,getfeatures)
            sm.save()




class HandleExcelUpload(Task):
    routing_key = 'ureport.upload'
    def handle_excel_file(self,file):
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
                    message = Message.objects.get(pk=pk)
                    cat, created = ClassifierCategory.objects.get_or_create(name=category)

                    sm, created = ScoredMessage.objects.get_or_create(message=message)
                    sm.trained_as = cat
                    sm.category=cat
                    sm.save()
                    classifier = FisherClassifier(getfeatures)
                    sm.train(FisherClassifier, getfeatures, cat)


            else:
                info =\
                'You seem to have uploaded an empty excel file'
        else:
            info = 'Invalid file'
        return info

    def run(self,file,**kwargs):
        pass


    
class UploadResponsesTask(Task):
    routing_key = 'ureport.poll_upload'
    def handle_excel_file(self,file):
        if file:
            excel = file.read()
            workbook = open_workbook(file_contents=excel)
            worksheet = workbook.sheet_by_index(0)

            if worksheet.nrows > 1:
                validated_numbers = []
                for row in range(1, worksheet.nrows):
                    pk, mobile, text, category = worksheet.cell(row, 0), worksheet.cell(row, 1), worksheet.cell(row,2), worksheet.cell(row, 3)
                    

            else:
                info =\
                'You seem to have uploaded an empty excel file'
        else:
            info = 'Invalid file'
        return info

    
    def run(self,file,**kwargs):
        pass




