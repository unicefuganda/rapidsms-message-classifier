Rapidsms-message_classifier
=============================

Rapidsms-message_classifier is a simple message classifier given a set of categories and training data.


 The actual  classifier is  based on the  [Naive Bayes]: http://en.wikipedia.org/wiki/Naive_Bayes_classifier algorithm  and  makes the 'naive' assumption that all features are
independent.

The classifier also makes use of the [Fisher]: http://en.wikipedia.org/wiki/Fisher%27s_method method.  Unlike the naïve Bayesian filter, which uses the feature probabilities to create a whole document
probability, the Fisher method calculates the probability of a category for each feature in the document



