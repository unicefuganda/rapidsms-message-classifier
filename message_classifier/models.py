from django.db import models
from  rapidsms_httprouter.models import Message
from .utils import *

class ClassifierFeature(models.Model):
    feature = models.CharField( max_length=100,db_index=True)
    category = models.ForeignKey(ClassifierCategory)
    count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.feature


class ClassifierCategory(models.Model):

    name = models.CharField(max_length=100,primary_key=True)
    count = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name


class ScoredMessage(Message):
    score = models.FloatField(blank=True, null=True)
    trained_as = models.CharField(max_length=4, blank=True, null=True)

    def classify(self,classifier,get_features):
        cl=classifier(get_features)
        return cl.classify(self.text)

    def train(self,classifier,get_features,category):
        cl=classifier(get_features)
        return cl.train(self.text,category)







