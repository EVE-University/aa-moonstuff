from django.conf.urls import url

from . import views

app_name = "moonstuff"

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
]
