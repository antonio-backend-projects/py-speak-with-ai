from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import threading
from assistant import voice_loop, stop_loop

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
conversation = []

# Stato globale per gestire UI (start/stop)
is_running = False

# Impostazioni di default
user_settings = {
    "language": "it",
    "model": "gpt-4-turbo",
    "voice": "nova",
    "pause": 1.0
}

app.layout = dbc.Container([
    html.H2("🗣️ Assistente Vocale OpenAI", className="my-3"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Lingua trascrizione"),
            dcc.Dropdown(
                id="lang-dropdown",
                options=[{"label": "Italiano", "value": "it"}, {"label": "Inglese", "value": "en"}],
                value="it"
            )
        ]),
        dbc.Col([
            dbc.Label("Modello GPT"),
            dcc.Dropdown(
                id="model-dropdown",
                options=[
                    {"label": "GPT-4 Turbo", "value": "gpt-4-turbo"},
                    {"label": "GPT-3.5 Turbo", "value": "gpt-3.5-turbo"}
                ],
                value="gpt-4-turbo"
            )
        ]),
        dbc.Col([
            dbc.Label("Voce sintetica"),
            dcc.Dropdown(
                id="voice-dropdown",
                options=[
                    {"label": v.capitalize(), "value": v} for v in
                    ["nova", "alloy", "shimmer", "fable", "onyx", "echo"]
                ],
                value="nova"
            )
        ]),
        dbc.Col([
            dbc.Label("Pausa (sec)"),
            dcc.Input(id="pause-input", type="number", min=0.5, step=0.5, value=1.0)
        ])
    ], className="mb-4"),

    dbc.Button("Avvia Conversazione", id="start-btn", color="success", className="me-2", disabled=False),
    dbc.Button("Ferma", id="stop-btn", color="danger", disabled=True),

    html.Hr(),

    html.Div([
        html.Div("Stato: ", style={"display": "inline", "fontWeight": "bold"}),
        html.Span(id="status-text", children="Inattivo", style={"color": "gray", "fontWeight": "bold"})
    ], className="mb-2"),

    html.Div(id="conversation-log", style={
        "whiteSpace": "pre-line",
        "height": "300px",
        "overflowY": "scroll",
        "border": "1px solid #ccc",
        "padding": "10px",
        "backgroundColor": "#f9f9f9",
        "fontFamily": "monospace",
        "fontSize": "14px"
    }),
    dcc.Interval(id="interval", interval=1000, n_intervals=0, disabled=True),
])

# Variabile globale per lo stato attuale da mostrare
current_status = "Inattivo"

@app.callback(
    Output("interval", "disabled"),
    Output("start-btn", "disabled"),
    Output("stop-btn", "disabled"),
    Input("start-btn", "n_clicks"),
    State("lang-dropdown", "value"),
    State("model-dropdown", "value"),
    State("voice-dropdown", "value"),
    State("pause-input", "value"),
    prevent_initial_call=True
)
def start_conversation(n_clicks, lang, model, voice, pause):
    global is_running, current_status
    if is_running:
        # Già in esecuzione
        return False, True, False
    is_running = True
    current_status = "Avviato"

    user_settings.update({
        "language": lang,
        "model": model,
        "voice": voice,
        "pause": pause
    })

    def update_log(user_text, reply):
        global current_status
        # Gestione stati speciali dall'assistant.py per UI
        if user_text.startswith("**[ASCOLTO]**"):
            current_status = "🎤 Ascolto"
        elif user_text.startswith("**[PENSO...]**"):
            current_status = "⏳ Penso"
        elif "[PARLO]" in reply:
            current_status = "🔊 Parlo"
            # rimuovo tag [PARLO] dal testo visivo
            reply = reply.replace("[PARLO]", "").strip()
        elif reply == "**[PRONTO]**":
            current_status = "✅ Pronto"
            # Evito che venga aggiunto al log

        if user_text not in ["**[ASCOLTO]**", "**[PENSO...]**"] and reply not in ["**[PRONTO]**"]:
            conversation.append(f"{user_text}\n{reply}\n")

    threading.Thread(target=voice_loop, args=(update_log, user_settings), daemon=True).start()
    return False, True, False

@app.callback(
    Output("conversation-log", "children"),
    Output("status-text", "children"),
    Input("interval", "n_intervals")
)
def update_output(n):
    # Mostra tutta la conversazione + stato
    text = "\n".join(conversation)
    return text, current_status

@app.callback(
    Output("interval", "disabled", allow_duplicate=True),
    Output("start-btn", "disabled", allow_duplicate=True),
    Output("stop-btn", "disabled", allow_duplicate=True),
    Input("stop-btn", "n_clicks"),
    prevent_initial_call=True
)
def stop_conversation(n_clicks):
    global is_running, current_status
    stop_loop()
    is_running = False
    current_status = "Interrotto"
    return True, False, True

if __name__ == "__main__":
    app.run(debug=True)
