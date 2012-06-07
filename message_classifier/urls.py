from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
    url(r"^hal/$", views.message_classification, name="classifier"),
    url(r"^classifier/(?P<message_pk>\d+)/train/(?P<slug>[a-zA-Z\-]+)/$", views.train, name="train"),
    url(r"^classifier/category/(?P<category_pk>\w+)/edit/$", views.edit_category, name="edit_category"),
    url(r"^classifier/(?P<message_pk>\w+)/change_action/(?P<action>\w+)/$", views.edit_action, name="change_action"),

    )
