
import unittest
from message_classifier.utils import *
from message_classifier.models import *




class BaseTest(unittest.TestCase):

    def setUp(self):
        self.positive,created=ClassifierCategory.objects.get_or_create(name='pos')
        self.negative,created=ClassifierCategory.objects.get_or_create(name='neg')
        self.neutral,created=ClassifierCategory.objects.get_or_create(name='net')
        self.classifier = FisherClassifier(getfeatures)
        self.classifier.train('u report rocks.', self.positive)
        self.classifier.train('u report to the bum rocks.', self.positive)
        self.classifier.train('the quick rabbit jumps fences', self.positive)
        self.classifier.train('how do i gain', self.negative)
        self.classifier.train('HELP am very sick', self.negative)
        self.classifier.train('the quick brown fox jumps', self.neutral)

    def test_trained_data(self):
        self.assertEqual(1, ClassifierFeature.objects.get(feature='report', category=self.positive).count)

    def test_classifier(self):
       pass