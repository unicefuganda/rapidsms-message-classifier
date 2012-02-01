from django.db import models
from  rapidsms_httprouter.models import Message

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






