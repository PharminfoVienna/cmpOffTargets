import base64
import random
from os.path import isfile
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from dash import Dash, dcc, html, no_update, Output, Input
import plotly.graph_objects as go

rand_color = lambda : "#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)])

def imgFromSmiles(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    else:
        drawer = rdMolDraw2D.MolDraw2DSVG(400, 400)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        svg_encoded = base64.b64encode(svg.encode('utf-8'))
        return "data:image/svg+xml;base64," + svg_encoded.decode('utf-8')


df = pd.read_csv('umap_test.csv')


fig = go.Figure(data=[
    go.Scatter(
        x=df["x"],
        y=df["y"],
        mode="markers",
        marker=dict(
            colorscale='viridis',
            size=5,
            colorbar={"title": "Prob."},
            line={"color": "#444"},
            reversescale=True,
            sizeref=45,
            sizemode="diameter",
            opacity=0.8,
        )
    )
])
#fig.update_traces(marker_color=(np.abs(df['doha']-df['iris'])))
fig.update_traces(hoverinfo="none", hovertemplate=None)

fig.update_layout(
    xaxis=dict(title='X - Coordinate'),
    yaxis=dict(title='Y - Coordinate'),
    margin=dict(l=0, r=0, t=8, b=0),
    #plot_bgcolor='rgba(255,255,255,0.1)'
)

app = Dash(__name__)
app.layout = html.Div([html.Div('Combining Machine Learning Models from Publicly Available and Proprietary Domains to Identify Potential Off-Target Interactions',
                                #Put this label in a box with a background color of #f5f5f5 and a border of 1px solid #dcdcdc
                                style={'font-size': '20px', 'color': '#000000', 'background-color': '#f5f5f5', 'border': '1px solid #dcdcdc', 'padding': '10px','text-align': 'center'}
                                ),
         html.Center(html.Div([

            #Choose a model from Cox2,AChE,PDE4D,MAOA

            dcc.Dropdown(
                id='target',
                options=[
                    {'label': 'Cox2', 'value': 'Cox2'},
                    {'label': 'AChE', 'value': 'AChE'},
                    {'label': 'PDE4D', 'value': 'PDE4D'},
                    {'label': 'MAOA', 'value': 'MAOA'}
                ],
                value='Cox2',
                style={'width': '40%', 'display': 'inline-block'},
            ),
            # dcc.Dropdown(
            #     id='weight',
            #     options = [{'label': f'{frac}', 'value': f'{frac}'} for frac in np.arange(0.1, 1., 0.1)],
            #     value='0.1',
            #     style={'width': '20%', 'display': 'inline-block'},
            # ),

            dcc.RadioItems(
                id='model',
                options=[
                    {'label': 'Model from Naga et. al.', 'value': 'doha'},
                    {'label': 'ChEMBL model', 'value': 'iris'},
                    {'label': 'Difference', 'value': 'diff'},
                ],
                value='diff',
                labelStyle={'display': 'inline-block'}
            ),

            dcc.Graph(id='graph-basic-2', figure=fig, clear_on_unhover=True, style={'height': '90vh'}),
            dcc.Tooltip(id="graph-tooltip"),
         ], style={'width': '100%', 'text-align': 'center', 'vertical-align': 'center','padding': '10px'}))])

#Choose between Doha's model and Iris's model and Differece between them
@app.callback(
    Output('graph-basic-2', 'figure'),
    [Input('model', 'value')],
    [Input('target', 'value')])
def update_graph(model, target):
    if model == "doha":
        fig.update_traces(marker_color=df[f'doha_{target}'])
    elif model == "iris":
        fig.update_traces(marker_color=df[f'iris_{target}'])
    else:
        fig.update_traces(marker_color=(np.abs(df[f'doha_{target}']-df[f'iris_{target}'])))
    return fig


@app.callback(
    Output("graph-tooltip", "show"),
    Output("graph-tooltip", "bbox"),
    Output("graph-tooltip", "children"),
    Input("graph-basic-2", "hoverData"),
)
def display_hover(hoverData):
    if hoverData is None:
        return False, no_update, no_update

    # demo only shows the first point, but other points may also be available

    #Find all points with the same x and y coordinates in df
    #df_subset = df[(df['x'] == hoverData['points'][0]['x']) & (df['y'] == hoverData['points'][0]['y'])]
    df_subset = df[(df['x'] == hoverData['points'][0]['x']) & (df['y'] == hoverData['points'][0]['y'])]
    #print("----------------------------------------------------")
    pt = hoverData["points"][0]

    #point = df.loc[(pt['pointNumber']), ['canonical_smiles', 'pchembl_value','family']]

    bbox = pt["bbox"]

    def make_molecular_card(point):
        return html.Div([
            html.Img(src=imgFromSmiles(point['smiles']), style={'width': '100%', 'height': '100%'}),
            #Make a table with Doha\'s models and Iris\'s models for each target
            html.Table([
                #Make a header for the table
                html.Thead(html.Tr([html.Th("Target"), html.Th("Naga et. al."), html.Th("ChEMBL")])),
                html.Tr([html.Td('Cox2'), html.Td(f'{point["doha_Cox2"]:.2f}'), html.Td(f'{point["iris_Cox2"]:.2f}')]),
                html.Tr([html.Td('AChE'), html.Td(f'{point["doha_AChE"]:.2f}'), html.Td(f'{point["iris_AChE"]:.2f}')]),
                html.Tr([html.Td('PDE4D'), html.Td(f'{point["doha_PDE4D"]:.2f}'), html.Td(f'{point["iris_PDE4D"]:.2f}')]),
                html.Tr([html.Td('MAOA'), html.Td(f'{point["doha_MAOA"]:.2f}'), html.Td(f'{point["iris_MAOA"]:.2f}')]),
            ], style={'width': '100%', 'height': '100%'})

            #html.P(f'Doha\'s model: {round(point["doha"],3)}'),
            #html.P(f'Iris\' model: {round(point["iris"],3)}'),
        ], style={'font-size': '18px','display': 'inline'})

    children = html.Div([
        make_molecular_card(point) for point in df_subset.to_dict('records')
    ])
    return True, bbox, children

app.run_server(debug=False)
