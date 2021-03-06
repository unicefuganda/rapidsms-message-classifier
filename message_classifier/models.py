from django.db import models
from  rapidsms_httprouter.models import Message
from django.conf import settings
from django.utils.translation import ugettext as _


class IbmCategory(models.Model):
    category_id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None):
        raise NotImplementedError("Please don't try to write stuff to this table... Ok?")

    class Meta:
        managed = getattr(settings, 'IBM_TABLES_MANAGED', False)
        db_table = 'ibm_category'
        app_label = 'message_classifier'


class IbmAction(models.Model):
    action_id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=50, verbose_name=_("Name"))

    def __unicode__(self):
        return self.name

    class Meta:
        managed = getattr(settings, 'IBM_TABLES_MANAGED', False)
        db_table = 'ibm_action'
        app_label = 'message_classifier'


class IbmMsgCategory(models.Model):
    msg = models.ForeignKey(Message, primary_key=True)
    category = models.ForeignKey(IbmCategory)
    score = models.FloatField()
    action = models.ForeignKey(IbmAction, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        msg = self.msg.text
        if len(msg) > 40:
            msg = msg[:37] + "..."
        return msg + " | " + self.category.name

    class Meta:
        managed = getattr(settings, 'IBM_TABLES_MANAGED', False)
        db_table = 'ibm_msg_category'
        app_label = 'message_classifier'
        ordering = ['score', '-msg__date']