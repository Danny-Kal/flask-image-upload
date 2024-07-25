from flask import Flask, render_template, request, redirect, url_for
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import logging
from datetime import datetime, timedelta

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
    filename = request.args.get('filename')
    return render_template('upload.html', filename=filename)

def upload_image_to_blob(file):
    logging.info("Uploading image to blob storage")
    try:
        blob_client = container_client.get_blob_client(file.filename)
        blob_client.upload_blob(file)
        logging.info("Successfully uploaded image to blob storage")
        return file.filename
    except Exception as e:
        logging.error(f"Failed to upload image to blob storage: {e}")
        return None

def generate_blob_url(filename):
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_client.container_name,
        blob_name=filename,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_client.container_name}/{filename}?{sas_token}"
    return blob_url

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = upload_image_to_blob(file)
        if filename:
            blob_url = generate_blob_url(filename)
            return redirect(url_for('upload_form', filename=blob_url))
    return redirect(request.url)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000, debug=True)
