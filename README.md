# 🗣️ Assistente Vocale AI con OpenAI, Whisper e Dash

Questo progetto è un assistente vocale AI che utilizza le API di OpenAI (Whisper + ChatGPT + TTS) e offre un'interfaccia utente tramite Dash. L'assistente ascolta la voce dell'utente, trascrive il parlato, genera una risposta tramite GPT e la legge ad alta voce.

---

## ✨ Funzionalità principali

* 🎙️ Riconoscimento vocale in tempo reale con **Whisper**
* 🤖 Risposte intelligenti con **GPT-3.5** o **GPT-4 Turbo**
* 🔊 Sintesi vocale con **TTS OpenAI** (voci come nova, alloy, shimmer, ecc.)
* 🌐 Interfaccia web interattiva tramite **Dash**
* 🔄 Ciclo continuo di ascolto → risposta
* ⏱️ Pausa automatica configurabile tra i turni di conversazione
* 🌍 Scelta della lingua di trascrizione (es. italiano, inglese)
* 💾 Salvataggio automatico delle conversazioni in formato CSV

---

## 📦 Requisiti di sistema

* Python 3.9 o superiore
* Connessione internet attiva
* Microfono funzionante
* API Key OpenAI valida
* **ffmpeg** installato nel sistema (necessario per `pydub`)

---

## 🔧 Installazione rapida

```bash
git clone https://github.com/tuo-utente/assistente-vocale-openai.git
cd assistente-vocale-openai

# (Opzionale ma consigliato)
python -m venv venv

# Su Windows PowerShell
.\venv\Scripts\Activate.ps1

# Su Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

## ⚠️ Nota importante per utenti Windows

### Installazione Microsoft C++ Build Tools

Alcuni pacchetti Python, come `simpleaudio`, richiedono un compilatore C++ per essere installati correttamente. Se ricevi errori simili a:

```
error: Microsoft Visual C++ 14.0 or greater is required.
```

segui questi passaggi:

1. Visita la pagina ufficiale:
   [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Scarica ed esegui `vs_buildtools.exe`.
3. Seleziona **Desktop development with C++** e installa.
4. Verifica nel prompt comandi con `cl` se l’installazione è avvenuta correttamente.
5. Reinstalla i pacchetti Python che richiedono compilazione:

   ```bash
   pip install simpleaudio
   ```

---

### Installazione di FFmpeg

`pydub` necessita di `ffmpeg` per gestire i file audio.

Su Windows, puoi installare facilmente ffmpeg con **winget**:

```powershell
winget install ffmpeg
```

Verifica l’installazione aprendo un terminale e digitando:

```bash
ffmpeg -version
```

---

## 🔐 Configurazione API

1. Crea un file `.env` nella root del progetto con questo contenuto:

```env
OPENAI_API_KEY=la_tua_chiave_api_openai
```

2. Assicurati che `.env` sia incluso in `.gitignore` per evitare di caricare la chiave su repository pubblici.

---

## 🚀 Come avviare l'assistente

```bash
python app.py
```

Apri il browser su:

```
http://127.0.0.1:8050
```

Potrai quindi iniziare a parlare con l’assistente tramite l’interfaccia web.

---

## 🛠️ Struttura del progetto

| File                | Descrizione                                                      |
| ------------------- | ---------------------------------------------------------------- |
| `app.py`            | Interfaccia Dash e gestione avvio/arresto del loop vocale        |
| `assistant.py`      | Funzioni di registrazione audio, trascrizione, GPT e TTS         |
| `.env`              | File per chiave API (non incluso nel repo)                       |
| `conversazioni.csv` | Log automatico delle conversazioni (timestamp, utente, risposta) |

---

## 📄 Funzionalità in sviluppo (To-Do)

* Scaricamento log conversazioni dalla GUI
* Supporto multi-turno e memoria contestuale
* Integrazione con dispositivi esterni e IoT

---

## 🧑‍💻 Autore

Realizzato con ❤️ da \[Il tuo nome o handle GitHub]

---

## 📜 Licenza

Distribuito con licenza MIT — vedi il file `LICENSE` per dettagli.
