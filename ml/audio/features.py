"""
Audio feature extraction.

Produces a fixed-length vector from preprocessed mono audio:

    MFCC (40)            mean + std  -> 80
    Chroma (12)          mean        -> 12
    Spectral centroid    mean + std  ->  2
    Spectral bandwidth   mean + std  ->  2
    Zero-crossing rate   mean + std  ->  2
    RMS energy           mean + std  ->  2
                                       ---
                                       100
"""

import numpy as np
import librosa

FEATURE_VERSION = "mfcc40-chroma-spectral-zcr-rms-v1"
N_MFCC = 40
FEATURE_NAMES = (
    [f"mfcc{i}_mean" for i in range(N_MFCC)]
    + [f"mfcc{i}_std" for i in range(N_MFCC)]
    + [f"chroma{i}_mean" for i in range(12)]
    + [
        "centroid_mean", "centroid_std",
        "bandwidth_mean", "bandwidth_std",
        "zcr_mean", "zcr_std",
        "rms_mean", "rms_std",
    ]
)
FEATURE_DIM = len(FEATURE_NAMES)

_N_FFT = 512
_HOP = 160  # 10 ms at 16 kHz


def extract_features(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    """Return a float32 vector of length FEATURE_DIM."""
    if samples.ndim != 1 or samples.size < _N_FFT:
        raise ValueError(f"Expected 1-D audio with at least {_N_FFT} samples")
    y = samples.astype(np.float32)
    kwargs = {"n_fft": _N_FFT, "hop_length": _HOP}

    mfcc = librosa.feature.mfcc(y=y, sr=sample_rate, n_mfcc=N_MFCC, **kwargs)
    stft = np.abs(librosa.stft(y, **kwargs))
    chroma = librosa.feature.chroma_stft(S=stft**2, sr=sample_rate)
    centroid = librosa.feature.spectral_centroid(S=stft, sr=sample_rate)
    bandwidth = librosa.feature.spectral_bandwidth(S=stft, sr=sample_rate)
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=_N_FFT, hop_length=_HOP)
    rms = librosa.feature.rms(S=stft, frame_length=_N_FFT, hop_length=_HOP)

    vector = np.concatenate([
        mfcc.mean(axis=1),
        mfcc.std(axis=1),
        chroma.mean(axis=1),
        [centroid.mean(), centroid.std()],
        [bandwidth.mean(), bandwidth.std()],
        [zcr.mean(), zcr.std()],
        [rms.mean(), rms.std()],
    ]).astype(np.float32)
    if not np.all(np.isfinite(vector)):
        raise ValueError("Feature extraction produced non-finite values")
    return vector
