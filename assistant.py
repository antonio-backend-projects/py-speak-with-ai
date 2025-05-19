from openai import OpenAI
import sounddevice as sd
import scipy.io.wavfile
import uuid
import os
import time
import csv
import threading
import traceback
from datetime import datetime
from dotenv import load_dotenv
from pydub import AudioSegment
import simpleaudio as sa
from queue import Queue, Empty
from tenacity import retry, stop_after_attempt, wait_exponential
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache

load_dotenv()

@dataclass
class AppState:
    is_running: bool = False
    current_status: str = "Inattivo"
    conversation: list = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # Aggiungi questo metodo
    def get_conversation(self):
        with self._lock:
            return self.conversation.copy()

    def update_status(self, new_status):
        with self._lock:
            self.current_status = new_status
    
    def update_settings(self, lang, model, voice, pause):
        with self._lock:
            self.settings = {
                "language": lang,
                "model": model,
                "voice": voice,
                "pause": pause
            }
    
    def add_conversation(self, user, system):
        with self._lock:
            self.conversation.append(f"{user}\n{system}\n")
    
    def stop(self):
        with self._lock:
            self.is_running = False
    
    def reset(self):
        with self._lock:
            self.__init__()

class LogManager:
    def __init__(self):
        self.queue = Queue(maxsize=100)
        self.history = []
        self._lock = threading.Lock()

    def add_log(self, user_msg, system_msg):
        with self._lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "user": user_msg,
                "system": system_msg
            }
            try:
                self.queue.put_nowait(entry)
                self.history.append(entry)
            except:
                pass

    def get_logs(self):
        logs = []
        while True:
            try:
                logs.append(self.queue.get_nowait())
            except Empty:
                break
        return logs

log_manager = LogManager()
stop_event = threading.Event()

@lru_cache(maxsize=1)
def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@contextmanager
def temp_audio_file():
    filename = f"temp_{uuid.uuid4()}.wav"
    try:
        yield filename
    finally:
        if os.path.exists(filename):
            os.remove(filename)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
def record_audio(filename):
    try:
        recording = sd.rec(int(44100 * 5), samplerate=44100, channels=1)
        sd.wait()
        scipy.io.wavfile.write(filename, 44100, recording)
    except sd.PortAudioError as e:
        log_manager.add_log("SYSTEM", f"Errore registrazione: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
def transcribe_audio(filename, language):
    try:
        with open(filename, "rb") as audio_file:
            transcript = get_openai_client().audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                language=language
            )
        return transcript.text
    except Exception as e:
        log_manager.add_log("SYSTEM", f"Errore trascrizione: {str(e)}")
        raise

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
def get_chatgpt_response(prompt, model):
    try:
        response = get_openai_client().chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        log_manager.add_log("SYSTEM", f"Errore GPT: {str(e)}")
        raise

def synthesize_speech(text, voice):
    try:
        filename = f"response_{uuid.uuid4()}.mp3"
        response = get_openai_client().audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        with open(filename, "wb") as f:
            f.write(response.read())

        def play_audio():
            try:
                sound = AudioSegment.from_file(filename, format="mp3")
                play_obj = sa.play_buffer(
                    sound.raw_data,
                    num_channels=sound.channels,
                    bytes_per_sample=sound.sample_width,
                    sample_rate=sound.frame_rate
                )
                play_obj.wait_done()
                os.remove(filename)
            except Exception as e:
                log_manager.add_log("SYSTEM", f"Errore riproduzione: {str(e)}")

        threading.Thread(target=play_audio, daemon=True).start()

    except Exception as e:
        log_manager.add_log("SYSTEM", f"Errore sintesi vocale: {str(e)}")
        raise

def voice_loop(settings):
    stop_event.clear()
    while not stop_event.is_set():
        try:
            log_manager.add_log("**[ASCOLTO]**", "")
            
            with temp_audio_file() as filename:
                record_audio(filename)
                user_text = transcribe_audio(filename, settings["language"])
                
                if not user_text:
                    continue

                log_manager.add_log(f"👤 {user_text}", "**[PENSO...]**")
                reply = get_chatgpt_response(user_text, settings["model"])
                log_manager.add_log("", f"🤖 {reply} [PARLO]")
                synthesize_speech(reply, settings["voice"])
                
                with threading.Lock():
                    with open("conversazioni.csv", "a", newline='', encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([datetime.now().isoformat(), user_text, reply])

                time.sleep(settings["pause"])
        
        except Exception as e:
            log_manager.add_log("SYSTEM", f"Errore loop: {traceback.format_exc()}")
            stop_event.set()