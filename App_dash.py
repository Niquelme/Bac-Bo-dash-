import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
from collections import Counter
import random
import json
import os

app = dash.Dash(__name__)
server = app.server

# Arquivo de histórico
HIST_FILE = "historico_bacbo.json"
if os.path.exists(HIST_FILE):
    with open(HIST_FILE, 'r') as f:
        historico = json.load(f)
else:
    historico = []

cores = {'vermelho': '🔴', 'azul': '🔵', 'amarelo': '🟡'}

# Detectores de padrões
def detectar_empate_vizinho(seq):
    if len(seq) < 3:
        return False
    return (
        seq[-3:] == ['vermelho', 'amarelo', 'vermelho'] or
        seq[-3:] == ['azul', 'amarelo', 'azul']
    )

def detectar_dupla(seq):
    if len(seq) < 4:
        return False
    return (
        seq[-4] == seq[-3] and
        seq[-2] == seq[-1] and
        seq[-3] != seq[-2]
    )

def detectar_trinca(seq):
    if len(seq) < 3:
        return False
    return seq[-1] == seq[-2] == seq[-3]

def detectar_escada_inversa(seq):
    if len(seq) < 3:
        return False
    last3 = seq[-3:]
    return len(set(last3)) == 3 and last3[0] != last3[1] != last3[2]

def detectar_2321(seq):
    if len(seq) < 8:
        return False
    janela = seq[-8:]
    grupos = []
    curr = janela[0]; cnt = 1
    for c in janela[1:]:
        if c == curr:
            cnt += 1
        else:
            grupos.append(cnt)
            curr, cnt = c, 1
    grupos.append(cnt)
    return grupos[:4] == [2,3,2,1]

def prever_por_padrao(seq):
    if detectar_empate_vizinho(seq):
        return 'amarelo'
    if detectar_dupla(seq):
        return 'vermelho' if seq[-1] == 'azul' else 'azul'
    if detectar_trinca(seq):
        return seq[-1]
    if detectar_escada_inversa(seq):
        faltante = [c for c in cores if c not in seq[-3:]]
        return faltante[0] if faltante else random.choice(list(cores.keys()))
    if detectar_2321(seq):
        return seq[-1]
    return None

def gerar_grafico(seq):
    cont = Counter(seq)
    fig = go.Figure(data=[
        go.Bar(
            x=list(cont.keys()),
            y=list(cont.values()),
            marker_color=['red', 'blue', 'gold']
        )
    ])
    fig.update_layout(title='Frequência das Cores', xaxis_title='Cor', yaxis_title='Contagem')
    return fig

def prever_cor(seq):
    pad = prever_por_padrao(seq)
    if pad:
        return pad
    if len(seq) < 2:
        return random.choice(list(cores.keys()))
    last = seq[-1]
    trans = [b for a,b in zip(seq, seq[1:]) if a == last]
    if trans:
        return Counter(trans).most_common(1)[0][0]
    return random.choice(list(cores.keys()))

app.layout = html.Div([
    html.H2("🔮 Previsão do Bac Bo com Padrões (sem IA)"),
    dcc.Dropdown(
        id='dropdown-cor',
        options=[{'label': f"{cores[c]} {c}", 'value': c} for c in cores],
        placeholder="Selecione o resultado mais recente"
    ),
    html.Button("Adicionar", id='btn-add', n_clicks=0),
    html.H4("Histórico:"),
    html.Div(id='div-historico'),
    dcc.Graph(id='graph-freq'),
    html.H4("Próxima Previsão:"),
    html.Div(id='div-previsao')
], style={'maxWidth':'500px','margin':'auto','textAlign':'center'})

@app.callback(
    Output('div-historico', 'children'),
    Output('graph-freq', 'figure'),
    Output('div-previsao', 'children'),
    Input('btn-add', 'n_clicks'),
    State('dropdown-cor', 'value'),
    prevent_initial_call=True
)
def atualizar(n, cor):
    if cor not in cores:
        return dash.no_update, dash.no_update, "Selecione uma cor válida."
    historico.append(cor)
    with open(HIST_FILE, 'w') as f:
        json.dump(historico, f)
    previsao = prever_cor(historico)
    fig = gerar_grafico(historico)
    hist_texto = " ➤ ".join([cores.get(c, c) for c in historico])
    return hist_texto, fig, f"Provável próxima: {cores.get(previsao, previsao)}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
