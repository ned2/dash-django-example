from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .server import server


def dispatcher(request):
    '''
    Main function
    @param request: Request object
    '''

    params = {
        'data': request.body,
        'method': request.method,
        'content_type': request.content_type
    }
    with server.test_request_context(request.path, **params):
        server.preprocess_request()
        try:
            response = server.full_dispatch_request()
        except Exception as e:
            response = server.make_response(server.handle_exception(e))
        return response.get_data()


def dash_index(request, **kwargs):
    ''' '''
    return HttpResponse(dispatcher(request))


@csrf_exempt
def dash_ajax(request):
    ''' '''
    return HttpResponse(dispatcher(request), content_type='application/json')

