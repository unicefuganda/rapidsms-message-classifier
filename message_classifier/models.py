from django.db import models
from  rapidsms_httprouter.models import Message
from .utils import *

class FeatureCount(models.Model):
    """ bayesian filter  training storage used to score new messages. """
    feature = models.CharField( max_length=100)
    category = models.CharField( max_length=100)
    count = models.IntegerField(default=0, null=False)


class CategoryCount(models.Model):
    #storage of different probabilities
    name = models.CharField(max_length=100)
    count = models.IntegerField(default=0, null=False)


class ScoredMessage(Message):
    score = models.FloatField(blank=True, null=True)
    trained_as = models.CharField(max_length=4, blank=True, null=True)

    def classify(self,classifier,get_features):
        cl=classifier(get_features)
        return cl.classify(self.text)

    def train(self,classifier,get_features,category):
        cl=classifier(get_features)
        return cl.train(self.text,category)







