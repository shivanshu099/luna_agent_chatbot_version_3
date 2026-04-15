import whisper
import sounddevice as sd
import numpy as np


class Listener:
    def __init__(self, model_name="base", sample_rate=16000):
        print("🔧 Initializing Listener...")
        
        self.model = whisper.load_model(model_name)
        self.fs = sample_rate
        self.audio_frames = []
        self.is_recording = False
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if self.is_recording:
            self.audio_frames.append(indata.copy())

    def start_recording(self):
        if self.is_recording:
            print("⚠️ Already recording")
            return

        print("🎤 Recording started...")
        self.audio_frames = []
        self.is_recording = True

        self.stream = sd.InputStream(
            samplerate=self.fs,
            channels=1,
            callback=self._callback
        )
        self.stream.start()

    def stop_recording(self):
        if not self.is_recording:
            print("⚠️ Not recording")
            return None

        self.is_recording = False

        self.stream.stop()
        self.stream.close()

        print("🛑 Recording stopped. Processing...")

        if len(self.audio_frames) == 0:
            print("❌ No audio recorded")
            return None

        # Convert to numpy array
        audio_data = np.concatenate(self.audio_frames, axis=0).flatten()

        # Transcribe
        result = self.model.transcribe(audio_data)
        text = result["text"].strip()

        print(f"✅ You said: {text}")
        return text


"""
if __name__ == "__main__":
    import time

    listener = Listener()

    print("\n=== 5-Second Auto Speech Test ===")
    print("🎤 Speak after it starts recording...\n")

    while True:
        # Start recording
        listener.start_recording()

        # Record for 10 seconds
        time.sleep(10)

        # Stop and process
        text = listener.stop_recording()

        if text:
            print("🎯 Final Output:", text)
        else:
            print("⚠️ No valid speech detected")

        print("\n⏳ Next recording starts in 2 seconds...\n")
        time.sleep(2)

"""
from kokoro import KPipeline
import sounddevice as sd
from scipy.io.wavfile import read
import soundfile as sf
import tempfile


class KokoroTTS:
    def __init__(self):
        print("🔧 Initializing Kokoro TTS...")
        self.pipeline = KPipeline(lang_code='a')

    def speak(self, text):
        print(f"🗣️ Speaking: {text}")

        # Generate audio
        generator = self.pipeline(text, voice='af_heart')

        for i, (gs, ps, audio) in enumerate(generator):
            # Save temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf.write(f.name, audio, 24000)

                # Play audio
                fs, data = read(f.name)
                sd.play(data, fs)
                sd.wait()


if __name__ == "__main__":
    tts = KokoroTTS()

    text = input("Enter text: ")
    tts.speak(text)













