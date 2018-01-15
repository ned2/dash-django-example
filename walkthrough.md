I had been meaning to have a look at that Django trick, so I had a bit of play
around with that code. There's a few issues I see with scaling the way some of
that code is laid out, but which can be smoothed over.

The main issues I see are:
* those urlpatterns using 'path' won't work
* a new Dash instance is needlessly created on every request
* does not support mounting the Dash app at a different prefix


Here's how I fixed these issues. I also made a few other modifications not
necessarily related to the above problems, which you can use or ignore as you
see fit. Also, I'm using Python 3. 

Let's work with a Django project called `dash_test` that contains a single
Django app `viz` that will house the Dash app. Here's the project structure
(omitting the files that `startproject` and `startapp` create that I didn't
touch):

    dash_test/
      urls.py
    viz/
      dashapp.py
      layouts.py
      router.py
      server.py
      urls.py
      views.py

## `dash_test/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', admin.site.urls),
    path('viz/', include('viz.urls')),
]
```

Your suggested approach assumes that the dash app will be mounted at the root of
the site. It will almost certainly be good to have some flexibility about where
it's mounted. Let's run it at `viz/` to make sure we have this modularisation
working.

## `viz/urls.py`
```python
from django.urls import re_path

from . import views
from . import dashapp # this loads the Dash app

urlpatterns = [
    re_path('^_dash-', views.dash_ajax),
    re_path('^', views.dash_index),
]
```


Note that the `path` function you were using looks for an exact match. I think
this might be a recent change with Django, where url routes were always defined
as regexes. Since we want a catchall for the `_dash-*` route, we should use the
`re_path` function. The dash index function should also be a regex, because we
want users to be able to load a URL that was generated with Dash's internal
router (eg `viz/fig1`) and have it take them to the correspond ending state of the
app. If it was an exact match then users would have to load the root of the app
and then navigate through the app to the relevant state.

Also note that the order matters, the more greedy index function would clobber
the ajax function if it came first.


## `viz/views.py`
```python
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
```

Similar to before but with the notable change that the Dash app is no longer
created within the `dispatch` function, which would have had the undesirable
effect of creating a new Dash app on every request. Instead we just import the
already defined Flask server from the server module into the global scope, where
the internals of the `dispatch` function can access it.

## `viz/dashapp.py`
```python
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html

from .server import app
from . import router


app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    dcc.Link('Index', href=app.url_base_pathname),
    ', ',
    dcc.Link('Figure 1', href=f'{app.url_base_pathname}fig1'),
    ', ',
    dcc.Link('Figure 2', href=f'{app.url_base_pathname}fig2'),
    html.Br(),
    html.Br(),
    html.Div(id='content')
])


# callbacks could go here, or in another callback.py file with this at the top:
# from .server import app

```

The main driving module of the app. Importing it will result in the app being "run".
Callbacks can go in here or if there's many of them perhaps in a `callback.py` file.  


## `viz/server.py`
```python
from flask import Flask
from dash import Dash

# should start and end with a '/'
URL_BASE_PATHNAME = '/viz/'

server = Flask(__name__)

app = Dash(
    __name__,
    server=server,
    url_base_pathname=URL_BASE_PATHNAME
)

app.config['suppress_callback_exceptions'] = True
```

This is where the actual Dash app is initialised. We do this in a module that
does as little as possible to reduce the chances of running into impossible to
meed import chains. For instance if the Dash app was created in `dashapp.py`
(which it might seem intuitive to do), then the `router` import would fail because
as it would need to import `app` from `dashapp` but this would not yet be initialised. 

`URL_BASE_PATHNAME` is defined here once, and then accessed through the
corresponding `app.url_base_pathname` attribute elsewhere to ensure that all
generated links and routes have the correct prefix. To mount the app at the root
we would set this to `/` (and also make sure the project's `urls.py` mounts the
Dash app at the root.)

One improvement might be to define a utility function `get_url(path)` or some such
that does the simple job of prefixing this to a given path, so that if the logic
need to change, you wouldn't have to do this for every link/route.

## `viz/router.py`
```python
from dash.dependencies import Output, Input

from .server import app, server
from . import layouts


pages = (
    ('', layouts.index),
    ('fig1', layouts.fig1),
    ('fig2', layouts.fig2),
)

routes = {f"{app.url_base_pathname}{path}": layout for path, layout in pages}


@app.callback(Output('content', 'children'), [Input('url', 'pathname')])
def display_page(pathname):
    ''' '''
    if pathname is None:
        return ''

    page = routes.get(pathname, 'Unknown link') 
    
    if callable(page):
        # can add arguments to layout functions if needed etc
        layout = page()
    else:
        layout = page

    return layout
```

This could go in `dashapp.py,` but I like the idea of keeping the page routes in
a separate file, in the same way that Django does.

I'm not such a fan of pulling out functions with the `dash` prefix and
automatically adding them as routes. This is more of a subjective thing, but it
feels bit too magic and not-discoverable.

Instead, this router maps paths (which are expanded to full prefixed urls) with
corresponding layouts in our `layout.py` file. You could adapt this to post-process 
 the route object in any way you like

```python
from random import randint
import dash_core_components as dcc
import dash_html_components as html


def index():
    return 'Welcome to index page'


def fig1():
    return dcc.Graph(
        id='main-graph',
        figure={
            'data': [{
                'name': 'Some name',
                'mode': 'line',
                'line': {
                    'color': 'rgb(0, 0, 0)',
                    'opacity': 1
                },
                'type': 'scatter',
                'x': [randint(1, 100) for x in range(20)],
                'y': [randint(1, 100) for x in range(20)]
            }],
            'layout': {
                'autosize': True,
                'scene': {
                    'bgcolor': 'rgb(255, 255, 255)',
                    'xaxis': {
                        'titlefont': {'color': 'rgb(0, 0, 0)'},
                        'title': 'X-AXIS',
                        'color': 'rgb(0, 0, 0)'
                    },
                    'yaxis': {
                        'titlefont': {'color': 'rgb(0, 0, 0)'},
                        'title': 'Y-AXIS',
                        'color': 'rgb(0, 0, 0)'
                    }
                }
            }
        }
    )

def fig2():
    return dcc.Graph(
        id='main-graph',
        figure={
            'data': [{
                'name': 'Some name',
                'mode': 'line',
                'line': {
                    'color': 'rgb(0, 0, 0)',
                    'opacity': 1
                },
                'type': 'scatter',
                'x': [randint(1, 100) for x in range(20)],
                'y': [randint(1, 100) for x in range(20)]
            }],
            'layout': {
                'autosize': True,
                'scene': {
                    'bgcolor': 'rgb(255, 255, 255)',
                    'xaxis': {
                        'titlefont': {'color': 'rgb(0, 0, 0)'},
                        'title': 'X-AXIS',
                        'color': 'rgb(0, 0, 0)'
                    },
                    'yaxis': {
                        'titlefont': {'color': 'rgb(0, 0, 0)'},
                        'title': 'Y-AXIS',
                        'color': 'rgb(0, 0, 0)'
                    }
                }
            }
        }
    )
```
