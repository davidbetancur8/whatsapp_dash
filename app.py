import base64
import datetime
import io

from io import BytesIO

import numpy as np
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
import plotly.express as px

import pandas as pd

from stop_words import get_stop_words
import collections
from wordcloud import WordCloud
import matplotlib.pyplot as plt

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = html.Div([

    dcc.Input(
        id="palabra",
        placeholder = "Ingresa la palabra que quieres buscar y luego sube el archivo",
        type="text",
        value = ""
        ),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },

    ),
    html.Div(
            dcc.Graph(
                id = "cuenta",
            )
        ),

    html.Div(
            dcc.Graph(
                id = "horas",
            )
        ),
    html.Div(
        dcc.Graph(
            id = "by_word",
        )
        ),
    html.Div(
        html.Img(
            id = 'wc_plot', 
            src = ''))
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    info = []
    try:
        if 'txt' in filename:
            print("file readed")
            print("*"*10)
            for line in decoded.decode('utf-8').split("\n"):
                try:
                    if ":" in line.split("-")[1]:
                        date = line.split("-")[0]
                        name = line.split("-")[1].split(":")[0]
                        message = line.split("-")[1].split(":")[1]
                    else:
                        pass
                    info.append([date, name, message])
                except Exception as e:
                    pass

            print("info ready")
            print("*"*10)
            df = pd.DataFrame(info, columns=["date", "name", "message"])
            df.name = df.name.str.strip()
            df.date = df.date.str.strip()
            df['date'] =  pd.to_datetime(df['date'], errors="coerce")

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return df


def fig_to_uri(in_fig, close_all=True, **save_args):
    # type: (plt.Figure) -> str
    """
    Save a figure as a URI
    :param in_fig:
    :return:
    """
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded)

def agrupar(x):
    todo = []
    for ex in x:
        todo.append(ex)
    todo_str = " ".join(todo)
    return todo_str

@app.callback(Output('cuenta', 'figure'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])

def update_count(content, name, date):
    if content is not None:
        df = parse_contents(content, name, date)
        df_count = pd.DataFrame(df['name'].value_counts()).reset_index()
        fig = px.bar(df_count, x="index", y="name")
        fig.update_layout(title='Número de mensajes por persona',
                   xaxis_title='Persona',
                   yaxis_title=f'Número de mensajes')
        return fig
    else:
        a = ["persona1","persona2", "persona3"]
        b = [2,4,6]
        df_p = pd.DataFrame({"a":a, "b":b})
        fig = px.bar(df_p, x="a", y="b")
        return fig


@app.callback(Output('horas', 'figure'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_hours(content, name, date):
    if content is not None:
        df = parse_contents(content, name, date)
        by_dates_df = pd.DataFrame(df.groupby([df.date.dt.hour])["name"].count()).reset_index()
        fig = px.bar(by_dates_df, x="date", y="name")
        fig.update_layout(title='horas mas comunes',
                   xaxis_title='hora del dia',
                   yaxis_title=f'numero de mensajes')
        return fig
    else:
        a = ["dia 1","dia 2", "dia 3"]
        b = [2,4,6]
        df_p = pd.DataFrame({"a":a, "b":b})
        fig = px.bar(df_p, x="a", y="b")
        return fig
    

@app.callback(Output('by_word', 'figure'),
              [Input('upload-data', 'contents'),
               Input("palabra", "value")],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_palabra(content, palabra, name, date):
    if content is not None:
        df = parse_contents(content, name, date)
        df_word = df.copy()
        df_word[palabra] = np.where(df['message'].str.contains(palabra, case=False, na=False), 1, 0)
        df_words = pd.DataFrame(df_word.groupby("name")[palabra].sum().sort_values(ascending=False)).reset_index()
        fig = px.bar(df_words, x="name", y=palabra)
        fig.update_layout(title=f'Personas que mas dicen {palabra}',
                   xaxis_title='Persona',
                   yaxis_title=f'Número de veces')
        return fig
    else:
        a = ["dia 1","dia 2", "dia 3"]
        b = [2,4,6]
        df_p = pd.DataFrame({"a":a, "b":b})
        fig = px.bar(df_p, x="a", y="b")
        return fig



@app.callback(Output('wc_plot', 'src'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_wc(content, name, date):
    if content is not None:
        df = parse_contents(content, name, date)
        all_text = df.groupby([True]*len(df)).message.apply(agrupar).values[0]
        all_text = all_text.replace("jajaja", "")
        all_text = all_text.replace("jaja", "")
        stopwords = get_stop_words('es')
        lista_propia = ["<multimedia", "omitido>", "https", "ja"]
        for palabra in lista_propia:
            stopwords.append(palabra)
        wordcount = collections.defaultdict(int)
        for word in all_text.lower().split():
            if word not in stopwords:
                wordcount[word] += 1

        wc = WordCloud(background_color="black",width=1000, height=1500).generate_from_frequencies(wordcount)
        fig = plt.figure(figsize=(15,15))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis('off')
        out_url = fig_to_uri(fig)
        return out_url




if __name__ == '__main__':
    app.run_server(debug=True, port=8881)