import whisper
import logging
import os
import subprocess
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
# Load model once globally
whisper_model = whisper.load_model("small")  # "tiny", "base", "small", "medium", "large"


def convert_to_wav(input_path: str) -> str:
    """Convert input audio file to 16kHz mono wav for Whisper."""
    output_path = os.path.splitext(input_path)[0] + ".wav"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return output_path
    except subprocess.CalledProcessError as e:
        logging.error(f"ffmpeg conversion failed: {e}")
        return input_path  # fallback: try original


def convert_audio_to_text(audio_path: str) -> str:
    try:
        wav_path = convert_to_wav(audio_path)
        result = whisper_model.transcribe(wav_path, fp16=False)
        return result.get("text", "")
    except Exception as e:
        logging.info(f"Error converting audio to text: {e}")
        return ""