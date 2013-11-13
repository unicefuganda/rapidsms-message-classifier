import os
from celery.task import Task, task
from celery.registry import tasks
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.utils.datastructures import SortedDict
from xlrd import open_workbook
from poll.models import ResponseCategory, Response, Category
from uganda_common.utils import ExcelResponse
from ureport.settings import UREPORT_ROOT


@task
def message_export(name, **kwargs):
    excel_file_path = \
        os.path.join(os.path.join(os.path.join(UREPORT_ROOT,
                                               'static'), 'spreadsheets'),
                     '%s_queued.xlsx' % name.replace(" ", "_"))
    link = "/static/ureport/spreadsheets/%s_queued.xlsx" % name.replace(" ", "_")
    messages = kwargs.get('queryset')
    print messages
    messages_list = []

    for message in messages:
        msg_export_list = SortedDict()
        msg_export_list['Identifier'] = message.msg.connection.pk
        msg_export_list['Score'] = "%.2f" % message.score
        msg_export_list['Text'] = message.msg.text
        msg_export_list['Date'] = message.msg.date
        try:
            msg_export_list['Category'] = message.category.name
        except models.ObjectDoesNotExist:
            msg_export_list['Category'] = "N/A"
        except:
            msg_export_list['Action'] = "N/A"
        try:
            msg_export_list['Action'] = message.action.name
        except models.ObjectDoesNotExist:
            msg_export_list['Action'] = "N/A"
        except:
            msg_export_list['Action'] = "N/A"

        try:
            msg_export_list['Rating'] = message.msg.details.filter(attribute__name='rating')[0].value
        except IndexError:
            msg_export_list['Rating'] = "Unrated"
        messages_list.append(msg_export_list)
    ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)
    username = kwargs.get("username")
    host = kwargs.get("host")
    print username
    user = User.objects.get(username=username)
    if user.email:
        msg = "Hi %s,\nThe excel report that you requested to download is now ready for download. Please visit %s%s" \
              " and download it.\n\nThank You\nUreport Team" % (user.username, host, link)
        send_mail('Classified Message Queue Compete', msg, "", [user.email], fail_silently=False)


@task
def upload_responses(excel_file, poll):
    if excel_file:
        workbook = open_workbook(file_contents=excel_file)
        worksheet = workbook.sheet_by_index(0)
        if worksheet.nrows > 1:
            response_lst = []
            response_pks = []
            for row in range(1, worksheet.nrows):

                contact_pk, message_pk, category = worksheet.cell(row, 0).value, worksheet.cell(row,
                                                                                                1).value, worksheet.cell(
                    row,
                    14).value
                try:
                    res = Response.objects.get(message__pk=int(message_pk))
                    res.poll = poll
                    res.save()
                except Response.DoesNotExist:
                    continue
                response_pks.append(int(message_pk))
                try:
                    rc = ResponseCategory.objects.get(response__message__pk=int(message_pk))
                    rc.category = poll.categories.get(name=category.strip())
                    rc.save()
                except (ResponseCategory.DoesNotExist, Category.DoesNotExist):
                    continue

            responses = poll.responses.exclude(message__pk__in=response_pks).delete()
        poll.reprocess_responses()