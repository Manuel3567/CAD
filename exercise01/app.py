from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.


import os
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './media'
USER = 'postgres'
PASSWORD = os.environ.get('DATABASE_PASSWORD')
HOST = '127.0.0.1'
PORT = '5432'
DATABASE_NAME = 'file_uploader'

DATABASE = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE_NAME}'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'py'}
EXTENSION_LOGICAL_MAP = {'txt': 'Document', 'pdf': 'Document', 'png': 'Picture', 'jpg': 'Picture', 'jpeg': 'Picture', 'gif': 'Video', 'mp4': 'Video'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATABASE'] = DATABASE

import db
db.init_app(app)

@app.route("/", methods = ["GET"])
def index():
    search_results = request.args.getlist('results')

    results = []

    if search_results:
        for search_result in search_results:
            sql = f"""
            select file.name, file.type, file.creation_date, file.description from file where file.name = '{search_result}'
            """
            file_details = db.execute(sql)[0]
            print(file_details)
            
            sql = f"""
            select tag.tag_key, tag.tag_value from tag where tag.file_name = '{search_result}'
            """
            tags = db.execute(sql)
            results.append(
                (file_details, tags)
            )

    return render_template("index.html", searched_files = results)


def allowed_file_extension(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods = ["POST"])
def upload():

    
    file = request.files['filename']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
    elif allowed_file_extension(file.filename):
        filename = secure_filename(file.filename)
        description = request.form.get('description', '')
        file_extension = filename.split('.')[-1]
        file_type = EXTENSION_LOGICAL_MAP[file_extension]
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        sql = f"""
                   INSERT INTO file (type, name, description)
                   VALUES ('{file_type}', '{filename}', '{description}');"""
        db.execute(sql)
    
    return redirect(url_for("index"))

@app.route("/add-tag", methods = ["POST"])
def add_tag():
    tag_file = request.form.get('tagFile', '')
    filename = secure_filename(tag_file)

    tag_key = request.form.get('tagKey', '')
    tag_value = request.form.get('tagValue', '')

    sql = f"""
        INSERT INTO tag (file_name, tag_key, tag_value)
        VALUES ('{filename}', '{tag_key}', '{tag_value}');"""
    db.execute(sql)
    
    return redirect(url_for("index"))

@app.route("/search", methods = ["GET"])
def search():
    search_value = request.args.get('searchValue', '')
    sql = "SELECT name FROM file WHERE name LIKE %s OR description LIKE %s"
    results_raw = db.execute(sql, params=(f"%{search_value}%", f"%{search_value}%"))
    results = [r['name'] for r in results_raw]
    return redirect(url_for("index", results = results))
