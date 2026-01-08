import numpy as np
from scipy.io import wavfile
from scipy import signal
import os
import random

# CONFIG
HIDDEN_FREQ = 20000  # Set to 20kHz (Near ultrasonic, invisible but recordable)
SAMPLE_RATE = 44100
UNIT_TIME = 0.06
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_LIB_PATH = os.path.join(BASE_DIR, 'uploads', 'music')

MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '1': '.----', '2': '..---', '3': '...--', 
    '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..', 
    '9': '----.', '0': '-----', '.': '.-.-.-', ',': '--..--', '?': '..--..', 
    "'": '.----.', '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-', 
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-', '+': '.-.-.', 
    '-': '-....-', '_': '..--.-', '"': '.-..-.', '$': '...-..-', '@': '.--.-.', ' ': '/'
}

def get_random_cover():
    """Selects a random wav file from the music directory."""
    try:
        files = [f for f in os.listdir(MUSIC_LIB_PATH) if f.endswith('.wav')]
        if not files:
            return None
        return os.path.join(MUSIC_LIB_PATH, random.choice(files))
    except:
        return None

def encode_audio(message, output_path):
    text = message.upper()
    
    # 1. Create Morse Signal
    t = np.arange(int(UNIT_TIME * SAMPLE_RATE)) / SAMPLE_RATE
    tone = np.sin(2 * np.pi * HIDDEN_FREQ * t)
    silence = np.zeros(len(tone))
    
    audio_seq = []
    for char in text:
        if char in MORSE_CODE_DICT:
            code = MORSE_CODE_DICT[char]
            for s in code:
                if s == '.': audio_seq.extend([tone, silence])
                elif s == '-': audio_seq.extend([np.tile(tone, 3), silence])
            audio_seq.extend([silence, silence])
        elif char == ' ':
            audio_seq.extend([silence] * 6)

    if not audio_seq:
        secret_signal = np.zeros(SAMPLE_RATE)
    else:
        secret_signal = np.concatenate(audio_seq)

    # 2. Load Cover Music
    cover_file = get_random_cover()
    if cover_file:
        fs, cover_data = wavfile.read(cover_file)
        # Convert to mono if stereo
        if len(cover_data.shape) > 1:
            cover_data = cover_data[:, 0]
        # Normalize cover
        cover_data = cover_data.astype(np.float32) / 32768.0
    else:
        # Fallback to silence if no music found
        cover_data = np.zeros(max(SAMPLE_RATE * 5, len(secret_signal)))

    # 3. Mixing
    # Ensure cover is long enough
    if len(cover_data) < len(secret_signal):
        padding = np.zeros(len(secret_signal) - len(cover_data))
        cover_data = np.concatenate([cover_data, padding])
    
    # Embed secret into cover
    mixed = cover_data.copy()
    # Add secret signal at a low volume to the cover
    mixed[:len(secret_signal)] += secret_signal * 0.15 
    
    # Final Normalization to prevent clipping
    mixed = mixed / np.max(np.abs(mixed))
    
    wavfile.write(output_path, SAMPLE_RATE, (mixed * 32767).astype(np.int16))
    return output_path

def decode_audio(audio_path):
    try:
        sr, data = wavfile.read(audio_path)
        data = data.astype(np.float32) / 32767.0
        if len(data.shape) > 1: data = data[:, 0]

        # Bandpass Filter to isolate the HIDDEN_FREQ
        nyq = 0.5 * sr
        low = (HIDDEN_FREQ - 400) / nyq
        high = (HIDDEN_FREQ + 400) / nyq
        b, a = signal.butter(5, [low, high], btype='band')
        filtered = signal.lfilter(b, a, data)
        
        # Envelope detection
        smoothed = np.convolve(np.abs(filtered), np.ones(int(sr * 0.01))/(sr * 0.01), mode='same')
        
        # Binary thresholding
        peak = np.percentile(smoothed, 95)
        is_beep = smoothed > (peak * 0.5)

        # Parse Durations
        changes = np.flatnonzero(np.diff(is_beep.astype(np.int8)))
        durations = np.diff(np.concatenate(([0], changes, [len(is_beep)])))
        
        if len(durations) < 2: return ""

        # Logic to extract Morse
        beeps = durations[0::2] if is_beep[0] else durations[1::2]
        if len(beeps) == 0: return ""
        
        dot_len = np.median(beeps)
        morse_str = ""
        start = 0 if is_beep[0] else 1
        
        for i in range(start, len(durations), 2):
            d = durations[i]
            sil = durations[i+1] if i+1 < len(durations) else 0
            morse_str += "-" if d > dot_len * 2 else "."
            if sil > dot_len * 5: morse_str += " / "
            elif sil > dot_len * 2: morse_str += " "
            
        reverse_dict = {v: k for k, v in MORSE_CODE_DICT.items()}
        decoded = []
        for word in morse_str.split(' / '):
            chars = "".join([reverse_dict.get(c, '') for c in word.split(' ')])
            decoded.append(chars)
            
        return " ".join(decoded).strip()

    except Exception as e:
        return f"Decode Error: {str(e)}"