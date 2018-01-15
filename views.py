# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from app.as_dash import dispatcher


##### dash #####


def dash(request, **kwargs):
    ''' '''
    return HttpResponse(dispatcher(request))


@csrf_exempt
def dash_ajax(request):
    ''' '''
    return HttpResponse(dispatcher(request), content_type='application/json')