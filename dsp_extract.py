import librosa
import numpy as np

AUDIO_DIR = "audio"

tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
tempo = float(np.atleast_1d(tempo)[0])

chromagram = librosa.feature.chroma_cqt(y=y, sr=sr)
chroma_mean = chromagram.mean(axis=1)
pitch_classes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
root_note = pitch_classes[np.argmax(chroma_mean)]

minor_profile = np.roll(np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]), np.argmax(chroma_mean))
major_profile = np.roll(np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]), np.argmax(chroma_mean))
is_minor = np.dot(chroma_mean, minor_profile) < np.dot(chroma_mean, major_profile)
key = f"{root_note} {'minor' if is_minor else 'major'}"

rms = librosa.feature.rms(y=y)
rms_mean = float(rms.mean())

print(f"Tempo    : {tempo:.2f} BPM")
print(f"Key      : {key}")
print(f"RMS Energy: {rms_mean:.6f}")