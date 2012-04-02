from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^hal/$", views.message_classification, name="classifier"),
    url(r"^classifier/(?P<message_pk>\d+)/train/(?P<category_pk>\w+)/$", views.train, name="train"),

    )
