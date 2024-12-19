Importing Required Libraries
python
Copy code
import os
import zipfile
from flask import Flask, request, send_from_directory, send_file
from pydub import AudioSegment
from hashlib import md5
os: Provides utilities to interact with the operating system, such as file handling.
zipfile: Enables creation and manipulation of .zip files.
Flask: A lightweight web framework to create APIs and web applications.
request: Handles HTTP requests in Flask.
send_from_directory & send_file: Used to send files from the server to the client.
AudioSegment: A class from pydub to process audio files.
md5: A hashing algorithm to calculate file hashes for detecting duplicates.
Application Initialization and Folder Setup
python
Copy code
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
DUPLICATE_FOLDER = 'duplicates'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(DUPLICATE_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['DUPLICATE_FOLDER'] = DUPLICATE_FOLDER
app = Flask(__name__): Creates the Flask application.
Defines three folders:
UPLOAD_FOLDER: Where uploaded files are stored temporarily.
PROCESSED_FOLDER: Where unique processed audio files are stored.
DUPLICATE_FOLDER: Where duplicate audio files are stored.
os.makedirs(): Ensures the folders exist, creating them if they don't.
app.config: Stores folder paths as Flask configuration variables.
Utility Functions
Clear Folder
python
Copy code
def clear_folder(folder_path):
    """Clear all files in the specified folder."""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
clear_folder(folder_path): Deletes all files in a given folder to reset its contents before use.
Iterates over each file in the folder and deletes it if it's a file.
Remove Duplicates and Allocate IDs
python
Copy code
def remove_duplicates_and_allocate_ids(folder_path, output_folder, duplicate_folder):
    """Remove duplicate audio files and allocate IDs."""
    seen_hashes = set()
    allocated_files = {}
    duplicate_files = []
Initializes:
seen_hashes: Tracks hashes of unique audio files.
allocated_files: Stores metadata (frame rate and duration) of unique files.
duplicate_files: Stores paths of duplicate files.
python
Copy code
    for filename in os.listdir(folder_path):
        if filename.endswith(('.wav', '.mp3', '.ogg')):
            file_path = os.path.join(folder_path, filename)
            audio = AudioSegment.from_file(file_path)
            file_hash = md5(audio.raw_data).hexdigest()
Loops through audio files in the folder.
Converts the file to an AudioSegment.
Computes the hash of the raw audio data to identify duplicates.
python
Copy code
            if file_hash not in seen_hashes:
                seen_hashes.add(file_hash)
                output_path = os.path.join(output_folder, filename)
                audio.export(output_path, format="wav")
                allocated_files[output_path] = {
                    "frame_rate": audio.frame_rate,
                    "duration": len(audio) / 1000.0
                }
If the hash is new:
Adds it to seen_hashes.
Exports the file to PROCESSED_FOLDER.
Saves its metadata in allocated_files.
python
Copy code
            else:
                duplicate_path = os.path.join(duplicate_folder, filename)
                audio.export(duplicate_path, format="wav")
                duplicate_files.append(duplicate_path)
If the hash already exists:
Exports the file to DUPLICATE_FOLDER.
Adds the path to duplicate_files.
python
Copy code
    return allocated_files, duplicate_files
Returns the metadata of unique files and paths of duplicates.
Flask Routes
Homepage
python
Copy code
@app.route('/')
def upload_form():
    return '''
    <html>
        <body>
            <h1>Upload Files</h1>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="files" multiple>
                <input type="submit" value="Upload">
            </form>
        </body>
    </html>
    '''
Displays a simple HTML form for file uploads.
File Upload Endpoint
python
Copy code
@app.route('/upload', methods=['POST'])
def upload_files():
    clear_folder(app.config['UPLOAD_FOLDER'])
    clear_folder(app.config['PROCESSED_FOLDER'])
    clear_folder(app.config['DUPLICATE_FOLDER'])
Clears existing files in all folders.
python
Copy code
    if 'files' not in request.files:
        return 'No file part'
    files = request.files.getlist('files')
Checks for uploaded files in the request.
python
Copy code
    for file in files:
        if file.filename == '':
            return 'No selected file'
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
Saves each uploaded file to the UPLOAD_FOLDER.
python
Copy code
    allocated_files, duplicate_files = remove_duplicates_and_allocate_ids(
        app.config['UPLOAD_FOLDER'], 
        app.config['PROCESSED_FOLDER'], 
        app.config['DUPLICATE_FOLDER']
    )
    return f'Files processed successfully. <a href="/download_zip/unique">Download unique files as ZIP</a> | <a href="/download_zip/duplicates">Download duplicate files as ZIP</a>'
Processes the files for duplicates, then returns links to download the results.
Download ZIP
python
Copy code
@app.route('/download_zip/<file_type>')
def download_zip(file_type):
    if file_type == 'unique':
        folder = app.config['PROCESSED_FOLDER']
        zip_filename = 'unique_files.zip'
    elif file_type == 'duplicates':
        folder = app.config['DUPLICATE_FOLDER']
        zip_filename = 'duplicate_files.zip'
Identifies the requested folder and ZIP file name based on file_type.
python
Copy code
    zip_path = os.path.join(folder, zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder):
            for file in files:
                if file != zip_filename:
                    zipf.write(os.path.join(root, file), file)
    return send_file(zip_path, as_attachment=True)
Creates a ZIP file of the folder's contents and sends it to the user.
Download Individual Files
python
Copy code
@app.route('/download')
def download_files():
    files = os.listdir(app.config['PROCESSED_FOLDER'])
    links = [f'<a href="/download/{file}">{file}</a>' for file in files]
    return '<br>'.join(links)
Displays download links for individual unique files.
python
Copy code
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)
Sends the requested file from PROCESSED_FOLDER.
Run the Application
python
Copy code
if __name__ == '__main__':
    app.run(debug=True)
Starts the Flask application in debug mode.












