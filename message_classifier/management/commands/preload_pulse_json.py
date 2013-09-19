import json
import datetime
from django.core.management import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from message_classifier.models import IbmMsgCategory, IbmCategory
from rapidsms.contrib.locations.models import Location
from ureport.settings import UREPORT_ROOT

__author__ = 'kenneth'


class Command(BaseCommand):
    def handle(self, **options):
        print "Starting to preload the json"
        self.gen_json()
        print "General Json Preloaded"
        self.gen_json(period='day')
        print "Daily Json Preloaded"
        self.gen_json(period='month')
        print "Monthly json Preloaded"

    def gen_json(self, period=None):
        print "Getting locations"
        l = [l.pk for l in Location.objects.filter(type='district').distinct()]
        period_map = {'day': 1, 'month': 30, 'year': 365}
        file_name = "all_data.json"
        _all = IbmMsgCategory.objects.filter(score__gte=0.5,
                                             msg__connection__contact__reporting_location__in=l).values_list('pk',
                                                                                                             flat=True)
        if period:
            now = datetime.datetime.now()
            previous_date = datetime.datetime.now() - datetime.timedelta(days=period_map[period])
            file_name = "%s_data.json" % period
            _all = _all.filter(msg__date__range=[previous_date, now])
        print "Making the giant query at", datetime.datetime.now()
        s = IbmCategory.objects.filter(ibmmsgcategory__in=_all).exclude(
            name__in=['family & relationships', "energy", "u-report", "social policy", "employment"]).annotate(
            total=Count('ibmmsgcategory_set')).values('total', 'name',
                                                       'ibmmsgcategory__msg__connection__contact__reporting_location__name')
        data = json.dumps(list(s), cls=DjangoJSONEncoder)
        data.replace('"ibmmsgcategory__msg__connection__contact__reporting_location__name"', "\"district\"").replace(
            "\"name\"", "\"category\"")
        f = open('%s/static/data/%s' % (UREPORT_ROOT, file_name), 'w')
        f.write(data)
        f.close()
        print "File written to", '%s/static/data/%s' % (UREPORT_ROOT, file_name), "at", datetime.datetime.now()