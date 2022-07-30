from django.urls import re_path

from . import views

app_name = "moonstuff"

urlpatterns = [
    re_path(r'^$', views.dashboard, name='dashboard'),
    re_path(r'^scan/$', views.add_scan, name='add_scan'),
    re_path(r'^track/$', views.add_character, name='add_character'),
    re_path(r'^info/(?P<moon_id>[0-9]+)/$', views.moon_info, name='view_moon')
]
