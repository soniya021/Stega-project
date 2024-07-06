import os
import shutil
from PIL import Image
import stepic
import sqlite3
from flask import Blueprint, current_app, render_template, request, flash
from werkzeug.utils import secure_filename

image = Blueprint("image", __name__, static_folder="static", template_folder="templates")

@image.route("/encode")
def image_encode():
    if os.path.exists(current_app.config['IMAGE_CACHE_FOLDER']):
        shutil.rmtree(current_app.config['IMAGE_CACHE_FOLDER'], ignore_errors=False)
    else:
        print("Not Found")

    if os.path.exists(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "encrypted_image.png")):
        os.remove(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "encrypted_image.png"))
    else:
        print("Not found")
    return render_template("encode-image.html")

@image.route("/encode-result", methods=['POST', 'GET'])
def image_encode_result():
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
            file.save(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], filename))
            image_encryption = True
            encrypted_image_path = encrypt_image(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], filename), message)
            save_image_to_db(filename, encrypted_image_path, message)
        else:
            image_encryption = False
        result = request.form

        return render_template("encode-image-result.html", result=result, file=file, image_encryption=image_encryption, message=message)

@image.route("/decode")
def image_decode():
    return render_template("decode-image.html")

@image.route("/decode-result", methods=['POST', 'GET'])
def image_decode_result():
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
            file.save(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], filename))
            image_decryption = True
            message = decrypt_image(os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], filename))
        else:
            image_decryption = False
        result = request.form
        return render_template("decode-image-result.html", result=result, file=file, image_decryption=image_decryption, message=message)

def encrypt_image(image_path, message):
    im = Image.open(image_path)
    im1 = stepic.encode(im, bytes(str(message), encoding='utf-8'))
    encrypted_image_path = os.path.join(current_app.config['UPLOAD_IMAGE_FOLDER'], "encrypted_image.png")
    im1.save(encrypted_image_path)
    return encrypted_image_path

def decrypt_image(image_path):
    im2 = Image.open(image_path)
    stegoImage = stepic.decode(im2)
    return stegoImage

def save_image_to_db(original_filename, encrypted_image_path, message):
    conn = sqlite3.connect('steganography.db')
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO images (original_filename, encrypted_image_path, message)
    VALUES (?, ?, ?)
    """, (original_filename, encrypted_image_path, message))
    conn.commit()
    conn.close()
