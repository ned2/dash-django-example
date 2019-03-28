from django.urls import re_path

from . import views
from . import dashapp # this loads the Dash app

urlpatterns = [
    re_path('^_dash-', views.dash_json),
    re_path('^assets/', views.dash_guess_mimetype),
    re_path('^', views.dash_index),
    
]
