from flask import Flask, request, jsonify, send_from_directory
import os
import pandas as pd
import numpy as np
import soundfile as sf
import librosa
from keras.models import load_model
import pickle

app = Flask(__name__)

df = pd.read_excel('sinama_bisaya.xlsx')
Bisaya_model = load_model('bisaya_model.h5')
with open('bisaya_label_encoder.pkl', 'rb') as s:
    bisaya_encoder = pickle.load(s)

Sinama_model = load_model('sinama_model.h5')
with open('sinama_label_encoder.pkl', 'rb') as f:
    sinema_encoder = pickle.load(f)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def extract_features(audio_file):
    sound, sampling_rate = librosa.load(audio_file)
    sound_trimmed, _ = librosa.effects.trim(sound, top_db=20)
    sound_trimmed2 = sesi_doldur_kirp(sound_trimmed)
    mfcc = librosa.feature.mfcc(y=sound_trimmed2, sr=sampling_rate)
    chroma = librosa.feature.chroma_stft(y=sound_trimmed2, sr=sampling_rate)
    mfcc = np.reshape(mfcc, (-1, 20, 44))
    chroma_stft = np.reshape(chroma, (-1, 12, 44))
    combined_features = np.concatenate((mfcc, chroma_stft), axis=1)
    return combined_features


@app.route('/')
def home():
    return "Language Translator API"


@app.route('/translate', methods=['POST'])
def translate():
    languages = request.form['languages']
    audio_file = os.path.join(app.config['UPLOAD_FOLDER'], 'output.wav')
    features = extract_features(audio_file)
    if languages == 'sinama':
        y_pred = np.argmax(Bisaya_model.predict(features), axis=1)
        word = bisaya_encoder.inverse_transform(y_pred)[0].lower()
        result = df['SINAMA'][df.loc[df['BISAYA'] == word].index[0]]
    else:
        y_pred = np.argmax(Sinama_model.predict(features), axis=1)
        word = sinema_encoder.inverse_transform(y_pred)[0].lower()
        result = df['BISAYA'][df.loc[df['SINAMA'] == word].index[0]]
    return jsonify({'result': result})


@app.route('/start-recording', methods=['POST'])
def start_recording():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    return jsonify({'success': True})


@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    audio_data = request.data
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'output.wav'), 'wb') as f:
        f.write(audio_data)
    return jsonify({'success': True})


@app.route('/play_sound')
def play_sound():
    filename = request.args.get('filename')
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
