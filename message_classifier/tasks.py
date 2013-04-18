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
        try:
            msg_export_list['Action'] = message.action.name
        except models.ObjectDoesNotExist:
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


# @task
# def classify_excel(excel_file):
#     if excel_file:
#         workbook = open_workbook(file_contents=excel_file)
#         worksheet = workbook.sheet_by_index(0)
#         alive,created=Department.objects.get_or_create(name="alive")
#         safe,created=Department.objects.get_or_create(name="safe")
#         learning,created=Department.objects.get_or_create(name="learning")
#         social_policy,created=Department.objects.get_or_create(name="social policy")
#         other,created=Department.objects.get_or_create(name="other")
#         categories={
#             'alive':['water','health'],
#             'safe':['Orphans & Vulnerable Children','Violence Against Children'],
#             'learning':['employment','education'],
#             'social_policy':['social policy'],
#             'other':['ureport','irrerevant','poll','family & relationships','emergency','energy']
#
#
#         }
#
#         if worksheet.nrows > 1:
#             validated_numbers = []
#             for row in range(1, worksheet.nrows):
#                 pk, mobile, text, date, category, action = worksheet.cell(row, 0).value, worksheet.cell(row,
#                     1).value, worksheet.cell(row,
#                     2).value, worksheet.cell(
#                     row, 3).value, worksheet.cell(row, 4).value, worksheet.cell(row, 5).value
#                 try:
#                     message = Message.objects.get(pk=int(pk))
#                 except:
#                     continue
#                 if category.lower() in categories['other']:
#                     department=other
#                 elif category.lower() in categories['social_policy']:
#                     department=social_policy
#                 elif category.lower() in categories['learning']:
#                     department=learning
#                 elif category.lower() in categories['alive']:
#                     department=alive
#                 elif category.lower() in categories['safe']:
#                     department=safe
#                 else:
#                     department=None
#                 try:
#                     cat = ClassifierCategory.objects.get(name__icontains=category)
#                 except:
#                     cat= ClassifierCategory.objects.create(name=category)
#                 if department:
#                     cat.department=department
#                     cat.save()
#
#
#                 sm, created = ScoredMessage.objects.get_or_create(message=message)
#                 sm.trained_as = cat
#                 sm.category = cat
#                 sm.action=action
#                 sm.save()
#                 classifier = FisherClassifier(getfeatures)
#                 sm.train(FisherClassifier, getfeatures, cat)
#
#
#         else:
#             info =\
#             'You seem to have uploaded an empty excel file'
#     else:
#         info = 'Invalid file'
#         return info


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


# #run every sunday at 2:30 am
# @periodic_task(run_every=crontab(hour=2, minute=30, day_of_week=0))
# def generate_reports():
#     root_path = os.path.dirname(os.path.realpath(__file__))
#     categories = ClassifierCategory.objects.all()
#     departments=Department.objects.all()
#     for department in departments:
#         excel_file_path = os.path.join(os.path.join(os.path.join(root_path, 'static'), 'spreadsheets'),
#             '%s.zip' % department.name)
#         messages_list = []
#         messages = ScoredMessage.objects.filter(category__department=department)
#         for sm in messages:
#             msg_export_list = SortedDict()
#             msg_export_list['pk'] = sm.message.pk
#             msg_export_list['mobile'] = sm.message.connection.identity
#             msg_export_list['text'] = sm.message.text
#             msg_export_list['category'] = sm.category.name
#             messages_list.append(msg_export_list)
#         if len(messages_list):
#             ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)
#
#
#     for category in categories:
#         excel_file_path = os.path.join(os.path.join(os.path.join(root_path, 'static'), 'spreadsheets'),
#             '%s.zip' % category.slug)
#         messages_list = []
#         messages = ScoredMessage.objects.filter(category=category)
#         for sm in messages:
#             msg_export_list = SortedDict()
#             msg_export_list['pk'] = sm.message.pk
#             msg_export_list['mobile'] = sm.message.connection.identity
#             msg_export_list['text'] = sm.message.text
#             msg_export_list['category'] = sm.category.name
#             messages_list.append(msg_export_list)
#         ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)
#
#
# #run eve
# @periodic_task(run_every=crontab(hour=23, minute=30, day_of_week='*'))
# def classify_messages():
#     classified_messages = ScoredMessage.objects.filter(trained_as=None).values_list('message')
#     messages = Message.objects.exclude(pk__in=classified_messages).filter(direction="I")
#     classifier = FisherClassifier(getfeatures)
#     for message in messages:
#         if len(message.text) > 30:
#             sm, created = ScoredMessage.objects.get_or_create(message=message)
#             sm.category = sm.classify(FisherClassifier, getfeatures)
#             sm.save()
#
# @periodic_task(run_every=crontab(hour=12, minute=30, day_of_week='*'))
# def reclassify_all():
#     classified_messages = ScoredMessage.objects.filter(trained_as=None).values_list('message')
#     messages = Message.objects.filter(pk__in=classified_messages)
#     classifier = FisherClassifier(getfeatures)
#     for message in messages:
#         if len(message.text) > 30:
#             sm, created = ScoredMessage.objects.get_or_create(message=message)
#             sm.category = sm.classify(FisherClassifier, getfeatures)
#             sm.save()
# @task
# def reclassify():
#     classified_messages = ScoredMessage.objects.values_list('message')
#     messages = Message.objects.filter(pk__in=classified_messages)
#     classifier = FisherClassifier(getfeatures)
#     for message in messages:
#         if len(message.text) > 30:
#             sm, created = ScoredMessage.objects.get_or_create(message=message)
#             sm.category = sm.classify(FisherClassifier, getfeatures)
#             sm.save()
