import os
import shutil
import sqlite3
from stegano import lsb
import math
import cv2
from flask import Blueprint, render_template, current_app, request, flash
from werkzeug.utils import secure_filename

video = Blueprint("video", __name__, static_folder="static", template_folder="templates")

@video.route("/encode")
def video_encode():
    return render_template("encode-video.html")

@video.route("/encode-result", methods=['POST', 'GET'])
def video_encode_result():
    if request.method == 'POST':
        message = request.form['message']
        if 'video' not in request.files:
            flash('No video found')
            return redirect(request.url)
        file = request.files['video']
        if file.filename == '':
            flash('No selected video')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_VIDEO_FOLDER'], filename))
            encryption = True
            encrypted_video_path = encrypt(os.path.join(current_app.config['UPLOAD_VIDEO_FOLDER'], filename), message)
            save_video_to_db(filename, encrypted_video_path, message)
        else:
            encryption = False
        result = request.form
        return render_template("encode-video-result.html", message=message, result=result, file=file, encryption=encryption)

@video.route("/decode")
def video_decode():
    return render_template("decode-video.html")

@video.route("/decode-result", methods=['POST', 'GET'])
def video_decode_result():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video found')
            return redirect(request.url)
        file = request.files['video']
        if file.filename == '':
            flash('No selected video')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_VIDEO_FOLDER'], filename))
            decryption = True
            decrypted_text = decrypt(os.path.join(current_app.config['UPLOAD_VIDEO_FOLDER'], filename))
        else:
            decryption = False
        result = request.form
        return render_template("decode-video-result.html", result=result, decrypted_text=decrypted_text, file=file, decryption=decryption)

def encrypt(f_name, input_string):
    frame_extraction(f_name)
    path = "C:\ffmpeg\bin\ffmpeg.exe" # Update this path to the location of ffmpeg

    encode_string(input_string)
    sec_command = f"{path} -i tmp/%d.png -vcodec png {os.path.join(current_app.config['UPLOAD_VIDEO_FOLDER'], 'enc-video.mp4')} -y"
    os.system(sec_command)

    encrypted_video_path = os.path.join(current_app.config['UPLOAD_VIDEO_FOLDER'], 'enc-video.mp4')
    return encrypted_video_path

def split_string(s_str, count=10):
    per_c = math.ceil(len(s_str) / count)
    c_count = 0
    out_str = ''
    split_list = []
    for s in s_str:
        out_str += s
        c_count += 1
        if c_count == per_c:
            split_list.append(out_str)
            out_str = ''
            c_count = 0
    if c_count != 0:
        split_list.append(out_str)
    return split_list

def frame_extraction(video):
    if not os.path.exists("./tmp"):
        os.makedirs("tmp")
    temp_folder = "./tmp"

    vidcap = cv2.VideoCapture(video)
    count = 0
    while True:
        success, image = vidcap.read()
        if not success:
            break
        cv2.imwrite(os.path.join(temp_folder, "{:d}.png".format(count)), image)
        count += 1

def encode_string(input_string, root="./tmp/"):
    split_string_list = split_string(input_string)
    for i in range(len(split_string_list)):
        f_name = "{}{}.png".format(root, i)
        secret_enc = lsb.hide(f_name, split_string_list[i])
        secret_enc.save(f_name)

def decrypt(video):
    frame_extraction(video)
    secret = []
    root = "./tmp/"
    for i in range(len(os.listdir(root))):
        f_name = "{}{}.png".format(root, i)
        secret_dec = lsb.reveal(f_name)
        if secret_dec is None:
            break
        secret.append(secret_dec)
    result = ''.join(secret)
    clean_tmp()
    return result

def clean_tmp(path="./tmp"):
    if os.path.exists(path):
        shutil.rmtree(path)

def save_video_to_db(original_filename, encrypted_video_path, message):
    conn = sqlite3.connect('steganography.db')
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO videos (original_filename, encrypted_video_path, message)
    VALUES (?, ?, ?)
    """, (original_filename, encrypted_video_path, message))
    conn.commit()
    conn.close()
