from celery.task import Task
from celery.registry import tasks
from rapidsms_httprouter.models import Message
import os
from django.utils.datastructures import SortedDict
from uganda_common.utils import ExcelResponse

class ProcessExcelExportTask(Task):
   def run(self, start_date,end_date,cutoff, **kwargs):
        root_path=os.path.dirname(os.path.realpath(__file__))
        messages=Message.objects.filter(date__gte=start_date,date__lte=end_date)
        excel_file_path = os.path.join(os.path.join(os.path.join(root_path,'static'),'spreadsheets'),'%s.xls'%options['n'])
        messages=Message.objects.filter(direction="I").exclude(application="script").filter(date__gte=start).filter(date__lte=end)
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

class ClassifyMessagesTask(Task):
    def run(self):
        pass

class HandleExcelUpload(Task):
    def run(self):
        pass

class UploadResponsesTask(Task):
    def run(self):
        pass




