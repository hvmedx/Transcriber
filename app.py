from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import numpy as np
from transcribe import transcribe_chunk
from gpt_pipeline import summarise_and_question
from report_generator import generate_live_report
import threading
import json
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=BASE_DIR)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

SAMPLE_RATE = 16000
SESSION_FILE = os.path.join(BASE_DIR, "session.json")
session_data = []
is_recording = False
accumulated_text = ""
live_report_data = {}

def process_chunk(chunk_audio, sample_rate):
    """Traite un chunk audio reçu du navigateur et envoie les résultats au frontend"""
    global session_data, accumulated_text, live_report_data
    try:
        segments = transcribe_chunk(chunk_audio, sample_rate)
        for seg in segments:
            if not seg["text"].strip():
                continue

            socketio.emit('transcription', {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            })

            accumulated_text += " " + seg["text"]

            try:
                summary_q = summarise_and_question(seg["text"])
                lines = summary_q.split("\n")
                summary = lines[0] if lines else ""
                questions = [q.strip() for q in lines[1:] if q.strip()]

                socketio.emit('analysis', {
                    'summary': summary,
                    'questions': questions
                })

                if len(session_data) % 3 == 0 and len(accumulated_text) > 50:
                    report_json = generate_live_report(accumulated_text)
                    if report_json:
                        try:
                            report_json = report_json.strip()
                            if report_json.startswith('```json'):
                                report_json = report_json[7:]
                            if report_json.endswith('```'):
                                report_json = report_json[:-3]
                            report_json = report_json.strip()

                            live_report_data = json.loads(report_json)
                            socketio.emit('live_report', live_report_data)
                        except json.JSONDecodeError as je:
                            print(f"Erreur parse JSON rapport: {je}")
                            print(f"JSON reçu: {report_json}")

                session_data.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "summary": summary,
                    "questions": questions
                })

                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)

            except Exception as e:
                socketio.emit('error', {'message': f'Erreur GPT: {str(e)}'})

    except Exception as e:
        socketio.emit('error', {'message': f'Erreur transcription: {str(e)}'})


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('start_recording')
def start_recording():
    global is_recording, session_data, accumulated_text, live_report_data
    if not is_recording:
        is_recording = True
        session_data = []
        accumulated_text = ""
        live_report_data = {}
        emit('status', {'recording': True, 'message': 'Enregistrement démarré'})


@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """Réception d'un buffer audio (Float32) envoyé par le navigateur"""
    global is_recording
    if not is_recording:
        return

    try:
        audio_list = data.get("audio")
        browser_rate = data.get("sampleRate", SAMPLE_RATE)
        if not audio_list:
            return

        audio_np = np.array(audio_list, dtype=np.float32)
        threading.Thread(
            target=process_chunk,
            args=(audio_np, browser_rate),
            daemon=True
        ).start()
    except Exception as e:
        emit('error', {'message': f'Erreur réception audio: {str(e)}'})


@socketio.on('stop_recording')
def stop_recording():
    global is_recording
    if is_recording:
        is_recording = False
        emit('status', {'recording': False, 'message': f'Arrêté - {len(session_data)} segments'})


@app.route('/session')
def get_session():
    """API pour récupérer toute la session"""
    return jsonify(session_data)


if __name__ == '__main__':
    print("🚀 Serveur démarré sur http://localhost:5000")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
