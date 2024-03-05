from flask import Flask, request, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
import tempfile
import subprocess
import zipfile


CDG_PATH = r'C:\Users\Adi\Desktop\Thesis\CDGeB-1\Solving Methods\three-tier-solver\src\CDGeB1\main.py'
PYTHON_BIN = 'python'
OUTPUT_DIR = os.path.join('download','output')

app = Flask(__name__)

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Ensure all three files are present
        file1 = request.files.get('measurements')
        file2 = request.files.get('servers')
        file3 = request.files.get('solution')

        if not (file1 and file2 and file3):
            return 'Missing files. Please ensure all three files are uploaded.'
        else:
            # Create a temporary directory
            with tempfile.TemporaryDirectory() as working_dir:
                input_path = os.path.join(working_dir, 'input')
                output_path = os.path.join(working_dir, 'output')
            
            # Create input and output directories if they do not exist
            os.makedirs(input_path, exist_ok=True)
            os.makedirs(output_path, exist_ok=True)

            app.config['UPLOAD_FOLDER'] = input_path
            app.config['OUTPUT_FOLDER'] = OUTPUT_DIR

            file1.save(os.path.join(app.config['UPLOAD_FOLDER'], 'measurements.csv'))
            file2.save(os.path.join(app.config['UPLOAD_FOLDER'], 'servers.csv'))
            file3.save(os.path.join(app.config['UPLOAD_FOLDER'], 'solution.csv'))

            # Create a temporary file for the subprocess output
            temp_output_path = os.path.join(output_path, "results.txt")
            with open(temp_output_path, 'w+') as temp_output:
                # Blocking call
                subprocess.run([PYTHON_BIN, CDG_PATH, input_path, output_path], stdout=temp_output, stderr=subprocess.STDOUT)
                
            # Create a temporary file for the ZIP to be sent in response
            zip_output_fd, zip_output_path = tempfile.mkstemp(dir=OUTPUT_DIR, suffix='.zip')
            relative_zip_output_path = os.path.relpath(zip_output_path, start=os.getcwd())
            os.close(zip_output_fd)  # Close the file descriptor

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

            return render_template('download.html', output_file=relative_zip_output_path)
    else:
        return 'File upload failed'

@app.route('/download/output/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
