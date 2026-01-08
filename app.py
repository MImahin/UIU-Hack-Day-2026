from flask import Flask, render_template, request, send_from_directory
import os
import math
import shutil
# Import the custom steganography modules
from logic import image_stego, audio_stego, zip_stego

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def split_text_into_three(text):
    """
    Splits the input string into 3 roughly equal fragments.
    """
    length = len(text)
    if length == 0:
        return ["", "", ""]
    
    # Calculate partition points
    size = math.ceil(length / 3)
    parts = [text[i:i + size] for i in range(0, length, size)]
    
    # Ensure we always return exactly 3 parts (pad with empty strings if text is very short)
    while len(parts) < 3:
        parts.append("")
    return parts[:3]

# --- ROUTES ---

@app.route('/')
def index():
    """Main landing page."""
    return render_template('index.html')

@app.route('/encode', methods=['GET', 'POST'])
def encode():
    """Handles splitting the message and generating the 3 stego files."""
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        folder_name = request.form.get('folder_name', 'secret_session').strip()
        
        if not message or not folder_name:
            return render_template('encode.html', error="Both message and folder name are required.")

        # 1. Split the message into 3 fragments
        fragments = split_text_into_three(message)

        # 2. Create the target subfolder in uploads
        target_dir = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(target_dir, exist_ok=True)

        # 3. Define the file paths
        img_path = os.path.join(target_dir, "part1_image.png")
        aud_path = os.path.join(target_dir, "part2_audio.wav")
        # Zip logic handles its own internal naming but we need the target dir
        
        # 4. Run the Encoders with their respective fragments
        try:
            # Fragment 1 -> Image
            image_stego.encode_image(fragments[0], img_path)
            
            # Fragment 2 -> Audio
            audio_stego.encode_audio(fragments[1], aud_path)
            
            # Fragment 3 -> Zip
            zip_path_full = zip_stego.encode_zip(fragments[2], target_dir)
            zip_filename = os.path.basename(zip_path_full)

            # Pass the relative paths (folder/file) to the result page for downloads
            return render_template('result.html', 
                                 folder=folder_name,
                                 img_file=f"{folder_name}/part1_image.png", 
                                 aud_file=f"{folder_name}/part2_audio.wav", 
                                 zip_file=f"{folder_name}/{zip_filename}")
        
        except Exception as e:
            return render_template('encode.html', error=f"Encoding failed: {str(e)}")

    return render_template('encode.html')

@app.route('/decode', methods=['GET', 'POST'])
def decode():
    """Handles reassembling fragments from uploaded files."""
    if request.method == 'POST':
        # Retrieve the 3 specific file inputs
        img_f = request.files.get('img_file')
        aud_f = request.files.get('aud_file')
        zip_f = request.files.get('zip_file')

        # We will store the extracted fragments here
        fragments = ["", "", ""]

        # Decode Part 1 (Image)
        if img_f and img_f.filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_dec_img.png")
            img_f.save(path)
            fragments[0] = image_stego.decode_image(path)
            os.remove(path)

        # Decode Part 2 (Audio)
        if aud_f and aud_f.filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_dec_aud.wav")
            aud_f.save(path)
            fragments[1] = audio_stego.decode_audio(path)
            os.remove(path)

        # Decode Part 3 (Zip)
        if zip_f and zip_f.filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_dec_zip.zip")
            zip_f.save(path)
            fragments[2] = zip_stego.decode_zip(path)
            os.remove(path)

        # Reassemble the final message
        full_message = "".join(fragments)
        
        return render_template('decode.html', 
                             merged_result=full_message, 
                             parts=fragments)

    return render_template('decode.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    """Securely serves the generated files from the uploads subfolders."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    # Running on port 5000 with debug mode for development
    app.run(debug=True, port=5000)