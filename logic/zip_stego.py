import os
import zipfile
import shutil
import base64

# This variable name must match exactly in both encode and decode
SECRET_VAR = "API_KEY_CACHE"

def encode_zip(message, target_dir):
    """
    Hides the message in a main.py file within a ZIP archive, 
    stored in the user-specified target_dir.
    """
    # The final zip will be named 'secret_bundle.zip' inside the custom folder
    zip_path = os.path.join(target_dir, "secret_bundle.zip")
    
    # 1. Base64 "Armor" - turns the message into a single safe string
    msg_bytes = message.encode('utf-8')
    safe_string = base64.b64encode(msg_bytes).decode('ascii')

    # 2. Create the Python content payload
    py_content = f"""# System Config
import os

{SECRET_VAR} = "{safe_string}"

def start_server():
    return True
"""
    
    # 3. Create a temporary main.py file inside the target directory
    temp_py_path = os.path.join(target_dir, "main.py")
    with open(temp_py_path, "w") as f:
        f.write(py_content)

    # 4. Create the Zip Archive and add the main.py file to it
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 'arcname' ensures that when unzipped, it doesn't contain the full folder path
        zipf.write(temp_py_path, arcname="main.py")

    # 5. Cleanup the temporary main.py (it's safely tucked inside the zip now)
    if os.path.exists(temp_py_path):
        os.remove(temp_py_path)
        
    return zip_path

def decode_zip(zip_file_path):
    """
    Extracts the hidden base64 string from main.py inside the ZIP 
    and converts it back to plain text.
    """
    try:
        if not os.path.exists(zip_file_path):
            return "Error: Zip file not found."

        with zipfile.ZipFile(zip_file_path, 'r') as z:
            # Check if our carrier file exists inside the archive
            if "main.py" not in z.namelist():
                return "Error: main.py missing inside the zip archive."
            
            # Read the file content without extracting it to disk
            with z.open("main.py") as f:
                content = f.read().decode("utf-8")
                
            # Parse line by line to find our secret variable
            for line in content.splitlines():
                if line.startswith(SECRET_VAR):
                    # Split the line by double quotes to get the value inside
                    parts = line.split('"')
                    if len(parts) >= 2:
                        encoded_val = parts[1]
                        # Decode from Base64 back to original UTF-8 text
                        return base64.b64decode(encoded_val).decode('utf-8')
                        
        return "Error: Hidden variable 'API_KEY_CACHE' not found in source."
    except Exception as e:
        return f"Zip Logic Error: {str(e)}"