from openai import OpenAI
import sounddevice as sd
import scipy.io.wavfile
import uuid
import os
import time
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

SAMPLE_RATE = 44100
DURATION = 5
stop_flag = False

def record_audio(filename):
    recording = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    scipy.io.wavfile.write(filename, SAMPLE_RATE, recording)

def transcribe_audio(filename, language="it"):
    with open(filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            language=language
        )
    return transcript.text

def get_chatgpt_response(prompt, model="gpt-4-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def synthesize_speech(text, filename="response.mp3", voice="nova"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    with open(filename, "wb") as f:
        f.write(response.read())  # <-- qui cambio
    # Riproduci file audio
    if os.name == 'nt':
        os.system(f"start {filename}")
    elif os.uname().sysname == 'Darwin':
        os.system(f"afplay {filename}")
    else:
        os.system(f"mpg123 {filename} || aplay {filename} || paplay {filename}")


def save_to_csv(user_text, reply, file_path="conversazioni.csv"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, user_text, reply])

def voice_loop(callback, settings):
    global stop_flag
    stop_flag = False
    while not stop_flag:
        filename = f"temp_{uuid.uuid4()}.wav"
        record_audio(filename)
        try:
            user_text = transcribe_audio(filename, language=settings["language"])
        except Exception as e:
            user_text = ""
            print(f"Errore trascrizione: {e}")
        if not user_text:
            os.remove(filename)
            continue
        reply = get_chatgpt_response(user_text, model=settings["model"])
        synthesize_speech(reply, voice=settings["voice"])
        os.remove(filename)
        save_to_csv(user_text, reply)
        callback(user_text, reply)
        time.sleep(settings["pause"])

def stop_loop():
    global stop_flag
    stop_flag = True
