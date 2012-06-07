import re
import math
from message_classifier.models import * #ClassifierFeature,ClassifierCategory,ScoredMessage
from django.db.models import F
from django.db.models import Sum
from nltk.corpus import stopwords
from django.db import transaction
from .settings import *
from nltk import bigrams,trigrams


def ngrams(message,n):
    regex=re.compile('\\W*')
    words=regex.split(message)
    if n==1:
        return words
    elif n == 2:
        return [a +" "+b for a,b in bigrams(words)]
    elif n== 3:
        return [a +" "+b+" "+c for a,b,c in trigrams(words)]
    else:
        return []

def getfeatures(message):
    regex=re.compile('\\W*')
    stop_words = stopwords.words('english')+STOP_WORDS
    # Split the words by non-alpha characters
    words=[s.lower() for s in regex.split(message)
          if not s in stop_words]
    #use the message sender as a feature
    #words.append(message.connection)

    # Return the unique set of words only
    words=words+ngrams(message,2)+ngrams(message,3)
    return dict([(w,1) for w in words])


class Classifier(object):

    def __init__(self,getfeatures):
        # Counts of feature/category combinations
        self.fc={}
        # Counts of messages in each category
        self.cc={}
        self.getfeatures=getfeatures


    def increment_feature(self,feature,cat):
       

        class_feature,created = ClassifierFeature.objects.get_or_create(category=cat,feature=feature)
        ClassifierFeature.objects.filter(category=cat,feature=feature).update(count=F('count') + 1)


    def feature_count(self,feature,cat):
        fc,created= ClassifierFeature.objects.get_or_create(feature=feature,category=cat)
        return float(fc.count)


    def increment_catcount(self,cat):
        classifiercat,created=ClassifierCategory.objects.get_or_create(name=cat)
        ClassifierCategory.objects.filter(name=cat).update(count=F('count') + 1)


    def catcount(self,cat):
        cc,created=ClassifierCategory.objects.get_or_create(name=cat)
        return float(cc.count)

    def categories(self):
        return ClassifierCategory.objects.all().distinct()
       

    def totalcount(self):
    
        total=ClassifierCategory.objects.aggregate(Sum("count"))
        return total.get("count__sum",0)

    def train(self,item,cat):
        features=self.getfeatures(item)
        # Increment the count for every feature with this category
        for feature in features:
            self.increment_feature(feature,cat)

        # Increment the count for this category
        self.increment_catcount(cat)


    def feature_prob(self,feature,cat):
        if self.catcount(cat)==0: return 0

        # The total number of times this feature appeared in this
        # category divided by the total number of items in this category
        return self.feature_count(feature,cat)/self.catcount(cat)

    def weightedprob(self,feature,cat,prf,weight=1.0,ap=0.5):
        # Calculate current probability
        basicprob=prf(feature,cat)

        # Count the number of times this feature has appeared in
        # all categories
        totals=sum([self.feature_count(feature,cat) for cat in self.categories()])

        # Calculate the weighted average
        bp=((weight*ap)+(totals*basicprob))/(weight+totals)
        return bp

class FisherClassifier(Classifier):
    
    def cprob(self,feature,cat):
        # The frequency of this feature in this category
        clf=self.feature_prob(feature,cat)
        if clf==0: return 0

        # The frequency of this feature in all the categories
        freqsum=sum([self.feature_prob(feature,cat) for cat in self.categories()])

        # The probability is the frequency in this category divided by
        # the overall frequency
        p=clf/(freqsum)

        return p

    def fisherprob(self,message,cat):
        # Multiply all the probabilities together
        p=1
        features=self.getfeatures(message)
        for feature in features:
            p*=(self.weightedprob(feature,cat,self.cprob))

        # Take the natural log and multiply by -2
        fscore=-2*math.log(p)

        # Use the inverse chi2 function to get a probability
        return self.invchi2(fscore,len(features)*2)

    def invchi2(self,chi, df):
        m = chi / 2.0
        sum = term = math.exp(-m)
        for i in range(1, df//2):
            term *= m / i
            sum += term
        return min(sum, 1.0)

    def __init__(self,getfeatures):
        Classifier.__init__(self,getfeatures)
        self.minimums={}

    def setminimum(self,cat,min):
        self.minimums[cat]=min

    def getminimum(self,cat):
        if cat not in self.minimums: return 0
        return self.minimums[cat]
    
    def classify(self,item,default=None):
        # Loop through looking for the best result
        best=default
        max=0.0
        for c in self.categories():
          p=self.fisherprob(item,c)
          # Make sure it exceeds its minimum
          if p>self.getminimum(c) and p>max:
            best=c
            max=p
        return best



