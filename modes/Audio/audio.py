import os
import shutil
import wave
import sqlite3
from flask import Blueprint, current_app, render_template, request, flash
from werkzeug.utils import secure_filename

audio = Blueprint("audio", __name__, static_folder="static", template_folder="templates")

@audio.route("/encode")
def audio_encode():
    return render_template("encode-audio.html")

@audio.route("/encode-result", methods=['POST', 'GET'])
def audio_encode_result():
    if request.method == 'POST':
        message = request.form['message']
        if 'audio' not in request.files:
            flash('No audio found')
            return redirect(request.url)
        file = request.files['audio']

        if file.filename == '':
            flash('No audio selected')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_AUDIO_FOLDER'], filename))
            audio_encryption = True
            encrypted_audio_path = encrypt_audio(os.path.join(current_app.config['UPLOAD_AUDIO_FOLDER'], filename), message)
            save_audio_to_db(filename, encrypted_audio_path, message)
        else:
            audio_encryption = False
        result = request.form

        return render_template("encode-audio-result.html", result=result, file=file, audio_encryption=audio_encryption, message=message)

@audio.route("/decode")
def audio_decode():
    return render_template("decode-audio.html")

@audio.route("/decode-result", methods=['POST', 'GET'])
def audio_decode_result():
    if request.method == 'POST':
        if 'audio' not in request.files:
            flash('No audio found')
            return redirect(request.url)
        file = request.files['audio']
        if file.filename == '':
            flash('No audio selected')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_AUDIO_FOLDER'], filename))
            audio_decryption = True
            message = decrypt_audio(os.path.join(current_app.config['UPLOAD_AUDIO_FOLDER'], filename))
        else:
            audio_decryption = False
        result = request.form
        return render_template("decode-audio-result.html", result=result, file=file, audio_decryption=audio_decryption, message=message)

def encrypt_audio(audio_path, message):
    song = wave.open(audio_path, mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    string = str(message)
    string = string + int((len(frame_bytes)-(len(string)*8*8))/8) * '#'
    bits = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in string])))

    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | bit

    frame_modified = bytes(frame_bytes)

    encrypted_audio_path = os.path.join(current_app.config['UPLOAD_AUDIO_FOLDER'], "song_embedded.wav")
    with wave.open(encrypted_audio_path, 'wb') as fd:
        fd.setparams(song.getparams())
        fd.writeframes(frame_modified)
    song.close()
    return encrypted_audio_path

def decrypt_audio(audio_path):
    song = wave.open(audio_path, mode='rb')
    frame_bytes = bytearray(list(song.readframes(song.getnframes())))

    extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
    string = "".join(chr(int("".join(map(str, extracted[i:i+8])), 2)) for i in range(0, len(extracted), 8))
    decoded = string.split("###")[0]

    song.close()
    return decoded

def save_audio_to_db(original_filename, encrypted_audio_path, message):
    conn = sqlite3.connect('steganography.db')
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO audios (original_filename, encrypted_audio_path, message)
    VALUES (?, ?, ?)
    """, (original_filename, encrypted_audio_path, message))
    conn.commit()
    conn.close()
