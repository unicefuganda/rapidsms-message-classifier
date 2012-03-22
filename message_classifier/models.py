from django.db import models
from  rapidsms_httprouter.models import Message


class ClassifierFeature(models.Model):
    feature = models.CharField( max_length=100,db_index=True)
    category = models.ForeignKey('ClassifierCategory')
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


class ScoredMessage(models.Model):
    score = models.FloatField(blank=True, null=True)
    trained_as = models.CharField(max_length=4, blank=True, null=True)
    message=models.ForeignKey(Message)

    def classify(self,classifier,get_features):
        cl=classifier(get_features)
        return cl.classify(self.text)

    def train(self,classifier,get_features,category):
        cl=classifier(get_features)
        return cl.train(self.text,category)







