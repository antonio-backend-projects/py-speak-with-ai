from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
from dataclasses import dataclass, field
import threading
from assistant import voice_loop, stop_event, log_manager, AppState
import time

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app_state = AppState()

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
    dcc.Store(id='conversation-store'),
    
    dbc.Accordion([
        dbc.AccordionItem(
            title="Storico Conversazioni",
            children=html.Div(id="history-log")
        )
    ])
])

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
    if app_state.is_running:
        return False, True, False

    app_state.reset()
    app_state.update_settings(lang, model, voice, max(0.5, min(float(pause), 5.0)))

    def start_thread():
        try:
            voice_loop(app_state.settings)
        except Exception as e:
            app_state.add_system_log(f"Errore thread: {str(e)}")
            app_state.stop()

    threading.Thread(target=start_thread, daemon=True).start()
    return False, True, False

@app.callback(
    Output("conversation-log", "children"),
    Output("status-text", "children"),
    Input("interval", "n_intervals"),
)
def update_output(n):
    logs = log_manager.get_logs()
    status = "Inattivo"
    
    for log in logs:
        if log['user'] == "**[ASCOLTO]**":
            status = "🎤 Ascolto"
        elif "PENSO" in log['system']:
            status = "⏳ Elaborazione"
        elif "[PARLO]" in log['system']:
            status = "🔊 Riproduzione"
            app_state.add_conversation(log['user'], log['system'].replace("[PARLO]", ""))
        elif log['system'] == "**[PRONTO]**":
            status = "✅ Pronto"
    
    app_state.update_status(status)
    return "\n".join(app_state.get_conversation()), app_state.current_status

@app.callback(
    Output("interval", "disabled", allow_duplicate=True),
    Output("start-btn", "disabled", allow_duplicate=True),
    Output("stop-btn", "disabled", allow_duplicate=True),
    Input("stop-btn", "n_clicks"),
    prevent_initial_call=True
)
def stop_conversation(n_clicks):
    app_state.stop()
    stop_event.set()
    return True, False, True

if __name__ == "__main__":
    app.run(debug=False, dev_tools_ui=False)