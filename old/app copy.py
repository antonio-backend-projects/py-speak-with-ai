from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import threading
from assistant import voice_loop, stop_loop

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
conversation = []

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

    dbc.Button("Avvia Conversazione", id="start-btn", color="success", className="me-2"),
    dbc.Button("Ferma", id="stop-btn", color="danger"),

    html.Hr(),
    html.Div(id="conversation-log", style={"whiteSpace": "pre-line", "height": "300px", "overflowY": "scroll"}),
    dcc.Interval(id="interval", interval=1000, n_intervals=0, disabled=True),
])

@app.callback(
    Output("interval", "disabled"),
    Input("start-btn", "n_clicks"),
    State("lang-dropdown", "value"),
    State("model-dropdown", "value"),
    State("voice-dropdown", "value"),
    State("pause-input", "value"),
    prevent_initial_call=True
)
def start_conversation(_, lang, model, voice, pause):
    user_settings.update({
        "language": lang,
        "model": model,
        "voice": voice,
        "pause": pause
    })

    def update_log(user_text, reply):
        conversation.append(f"👤 {user_text}\n🤖 {reply}\n")

    threading.Thread(target=voice_loop, args=(update_log, user_settings), daemon=True).start()
    return False

@app.callback(
    Output("conversation-log", "children"),
    Input("interval", "n_intervals")
)
def update_output(_):
    return "\n".join(conversation)

@app.callback(
    Output("interval", "disabled", allow_duplicate=True),
    Input("stop-btn", "n_clicks"),
    prevent_initial_call=True
)
def stop_conversation(_):
    stop_loop()
    return True

if __name__ == "__main__":
    app.run(debug=True)
