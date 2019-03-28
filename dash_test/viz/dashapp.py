from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html

from .server import app
from . import router


app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    dcc.Link('Index', href=f'{app.url_base_pathname}'),
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
