import whisper
import numpy as np

# Charger le modèle (tiny/base/small/medium/large selon précision/vitesse)
model = whisper.load_model("small")


def _resample(audio_data: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    """Resample le flux audio si le navigateur n'est pas à 16 kHz."""
    if from_rate == to_rate:
        return audio_data
    duration = len(audio_data) / float(from_rate)
    target_length = int(duration * to_rate)
    # Interpolation linéaire simple pour rester léger côté serveur
    return np.interp(
        np.linspace(0, len(audio_data), target_length, endpoint=False),
        np.arange(len(audio_data)),
        audio_data
    ).astype(np.float32)


def transcribe_chunk(audio_chunk, sample_rate=16000):
    """
    Transcrit un morceau audio reçu du navigateur.
    audio_chunk : np.array
    sample_rate : fréquence d'échantillonnage
    """
    audio_data = audio_chunk.flatten().astype(np.float32)

    if len(audio_data) == 0 or audio_data.size == 0:
        return []

    if np.abs(audio_data).max() < 0.001:
        return []

    if audio_data.max() > 1.0 or audio_data.min() < -1.0:
        audio_data = audio_data / np.abs(audio_data).max()

    audio_data = _resample(audio_data, sample_rate, 16000)
    sample_rate = 16000

    min_samples = int(0.1 * sample_rate)
    if len(audio_data) < min_samples:
        audio_data = np.pad(audio_data, (0, min_samples - len(audio_data)), mode='constant')

    try:
        result = model.transcribe(audio_data, fp16=False, language="fr")
        return result["segments"]
    except Exception as e:
        print(f"Erreur Whisper: {e}")
        return []


if __name__ == "__main__":
    result = model.transcribe("audio_long.mp3")
    for seg in result["segments"]:
        print(seg["start"], seg["end"], seg["text"])
