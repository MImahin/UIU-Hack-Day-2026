import numpy as np
from PIL import Image
import requests
import io
import os

# CONFIG
SEED = 0.523456
R_VALUE = 3.99
IMG_SIZE = (800, 600)
STOP_MARKER = "###"

def generate_chaotic_sequence(length):
    sequence = np.zeros(length, dtype=np.float32)
    x = SEED
    for i in range(length):
        x = R_VALUE * x * (1 - x)
        sequence[i] = x
    return np.argsort(sequence)

def encode_image(message, output_path):
    # Sanitize and Prepare
    msg = message.encode("ascii", "ignore").decode("ascii")
    data = msg + STOP_MARKER
    bits = [int(b) for char in data for b in bin(ord(char)).lstrip('0b').zfill(8)]

    # Fetch Carrier
    try:
        r = requests.get(f"https://picsum.photos/{IMG_SIZE[0]}/{IMG_SIZE[1]}", timeout=3)
        img = Image.open(io.BytesIO(r.content)).convert('RGB')
    except:
        # Fallback to noise if offline
        img = Image.fromarray(np.random.randint(0, 255, (IMG_SIZE[1], IMG_SIZE[0], 3), dtype=np.uint8))

    pixels = np.array(img.resize(IMG_SIZE))
    flat = pixels.flatten()

    if len(bits) > len(flat):
        raise ValueError("Message too long for this image size.")

    indices = generate_chaotic_sequence(len(flat))
    
    # Embed
    for i, bit in enumerate(bits):
        idx = indices[i]
        flat[idx] = (flat[idx] & 254) | bit

    # Save
    Image.fromarray(flat.reshape(pixels.shape).astype(np.uint8)).save(output_path, "PNG")
    return output_path

def decode_image(image_path):
    img = Image.open(image_path).convert('RGB').resize(IMG_SIZE)
    flat = np.array(img).flatten()
    indices = generate_chaotic_sequence(len(flat))

    extracted_bits = []
    current_str = ""
    
    # Optimize: Process in chunks of 8 to detect marker early
    for i in range(len(flat)):
        idx = indices[i]
        extracted_bits.append(flat[idx] & 1)

        if len(extracted_bits) % 8 == 0:
            byte_val = int(''.join(map(str, extracted_bits[-8:])), 2)
            current_str += chr(byte_val)
            
            if current_str.endswith(STOP_MARKER):
                return current_str[:-len(STOP_MARKER)]
    
    return "No hidden message found (or marker corrupted)."