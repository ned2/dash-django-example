from django.urls import re_path

from . import views
from . import dashapp # this loads the Dash app

urlpatterns = [
    re_path('^_dash-', views.dash_ajax),
    re_path('^', views.dash_index),
]
