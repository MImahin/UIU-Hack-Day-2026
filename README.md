# GHOSTVECTOR: Distributed Stealth Architecture
### **Multi-Vector Steganography Suite**
**Developed for UIU Hackday 2026** **Team Name: KALA BHUNA**

---

## 🛠️ Overview
GhostVector is a high-security steganography application designed to hide sensitive information by fragmenting it across three different digital mediums (Vectors). Unlike standard encryption, GhostVector focuses on **deniability** and **invisibility**. By splitting a secret into three parts, the message remains unrecoverable even if one or two files are intercepted.

---

## 🛡️ The Triple-Vector Logic
The system automatically splits the input message into three mathematically equal fragments and embeds them into the following:

### 1. Visual Vector (Image)
* **Method:** LSB (Least Significant Bit) Steganography.
* **Logic:** Data is injected into the noise of a PNG image, altering the color values so slightly that the human eye cannot detect the change.

### 2. Acoustic Vector (Audio)
* **Method:** High-Frequency Morse Encoding.
* **Logic:** The message is converted to Morse code and modulated onto a **20,000Hz (Ultrasonic)** carrier wave, then mixed with a cover music track. It is audible to machines but invisible to humans.

### 3. Archive Vector (Source Code)
* **Method:** Comment-Injection & Whitespace Steganography.
* **Logic:** Data is hidden within non-functional segments of a ZIP archive containing source code.

---

## 🚀 Installation & Usage

### 1. Prerequisites
Ensure you have Python 3.9+ installed.
```bash
pip install -r requirements.txt
