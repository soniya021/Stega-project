import os
import shutil
from PIL import Image
import stepic
import sqlite3
from flask import Blueprint, current_app, render_template, request, flash
from werkzeug.utils import secure_filename

text = Blueprint("text", __name__, static_folder="static", template_folder="templates")

@text.route("/encode")
def text_encode():
    if os.path.exists(current_app.config['TEXT_CACHE_FOLDER']):
        shutil.rmtree(current_app.config['TEXT_CACHE_FOLDER'], ignore_errors=False)
    else:
        print("Not Found")

    if os.path.exists(os.path.join(current_app.config['UPLOAD_TEXT_FOLDER'], "encrypted_text_image.png")):
        os.remove(os.path.join(current_app.config['UPLOAD_TEXT_FOLDER'], "encrypted_text_image.png"))
    else:
        print("Not found")
    return render_template("encode-text.html")

@text.route("/encode-result", methods=['POST', 'GET'])
def text_encode_result():
    if request.method == 'POST':
        message = request.form['message']
        if 'image' not in request.files:
            flash('No image found')
            return redirect(request.url)
        file = request.files['image']

        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_TEXT_FOLDER'], filename))
            text_encryption = True
            encrypted_image_path = encrypt_text(os.path.join(current_app.config['UPLOAD_TEXT_FOLDER'], filename), message)
            save_text_to_db(filename, encrypted_image_path, message)
        else:
            text_encryption = False
        result = request.form

        return render_template("encode-text-result.html", result=result, file=file, text_encryption=text_encryption, message=message)

@text.route("/decode")
def text_decode():
    return render_template("decode-text.html")

@text.route("/decode-result", methods=['POST', 'GET'])
def text_decode_result():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image found')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_TEXT_FOLDER'], filename))
            text_decryption = True
            message = decrypt_text(os.path.join(current_app.config['UPLOAD_TEXT_FOLDER'], filename))
        else:
            text_decryption = False
        result = request.form
        return render_template("decode-text-result.html", result=result, file=file, text_decryption=text_decryption, message=message)

def encrypt_text(image_path, message):
    im = Image.open(image_path)
    im1 = stepic.encode(im, bytes(str(message), encoding='utf-8'))
    encrypted_image_path = os.path.join(current_app.config['UPLOAD_TEXT_FOLDER'], "encrypted_text_image.png")
    im1.save(encrypted_image_path)
    return encrypted_image_path

def decrypt_text(image_path):
    im2 = Image.open(image_path)
    stegoImage = stepic.decode(im2)
    return stegoImage

def save_text_to_db(original_filename, encrypted_image_path, message):
    conn = sqlite3.connect('steganography.db')
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO images (original_filename, encrypted_image_path, message)
    VALUES (?, ?, ?)
    """, (original_filename, encrypted_image_path, message))
    conn.commit()
    conn.close()
