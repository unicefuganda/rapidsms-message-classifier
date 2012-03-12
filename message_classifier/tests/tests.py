
import unittest
from message_classifier.utils import *
from message_classifier.models import *


POSITIVE = 'pos'
NEGATIVE = 'neg'
NEUTRAL = 'net'


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.classifier = FisherClassifier(getfeatures)
        self.classifier.train('u report rocks.', POSITIVE)
        self.classifier.train('the quick rabbit jumps fences', POSITIVE)
        self.classifier.train('how do i gain', NEGATIVE)
        self.classifier.train('HELP am very sick', NEGATIVE)
        self.classifier.train('the quick brown fox jumps', NEUTRAL)

    def test_trained_data(self):
        pass

    def test_classifier(self):
       pass