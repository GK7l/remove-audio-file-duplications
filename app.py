import os
import zipfile
from flask import Flask, request, send_from_directory, send_file
from pydub import AudioSegment
from hashlib import md5

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

def clear_folder(folder_path):
    """Clear all files in the specified folder."""
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)

def remove_duplicates_and_allocate_ids(folder_path, output_folder, duplicate_folder):
    """Remove duplicate audio files and allocate IDs."""
    seen_hashes = set()
    allocated_files = {}
    duplicate_files = []
    for filename in os.listdir(folder_path):
        if filename.endswith(('.wav', '.mp3', '.ogg')):
            file_path = os.path.join(folder_path, filename)
            audio = AudioSegment.from_file(file_path)
            file_hash = md5(audio.raw_data).hexdigest()
            if file_hash not in seen_hashes:
                seen_hashes.add(file_hash)
                output_path = os.path.join(output_folder, filename)
                audio.export(output_path, format="wav")
                allocated_files[output_path] = {
                    "frame_rate": audio.frame_rate,
                    "duration": len(audio) / 1000.0
                }
            else:
                duplicate_path = os.path.join(duplicate_folder, filename)
                audio.export(duplicate_path, format="wav")
                duplicate_files.append(duplicate_path)
    return allocated_files, duplicate_files

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

@app.route('/upload', methods=['POST'])
def upload_files():
    # Clear the upload, processed, and duplicate folders
    clear_folder(app.config['UPLOAD_FOLDER'])
    clear_folder(app.config['PROCESSED_FOLDER'])
    clear_folder(app.config['DUPLICATE_FOLDER'])

    if 'files' not in request.files:
        return 'No file part'
    files = request.files.getlist('files')
    if not files:
        return 'No selected files'
    for file in files:
        if file.filename == '':
            return 'No selected file'
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
    allocated_files, duplicate_files = remove_duplicates_and_allocate_ids(app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], app.config['DUPLICATE_FOLDER'])
    return f'Files processed successfully. <a href="/download_zip/unique">Download unique files as ZIP</a> | <a href="/download_zip/duplicates">Download duplicate files as ZIP</a>'

@app.route('/download_zip/<file_type>')
def download_zip(file_type):
    if file_type == 'unique':
        folder = app.config['PROCESSED_FOLDER']
        zip_filename = 'unique_files.zip'
    elif file_type == 'duplicates':
        folder = app.config['DUPLICATE_FOLDER']
        zip_filename = 'duplicate_files.zip'
    else:
        return 'Invalid file type'
    
    zip_path = os.path.join(folder, zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder):
            for file in files:
                if file != zip_filename:
                    zipf.write(os.path.join(root, file), file)
    return send_file(zip_path, as_attachment=True)

@app.route('/download')
def download_files():
    files = os.listdir(app.config['PROCESSED_FOLDER'])
    links = [f'<a href="/download/{file}">{file}</a>' for file in files]
    return '<br>'.join(links)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)