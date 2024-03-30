from flask import Flask, request, render_template, send_from_directory
import os
import sys
from werkzeug.utils import secure_filename
import tempfile
import subprocess
import zipfile
import json
import datetime
from multiprocessing import Pool, freeze_support

from CDGeB1.main import main as CDG_main


ROOT_DIR = os.path.join(os.path.dirname(__file__), 'webappstorage')
SESSIONS_DIR = os.path.join(ROOT_DIR,'sessions')

os.makedirs(ROOT_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)


application = Flask(__name__)


@application.route('/')
def upload_file():
    return render_template('upload.html')

@application.route('/download/<path:filepath>', methods=['GET'])
def download_zip(filepath):
    if filepath.lower().endswith('.zip'):
        return send_from_directory(ROOT_DIR, filepath, as_attachment=True)
    else:
        return 'Invalid file path'

@application.route('/uploader', methods=['POST'])
def upload_files():
    if request.method == 'POST':
        # Ensure all three files are present
        file1 = request.files.get('measurements')
        file2 = request.files.get('servers')
        file3 = request.files.get('solution')

        if not (file1 and file2 and file3):
            return 'Missing files. Please ensure all three files are uploaded.'
        
        # Make new folder with uniquely generated name inside session directory
        session_dir = tempfile.mkdtemp(dir=SESSIONS_DIR)

        input_path = os.path.join(session_dir, 'input')
        output_path = os.path.join(session_dir, 'output')

        os.makedirs(input_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)

        file1.save(os.path.join(input_path, 'measurements.csv'))
        file2.save(os.path.join(input_path, 'servers.csv'))
        file3.save(os.path.join(input_path, 'solution.csv'))

        # Create a temporary file for the CDG output
        temp_output_path = os.path.join(output_path, "results.txt")
        
        # Redirect sys.stdout hack
        original_stdout = sys.stdout
        with open(temp_output_path, 'w') as f:
            sys.stdout = f
            CDG_main(input_path, output_path)
            # Reset sys.stdout to its original value
            sys.stdout = original_stdout

        # Create a temporary file for the ZIP to be sent in response
        zip_output_fd, zip_output_path = tempfile.mkstemp(dir=session_dir, prefix='CDG_', suffix='.zip')
        relative_zip_output_path = os.path.relpath(zip_output_path, start=ROOT_DIR)
        os.close(zip_output_fd)

        # Create a ZIP file to include the output folder
        with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=os.path.dirname(output_path))
                    zipf.write(file_path, arcname=arcname)
            for root, dirs, files in os.walk(input_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=os.path.dirname(input_path))
                    zipf.write(file_path, arcname=arcname)

        return render_template('download.html', output_file_path=relative_zip_output_path)
    else:
        return 'File upload failed'

@application.route('/rest', methods=['POST'])
def rest_api():
    if request.method == 'POST':
        # Ensure all three files are present
        file1 = request.files.get('measurements')
        file2 = request.files.get('servers')
        file3 = request.files.get('solution')

        if not (file1 and file2 and file3):
            return 'Missing files. Please ensure all three files are uploaded.'
        
        # Make new folder with uniquely generated name inside session directory
        session_dir = tempfile.mkdtemp(dir=SESSIONS_DIR)

        input_path = os.path.join(session_dir, 'input')
        output_path = os.path.join(session_dir, 'output')

        os.makedirs(input_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)

        file1.save(os.path.join(input_path, 'measurements.csv'))
        file2.save(os.path.join(input_path, 'servers.csv'))
        file3.save(os.path.join(input_path, 'solution.csv'))

        # Create a temporary file for the CDG output
        temp_output_path = os.path.join(output_path, "results.txt")
        
        # Redirect sys.stdout hack
        original_stdout = sys.stdout
        with open(temp_output_path, 'w') as f:
            sys.stdout = f
            CDG_main(input_path, output_path)
            # Reset sys.stdout to its original value
            sys.stdout = original_stdout

        outputAsDict = {}
        outputAsDict['Meta'] = {}
        outputAsDict['Meta']['date_utc'] = datetime.datetime.now(datetime.UTC).isoformat()

        outputAsDict['Assets'] = {}
        for root, dirs, files in os.walk(output_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=os.path.dirname(SESSIONS_DIR))
                print("file", file, "file_path", file_path, "arcname", arcname)
                outputAsDict['Assets'][file] = arcname.replace('\\', '/').replace('sessions', '/GetFile')
        for root, dirs, files in os.walk(input_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=os.path.dirname(SESSIONS_DIR))
                outputAsDict['Assets'][file] = arcname.replace('\\', '/').replace('sessions', '/GetFile')

        return json.dumps(outputAsDict, indent=4)
    else:
        return 'File upload failed'

@application.route('/GetFile/<path:filepath>', methods=['GET'])
def download_file(filepath):
    if filepath.lower().endswith(('.html', '.txt', '.csv')):
        return send_from_directory(SESSIONS_DIR, filepath, as_attachment=True)
    else:
        return 'Invalid file path'


def main():
    application.run(debug=True)

if __name__ == "__main__":
    freeze_support()  # For Windows support
    main()    
