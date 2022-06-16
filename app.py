from dash import Dash, dash_table, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

import requests
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.io as poi
import plotly.graph_objects as go

""" READ DATA """
#Source - http://www.asterank.com/
response = requests.get('http://asterank.com/api/kepler?query={}&limit=5000')
df = pd.json_normalize(response.json())
df = df[(df.PER > 0)]
df['KOI'] = df['KOI'].astype(int, errors = 'ignore')

min_RPLANET_Df = min(df.RPLANET)
max_RPLANET_Df = max(df.RPLANET)

#create star size category
bins = [0, 0.8, 1.2, 100]
names = ['small','similar','bigger']
df['StarSize'] = pd.cut(df.RSTAR, bins, labels=names)

# TEMPERATURE BINS
tp_bins = [0, 200, 400, 500, 5000]
tp_labels = ['t_low', 't_optimal', 't_high', 't_extreme']
df['temp'] = pd.cut(df.TPLANET, tp_bins, labels = tp_labels)

# SIZE BINS
r_bins = [0, 0.5, 2, 4, 100]
r_labels = ['r_low', 'r_optimal', 'r_high', 'r_extreme']
df['gravity'] = pd.cut(df.RPLANET, r_bins, labels = r_labels)

# ESTIMATED OBJECT

df['status'] = np.where((df['temp'] == 't_optimal') & (df['gravity'] == 'r_optimal'), 'promising', None)
df.loc[:,'status'] = np.where((df['temp'] == 't_optimal') & (df['gravity'].isin(['r_low','r_high'])), 'challenging', df['status'])
df.loc[:,'status'] = np.where((df['gravity'] == 'r_optimal') & (df['temp'].isin(['t_low','t_high'])), 'challenging', df['status'])
df['status'] = df.status.fillna('extreme')

# RELATIVE DISTANCE
df['relative_dist'] = df['A']/df['RSTAR']

#GLOBAL DESIGN SETTINGS
CHARTS_TEMPLATE = dict(
    layout=go.Layout(
                    font = dict(family="Rockwell"),
                    title_font = dict(family="Rockwell" , size=24),
                    legend = dict(orientation = 'h', title_text = '', x = 0, y = 1.1)
                    )
)

COLOR_STATUS_VALUES = ['#646466','#3462eb','#12e639']


#print(df.status.value_counts(dropna=False))

star_size_selector = dcc.Dropdown(
    id = 'star_selector',
    options = [{'label': k, 'value': k} for k in names],
    value = ['small','similar','bigger'],
    multi = True
)

tplanet_selector = dcc.RangeSlider(
    id = 'range_slider',
    min = min_RPLANET_Df, # Minimal value
    max = max_RPLANET_Df, # Maximum value
    marks = {min_RPLANET_Df: str(min_RPLANET_Df), 10: '10', 30: '30', 50: '50', 70: '70', max_RPLANET_Df: str(max_RPLANET_Df)}, #Marks
    step = 1, # Step
    value = [min_RPLANET_Df,max_RPLANET_Df] # Default value
)

#https://github.com/facultyai/dash-bootstrap-components
#
external_stylesheets = [dbc.themes.FLATLY]

app = Dash(__name__, external_stylesheets=external_stylesheets)

""" TABS CONTENT """

# tab1 content
tab1_content = [    
    dbc.Row([
        dbc.Col([
            html.Div(id = 'dist_temp_chart')
        ],
            width={'size': 6}
        ),
        dbc.Col([
            html.Div(id = 'dist_celestial_chart')
        ],
            width={'size': 6}
        )
    ],
    style = {'margin-top': 20}
    ),
    dbc.Row([
        dbc.Col([
            html.Div(id = 'relative_distance_chart')
        ]),
        dbc.Col([
            html.Div(id = 'mstart_tstar_chart')
        ])
    ])]

# tab2 content
tab2_content = [
    dbc.Row([
        dbc.Col([
            html.Div(id = 'data_table')
        ])
    ],
     style = {'margin-top': 20}
    )
  
]
# tab3 content
text = 'Data are sourced from Kepler API via asterank.com'
table_header = [
    html.Thead(html.Tr([html.Th("Field Name"), html.Th("Details")]))
]

expl ={
'KOI':	'Object of Interest number',
'A':	'Semi-major axis (AU)',
'RPLANET':	'Planetary radius (Earth radii)',
'RSTAR':	'Stellar radius (Sol radii)',
'TSTAR':	'Effective temperature of host star as reported in KIC (k)',
'KMAG':	'Kepler magnitude (kmag)',
'TPLANET':	'Equilibrium temperature of planet, per Borucki et al. (k)',
'T0':	'Time of transit center (BJD-2454900)',
'UT0':	'Uncertainty in time of transit center (+-jd)',
'PER':	'Period (days)',
'UPER':	'Uncertainty in period (+-days)',
'DEC':	'Declination (@J200)',
'RA':	'Right ascension (@J200)',
'MSTAR':	'Derived stellar mass (msol)'
}

tbl_rows = []
for i in expl:
    tbl_rows.append(html.Tr([html.Td(i), html.Td(expl[i])]))
table_body = [html.Tbody(tbl_rows)]
table = dbc.Table(table_header + table_body, bordered=True)


tab3_content = [
    dbc.Row([
        dbc.Col([
            html.A(text, href = 'http://www.asterank.com/kepler')
        ])
    ],
     style = {'margin-top': 20}
    )
    ,
    dbc.Row([
        dbc.Col([
            html.Div(children = table)
        ])
    ],
     style = {'margin-top': 20}
    )
  
]

""" LAYOUT """

app.layout = html.Div([
    # header
        dbc.Row([
        dbc.Col(
            html.Img(src = app.get_asset_url('images/exoplanets_by_jaysimons-d9dv6th-small1.jpg'),
            style  = {'width': '70px',
                      'height': '70px',
                      'border-radius': '50%',
                      'marginTop': '20px',
                      'marginLeft': '40px'
                     }),
            width = 1
            ),
        dbc.Col([
            html.H1('Exoplanet analysis', style = {'textAlign' : 'center', 'marginTop' : 20 })
            ],
            width = 6
            ),
        dbc.Col(
            html.Div([
                html.A('Read about exoplanet', href = 'https://spaceplace.nasa.gov/all-about-exoplanets/en/') ,
                ],
                style = {'textAlign' : 'center', 'marginTop' : 40 }
                ),
            width = 2
            ),
        dbc.Col(
            html.Div([
                html.P('Developed by'),
                html.A('Artem Suchkov', href = '', style={'marginLeft': '2px'})
                ],
                 className = 'app-referral'
                ),
            width = 3
            ),
    ],  className = 'app-header'),
    #Store sessions up to 5~10 MB
    dcc.Store(id = 'filtered_data', storage_type = 'session'),
    #Body
    html.Div([
    #html.Hr(),
    dbc.Row([
        dbc.Col([
                html.H6('Select Planet main semi-axis range'),
                html.Div(tplanet_selector)
            ],
                width={'size': 3}
            ),
        dbc.Col([
                html.H6('Star size'),
                html.Div(star_size_selector),
            ],
                width={'size': 3, 'offset': 0} #offset - отступ
            ),
        dbc.Col(dbc.Button('Apply', id ='submit-val', className= 'mr-2'), style={'marginTop': '25px'})],
        style = {'margin-bottom':40}
        ),
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(tab1_content, tab_id='graphs_tab', label = ' Charts'),
                dbc.Tab(tab2_content, tab_id='table_tab', label = 'Data'),
                dbc.Tab(tab3_content, tab_id='about_tab',  label = 'About')
        ],
            id = 'tabs',
            active_tab = 'graphs_tab')
            ]),
    ]),
],
   className = 'app-body' )
])

""" CALLBACKS """
@app.callback(
    Output(component_id= 'filtered_data', component_property='data'),
    [Input(component_id='submit-val', component_property = 'n_clicks')],
    [State(component_id='range_slider', component_property='value'),
    State(component_id='star_selector', component_property='value')]
)
def filter_data(n, radius_range, star_size):
    my_data = df[(df.RPLANET > radius_range[0]) &
                 (df.RPLANET < radius_range[1]) &
                 (df.StarSize.isin(star_size))]

    return my_data.to_json(date_format='iso', orient='split', default_handler=str)

# 1 Chart Callback Planet temperature ~ Distance from Star
@app.callback(
    Output(component_id='dist_temp_chart', component_property='children'),
    [Input(component_id='filtered_data', component_property = 'data')]
     )
def update_chart(data):

    chart_date = pd.read_json(data, orient = 'split')

    if chart_date.shape[0] == 0:
        return html.Div('Please select more data'), html.Div()

    # Graph Planet temperature ~ Distance from Star
    fig1 = px.scatter(chart_date, x = 'TPLANET', y = 'A', color = 'StarSize')
    fig1.update_layout(template = CHARTS_TEMPLATE)
    html1 = [
            html.H4('Planet temperature ~ Distance from Star'),
            dcc.Graph(figure = fig1) # 1 Graph Planet temperature ~ Distance from Star
    ]
    return html1


# 2 Chart Callback Position on the Celestial Sphere
@app.callback(
    Output(component_id='dist_celestial_chart', component_property='children'),
    [Input(component_id='filtered_data', component_property = 'data')]
     )
def update_chart(data):
    chart_date = pd.read_json(data, orient = 'split')
    if chart_date.shape[0] == 0:
        return html.Div('Please select more data'), html.Div()

    # Position on the Celestial Sphere
    fig2 = px.scatter(chart_date, x = 'RA', y = 'DEC', size = 'RPLANET', color = 'status', color_discrete_sequence=COLOR_STATUS_VALUES)
    fig2.update_layout(template = CHARTS_TEMPLATE)
    html2 = [
            html.H4('Position on the Celestial Sphere'),
            dcc.Graph(figure = fig2)
    ]
    return html2


# 3 Chart Callback Relative Distance (AU/Sol radius)
@app.callback(
    Output(component_id='relative_distance_chart', component_property='children'),
    [Input(component_id='filtered_data', component_property = 'data')]
     )
def update_chart(data):

    chart_date = pd.read_json(data, orient = 'split')
    if chart_date.shape[0] == 0:
        return html.Div('Please select more data'), html.Div()

    # Relative dist chart
    fig3 = px.histogram(chart_date, x = 'relative_dist', barmode = 'overlay', color = 'status')
    fig3.add_vline(x = 1, y0 = 0, y1 = 160, annotation_text = 'Earth', line_dash = 'dot')
    fig3.update_layout(template = CHARTS_TEMPLATE)
    html3 = [
            html.H4('Relative Distance (AU/Sol radius)'),
            dcc.Graph(figure = fig3)
    ]
    return html3


# 4 Chart Callback Star Mass ~ Star Temperature
@app.callback(
    Output(component_id='mstart_tstar_chart', component_property='children'),
    [Input(component_id='filtered_data', component_property = 'data')]
     )
def update_chart(data):
    chart_date = pd.read_json(data, orient = 'split')
    if chart_date.shape[0] == 0:
        return html.Div('Please select more data'), html.Div()

    fig4 = px.scatter(chart_date, x = 'MSTAR', y = 'TSTAR', size = 'RPLANET', color = 'status', color_discrete_sequence=COLOR_STATUS_VALUES)
    fig4.update_layout(template = CHARTS_TEMPLATE)
    html4 = [
            html.H4('Star Mass ~ Star Temperature'),
            dcc.Graph(figure = fig4)
    ]
    return html4


# 5 Table Callback Star Mass ~ Star Temperature
@app.callback(
    Output(component_id='data_table', component_property='children'),
    [Input(component_id='filtered_data', component_property = 'data')
    ]
     )
def update_dist_temp_chart(data):
    chart_date = pd.read_json(data, orient = 'split')
    if chart_date.shape[0] == 0:
        return html.Div('Please select more data'), html.Div()

    fig4 = px.scatter(chart_date, x = 'MSTAR', y = 'TSTAR', size = 'RPLANET', color = 'status', color_discrete_sequence=COLOR_STATUS_VALUES)
    fig4.update_layout(template = CHARTS_TEMPLATE)
    html4 = [
            html.H4('Star Mass ~ Star Temperature'),
            dcc.Graph(figure = fig4)
    ]
    
    #RAW DATA TABLE
    raw_data = chart_date.drop(['relative_dist','StarSize', 'ROW'], axis = 1)
    tbl = dash_table.DataTable(data = raw_data.to_dict('records'),
                                columns = [{'name': i, 'id': i} for i in raw_data.columns],
                                style_cell={'textAlign': 'left'},
                                style_data={'width': '100px',
                                            'maxWidth': '100px',
                                            'minWidth': '100px'
                                            },
                                style_header={
                                    'backgroundColor': 'rgb(210, 210, 210)',
                                    'color': 'black',
                                    'fontWeight': 'bold',
                                    'text_align': 'center'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(220, 220, 220)',
                                    }],
                                sort_action='native',
                                filter_action='native',
                                page_size = 50
                            )
    html5 = [html.P('Raw Data'), tbl]

    return html5


if __name__ == '__main__':
    app.run_server(debug=True)