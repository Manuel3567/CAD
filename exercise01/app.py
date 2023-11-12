from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

import os
from flask import Flask, flash, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
from io import BytesIO

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'py'}
EXTENSION_LOGICAL_MAP = {'txt': 'Document', 'pdf': 'Document', 'png': 'Picture', 'jpg': 'Picture', 'jpeg': 'Picture', 'gif': 'Video', 'mp4': 'Video'}

BUCKET_NAME = os.environ.get('BUCKET_NAME')

app = Flask(__name__)


import gcp


@app.route("/", methods = ["GET"])
def index():
    search_results = request.args.getlist('results')

    results = []

    if search_results:
        for search_result in search_results:
            """
            search_result = "example.txt"
            result = {
              "filename": "example.txt",
              "description": "exampledescription", 
              "type": "Document",
              "creation_date": 2023-01-01,
              "tags": [{"key": "location", "value": "town"}]
            }
            """
            result = gcp.get_metadata_from_filename(search_result)
            result["filename"] = search_result
            print(search_result)
            print(result)
            results.append(result)

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
        gcp.upload(file, BUCKET_NAME, filename)
        gcp.set_metadata(filename, file_type, description)
    
    return redirect(url_for("index"))

@app.route("/add-tag", methods = ["POST"])
def add_tag():
    tag_file = request.form.get('tagFile', '')
    filename = secure_filename(tag_file)

    tag_key = request.form.get('tagKey', '')
    tag_value = request.form.get('tagValue', '')
    gcp.set_tag(filename, tag_key, tag_value)

    return redirect(url_for("index"))

@app.route("/search", methods = ["GET"])
def search():
    search_value = request.args.get('searchValue', '')
    results = gcp.search(search_value)
    return redirect(url_for("index", results = results))

@app.route("/download/<path:name>", methods = ["GET"])
def download(name):
    content = gcp.download(BUCKET_NAME, name)
    return send_file(
        BytesIO(content), as_attachment=True, download_name=name
    )
