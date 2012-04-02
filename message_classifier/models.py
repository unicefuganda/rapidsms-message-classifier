from django.contrib.auth.models import User
from django.db import models
from  rapidsms_httprouter.models import Message
from contact.models import Flag


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
    department=models.ForeignKey("Department")
    flags=models.ManyToManyField(Flag,null=True)

    def __unicode__(self):
        return self.name


class ScoredMessage(models.Model):
    score = models.FloatField(blank=True, null=True)
    trained_as = models.ForeignKey(ClassifierCategory,null=True)
    message=models.ForeignKey(Message)
    action=models.CharField(max_length=15,choices=(("inform","inform"),("action","action"),("no response","no response"),))

    def classify(self,classifier,get_features):
        cl=classifier(get_features)
        return cl.classify(self.message.text)

    def train(self,classifier,get_features,category):
        cl=classifier(get_features)
        return cl.train(self.message.text,category)

class Reports(models.Model):
    user=models.ForeignKey(User)
    title=models.CharField(max_length=30)
    link=models.CharField(max_length=50)
    date=models.DateTimeField(auto_now=True)

class Department(models.Model):
    name=models.CharField(max_length=50)
    def categories(self):
        return ClassifierCategory.objects.filter(department=self)

    def __unicode__(self):
        return self.name












