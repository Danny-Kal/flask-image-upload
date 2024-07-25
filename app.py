from flask import Flask, render_template, request, redirect, url_for
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Get the connection string from the environment variable
connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Initialize the BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("uploaded-images")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_form():
    return render_template('upload.html')

def upload_image_to_blob(file):
    logging.info("Uploading image to blob storage")
    try:
        blob_client = container_client.get_blob_client(file.filename)
        blob_client.upload_blob(file)
        logging.info("Successfully uploaded image to blob storage")
    except Exception as e:
        logging.error(f"Failed to upload image to blob storage: {e}")

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = file.filename
        upload_image_to_blob(file)
        return redirect(url_for('upload_form', filename=filename))
    return redirect(request.url)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000, debug=True)
