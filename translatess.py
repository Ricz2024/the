from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
import requests
import datetime

class LanguageTranslator(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        
        # Header
        header = Label(text="Language Translator", font_size='44sp', size_hint=(1, None), height='50sp')
        layout.add_widget(header)

        # Date and Time
        self.datetime_label = Label(text='', font_size='22sp')
        layout.add_widget(self.datetime_label)
        self.update_datetime()

        # Error message
        self.error_label = Label(font_size='20sp', color=(1, 0, 0, 1))
        layout.add_widget(self.error_label)

        # Text input
        self.source_text = TextInput(text='', font_size='20sp', size_hint=(1, None), height='250sp')
        layout.add_widget(self.source_text)

        # Language selection
        self.languages_spinner = Spinner(text='Select Language', values=('bisaya', 'sinama'), size_hint=(1, None), height='48sp')
        layout.add_widget(self.languages_spinner)

        # Translate button
        self.translate_button = Button(text='Translate', size_hint=(1, None), height='48sp')
        self.translate_button.bind(on_press=self.translate_text)
        layout.add_widget(self.translate_button)

        # Record button
        self.record_button = Button(text='Record', size_hint=(0.5, None), height='48sp')
        self.record_button.bind(on_press=self.start_recording)
        layout.add_widget(self.record_button)

        # Stop recording button
        self.stop_button = Button(text='Stop', size_hint=(0.5, None), height='48sp', disabled=True)
        self.stop_button.bind(on_press=self.stop_recording)
        layout.add_widget(self.stop_button)

        # Translated text
        self.translated_text = TextInput(text='', font_size='20sp', size_hint=(1, None), height='250sp')
        layout.add_widget(self.translated_text)

        return layout

    def update_datetime(self, *args):
        now = datetime.datetime.now()
        self.datetime_label.text = now.strftime("%Y-%m-%d %H:%M:%S")

    def start_recording(self, instance):
        self.record_button.disabled = True
        self.stop_button.disabled = False
        # Send request to start recording
        response = requests.post('http://127.0.0.1:5000/start-recording')
        if response.status_code == 200:
            print("Recording started")
        else:
            print("Failed to start recording")

    def stop_recording(self, instance):
        self.record_button.disabled = False
        self.stop_button.disabled = True
        # Send request to stop recording
        response = requests.post('http://127.0.0.1:5000/stop-recording')
        if response.status_code == 200:
            print("Recording stopped")
            # After recording stopped, send request to translate the audio
            self.translate_audio()
        else:
            print("Failed to stop recording")

    def translate_audio(self):
        # Send request to Flask API for translation
        sourcetext = self.source_text.text.strip()
        languages = self.languages_spinner.text
        response = requests.post('http://127.0.0.1:5000/translate', data={'languages': languages})
        if response.status_code == 200:
            translated_text = response.json().get('result')
            self.translated_text.text = translated_text
        else:
            print("Failed to translate audio")

    def translate_text(self, instance):
        self.translate_audio()

if __name__ == '__main__':
    LanguageTranslator().run()
