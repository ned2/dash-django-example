import mimetypes

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

        response.direct_passthrough = False
        return response.get_data()


@csrf_exempt
def dash_json(request, **kwargs):
    """Handle Dash JSON API requests"""
    print(request.get_full_path())
    return HttpResponse(dispatcher(request), content_type='application/json')


def dash_index(request, **kwargs):
    """Handle Dash CSS requests"""
    return HttpResponse(dispatcher(request), content_type='text/html')


def dash_guess_mimetype(request, **kwargs):
    """Handle Dash requests and guess the mimetype. Needed for static files."""
    url = request.get_full_path().split('?')[0]
    content_type, _encoding = mimetypes.guess_type(url)
    return HttpResponse(dispatcher(request), content_type=content_type)
