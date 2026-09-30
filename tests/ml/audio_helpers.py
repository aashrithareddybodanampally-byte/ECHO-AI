import io

import numpy as np
import soundfile as sf


def tone(freq=440.0, seconds=1.0, sr=16000, amplitude=0.5):
    t = np.arange(int(seconds * sr)) / sr
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def encode(samples, sr, fmt="WAV") -> bytes:
    buffer = io.BytesIO()
    sf.write(buffer, samples, sr, format=fmt)
    return buffer.getvalue()


def peak_frequency(samples, sr) -> float:
    spectrum = np.abs(np.fft.rfft(samples))
    return float(np.fft.rfftfreq(samples.size, 1 / sr)[np.argmax(spectrum)])
