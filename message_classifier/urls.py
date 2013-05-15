from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns('',
                       url(r"^hal/$", views.message_classification, name="classifier"),
)
