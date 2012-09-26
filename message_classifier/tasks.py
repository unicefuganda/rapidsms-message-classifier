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
from poll.models import ResponseCategory, Poll, Response,Category


def create_tags(message):
    pass
@task
def message_export(start_date, end_date, cutoff, name, user,contains, **kwargs):
    root_path = os.path.dirname(os.path.realpath(__file__))
    excel_file_path = os.path.join(os.path.join(os.path.join(root_path, 'static'), 'spreadsheets'), '%s.zip' % name)
    link = "/static/message_classifier/spreadsheets/" + name + ".zip"
    Report.objects.create(title=name, user=user, link=link)
    messages = Message.objects.filter(direction="I").exclude(application="script").filter(
        date__range=(start_date, end_date))
    if contains:
        or_searches=contains.split('or')
        search_reg="|".join(or_searches)
        messages=messages.filter(text__iregex=".*\m(%s)\y.*"%search_reg).distinct()
    messages_list = []
    for message in messages:
        if cutoff and len(message.text) > cutoff:
            pass
        else:
            msg_export_list = SortedDict()
            msg_export_list['pk'] = message.pk
            msg_export_list['mobile'] = message.connection.identity
            msg_export_list['text'] = message.text
            msg_export_list['date'] = message.date.date()
            msg_export_list['category'] = ''
            messages_list.append(msg_export_list)
    ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)


@task
def classify_excel(excel_file):
    if excel_file:
        workbook = open_workbook(file_contents=excel_file)
        worksheet = workbook.sheet_by_index(0)
        alive,created=Department.objects.get_or_create(name="alive")
        safe,created=Department.objects.get_or_create(name="safe")
        learning,created=Department.objects.get_or_create(name="learning")
        social_policy,created=Department.objects.get_or_create(name="social policy")
        other,created=Department.objects.get_or_create(name="other")
        categories={
            'alive':['water','health'],
            'safe':['Orphans & Vulnerable Children','Violence Against Children'],
            'learning':['employment','education'],
            'social_policy':['social policy'],
            'other':['ureport','irrerevant','poll','family & relationships','emergency','energy']


        }

        if worksheet.nrows > 1:
            validated_numbers = []
            for row in range(1, worksheet.nrows):
                pk, mobile, text, date, category, action = worksheet.cell(row, 0).value, worksheet.cell(row,
                    1).value, worksheet.cell(row,
                    2).value, worksheet.cell(
                    row, 3).value, worksheet.cell(row, 4).value, worksheet.cell(row, 5).value
                try:
                    message = Message.objects.get(pk=int(pk))
                except:
                    continue
                if category.lower() in categories['other']:
                    department=other
                elif category.lower() in categories['social_policy']:
                    department=social_policy
                elif category.lower() in categories['learning']:
                    department=learning
                elif category.lower() in categories['alive']:
                    department=alive
                elif category.lower() in categories['safe']:
                    department=safe
                else:
                    department=None
                try:
                    cat = ClassifierCategory.objects.get(name__icontains=category)
                except:
                    cat= ClassifierCategory.objects.create(name=category)
                if department:
                    cat.department=department
                    cat.save()


                sm, created = ScoredMessage.objects.get_or_create(message=message)
                sm.trained_as = cat
                sm.category = cat
                sm.action=action
                sm.save()
                classifier = FisherClassifier(getfeatures)
                sm.train(FisherClassifier, getfeatures, cat)


        else:
            info =\
            'You seem to have uploaded an empty excel file'
    else:
        info = 'Invalid file'
        return info


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
                    1).value, worksheet.cell(row,
                    14).value
                try:
                    res=Response.objects.get(message__pk=int(message_pk))
                    res.poll=poll
                    res.save()
                except Response.DoesNotExist:
                    continue
                response_pks.append(int(message_pk))
                try:
                    rc = ResponseCategory.objects.get(response__message__pk=int(message_pk))
                    rc.category = poll.categories.get(name=category.strip())
                    rc.save()
                except (ResponseCategory.DoesNotExist,Category.DoesNotExist):
                    continue

            responses = poll.responses.exclude(message__pk__in=response_pks).delete()
        poll.reprocess_responses()




#run every sunday at 2:30 am
@periodic_task(run_every=crontab(hour=2, minute=30, day_of_week=0))
def generate_reports():
    root_path = os.path.dirname(os.path.realpath(__file__))
    categories = ClassifierCategory.objects.all()
    departments=Department.objects.all()
    for department in departments:
        excel_file_path = os.path.join(os.path.join(os.path.join(root_path, 'static'), 'spreadsheets'),
            '%s.zip' % department.name)
        messages_list = []
        messages = ScoredMessage.objects.filter(category__department=department)
        for sm in messages:
            msg_export_list = SortedDict()
            msg_export_list['pk'] = sm.message.pk
            msg_export_list['mobile'] = sm.message.connection.identity
            msg_export_list['text'] = sm.message.text
            msg_export_list['category'] = sm.category.name
            messages_list.append(msg_export_list)
        if len(messages_list):
            ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)


    for category in categories:
        excel_file_path = os.path.join(os.path.join(os.path.join(root_path, 'static'), 'spreadsheets'),
            '%s.zip' % category.slug)
        messages_list = []
        messages = ScoredMessage.objects.filter(category=category)
        for sm in messages:
            msg_export_list = SortedDict()
            msg_export_list['pk'] = sm.message.pk
            msg_export_list['mobile'] = sm.message.connection.identity
            msg_export_list['text'] = sm.message.text
            msg_export_list['category'] = sm.category.name
            messages_list.append(msg_export_list)
        ExcelResponse(messages_list, output_name=excel_file_path, write_to_file=True)


#run eve
@periodic_task(run_every=crontab(hour=23, minute=30, day_of_week='*'))
def classify_messages():
    classified_messages = ScoredMessage.objects.filter(trained_as=None).values_list('message')
    messages = Message.objects.exclude(pk__in=classified_messages).filter(direction="I")
    classifier = FisherClassifier(getfeatures)
    for message in messages:
        if len(message.text) > 30:
            sm, created = ScoredMessage.objects.get_or_create(message=message)
            sm.category = sm.classify(FisherClassifier, getfeatures)
            sm.save()

@periodic_task(run_every=crontab(hour=12, minute=30, day_of_week='*'))
def reclassify_all():
    classified_messages = ScoredMessage.objects.filter(trained_as=None).values_list('message')
    messages = Message.objects.filter(pk__in=classified_messages)
    classifier = FisherClassifier(getfeatures)
    for message in messages:
        if len(message.text) > 30:
            sm, created = ScoredMessage.objects.get_or_create(message=message)
            sm.category = sm.classify(FisherClassifier, getfeatures)
            sm.save()
@task
def reclassify():
    classified_messages = ScoredMessage.objects.values_list('message')
    messages = Message.objects.filter(pk__in=classified_messages)
    classifier = FisherClassifier(getfeatures)
    for message in messages:
        if len(message.text) > 30:
            sm, created = ScoredMessage.objects.get_or_create(message=message)
            sm.category = sm.classify(FisherClassifier, getfeatures)
            sm.save()
