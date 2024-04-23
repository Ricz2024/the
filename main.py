from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
import soundfile as sf
import numpy as np
import sounddevice as sd

from keras.models import load_model
import pickle
import librosa
import datetime
import wavio


df = pd.read_excel('sinama_bisaya.xlsx')
Bisaya_model = load_model('bisaya_model.h5')
with open('bisaya_label_encoder.pkl', 'rb') as s:
    bisaya_encoder = pickle.load(s)

Sinama_model = load_model('sinama_model.h5')
with open('sinama_label_encoder.pkl', 'rb') as f:
    sinema_encoder = pickle.load(f)

def sesi_doldur_kirp(ses, uzunluk=22201): # one second = 22050
    if len(ses) >= uzunluk:
        # Audio file is too long, trim it
        return ses[:uzunluk]
    else:
        # Audio file is too short, fill it out
        return np.pad(ses, (0, uzunluk - len(ses)), "constant")

# Global variables
fs = 22050  # Sampling frequency (Hz)
t = 1.5  # Total recording time (seconds)
recording_state = False  # Registration status
stream = None
res = None

app = Flask(__name__)

@app.route('/')
def home():
    datetoday2 = datetime.datetime.now()
    return render_template('index.html', datetoday2=datetoday2)


@app.route('/translate', methods=['POST'])
def translate():
    global res
    sourcetext = request.form['sourcetext']
    languages = request.form['languages']
    # audiofile = request.files['audiofile']
    # filename = secure_filename(audiofile.filename)
    # audiofile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    print(sourcetext)
    print(languages)
    # print(audiofile)
    sourcetext = sourcetext.strip()
    if sourcetext == '':
        sound, sampling_rate = librosa.load('output.wav')
        print('sound turned up')
        sound_trimmed, _  = librosa.effects.trim(sound, top_db = 20)
        sound_trimmed2 = sesi_doldur_kirp(sound_trimmed)
        mfcc = librosa.feature.mfcc(y = sound_trimmed2, sr = sampling_rate )
        chroma = librosa.feature.chroma_stft(y = sound_trimmed2, sr = sampling_rate)
        mfcc = np.reshape(mfcc, (-1, 20, 44))
        chroma_stft = np.reshape(chroma, (-1, 12, 44))
        combined_features = np.concatenate((mfcc, chroma_stft), axis=1)
        if languages == 'sinama':
            try:
                y_pred = np.argmax(Bisaya_model.predict(combined_features), axis=1)
                sourcetext = bisaya_encoder.inverse_transform(y_pred)[0].lower()
                print(sourcetext)
                res = df['SINAMA'][df.loc[df['BISAYA'] == sourcetext].index[0]]
                sourcetext2 = sourcetext
            except Exception as e:
                print(e)
                res = "I'm sorry. Unfortunately, we couldn't find the word you were looking for. "
        else:
            try:
                y_pred = np.argmax(Sinama_model.predict(combined_features), axis=1)
                sourcetext = sinema_encoder.inverse_transform(y_pred)[0].lower()
                print(sourcetext)
                res = df['BISAYA'][df.loc[df['SINAMA'] == sourcetext].index[0]]
                sourcetext2 = sourcetext
            except Exception as e:
                print(e)
                res = "I'm sorry. Unfortunately, we couldn't find the word you were looking for. "
        return render_template('index.html', res=res, datetoday2=datetime.datetime.now(), sourcetext2=sourcetext2 )

    else:
        sourcetext2 = sourcetext
        if languages != 'sinama':
            try:
                res = df['BISAYA'][df.loc[df['SINAMA'] == sourcetext].index[0]]
            except Exception as e:
                print(e)
                res = "I'm sorry. Unfortunately, we couldn't find the word you were looking for. "
        else:
            try:
                res = df['SINAMA'][df.loc[df['BISAYA'] == sourcetext].index[0]]
            except Exception as e:
                print(e)
                res = "I'm sorry. Unfortunately, we couldn't find the word you were looking for. "


    return render_template('index.html', res=res, datetoday2=datetime.datetime.now() )

@app.route('/play_sound')
def play_sound():
    global res
    sound_url = url_for('static', filename='sounds/'+res+'.wav')
    return sound_url


def audio_callback(indata, frames, time, status):
    if is_recording:
        audio_frames.append(indata.copy())



@app.route('/start-recording', methods=['POST'])
def start_recording():
    global is_recording, audio_frames, stream
    is_recording = True
    audio_frames = []
    sd.default.samplerate = 44100  # Sample audio recording speed
    sd.default.channels = 2  # 2 channels for stereo recording
    stream = sd.InputStream(callback=audio_callback)
    stream.start()
    return jsonify(success=True)

@app.route('/stop-recording', methods=['POST'])
def stop_recording():
    global is_recording, audio_frames, stream
    is_recording = False
    stream.stop()  # Stop recording flow
    stream.close()  # Close recording stream
    audio_data = np.concatenate(audio_frames, axis=0)
    # Save audio data as wav file
    wavio.write('output.wav', audio_data, 44100, sampwidth=2)

    return jsonify(success=True)






if __name__ == '__main__':
    app.run(debug=True)
