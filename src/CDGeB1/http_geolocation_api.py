from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qsl, urlparse
import os
import tempfile
import zipfile
import subprocess
from time import sleep
import shutil

class WebRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Parse user request
        # Example:
        # >>> urlparse("http://www.google.com/api/search?param1=val1&param2=val2")
        # ParseResult(scheme='http', netloc='www.google.com', path='/api/search', params='', query='param1=val1&param2=val2', fragment='')
        parsed_url = urlparse(self.path)
        _host = parsed_url.netloc
        operation = parsed_url.path
        parameters = dict(parse_qsl(parsed_url.query))

        if "/CDGeolocation" != operation:
            print("Invalid path in URL")
            self.gen_response(400, "Invalid path in URL")
            return

        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
        except:
            print("Content is missing. Perhaps you forgot content-type header?")
            self.gen_response(400, "Content is missing. Perhaps you forgot content-type header?")
            return
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as working_dir:

            zip_file_path = os.path.join(working_dir, "uploaded.zip")
            input_path = os.path.join(working_dir, 'input', os.sep)
            output_path = os.path.join(working_dir, 'output', os.sep)
   
            # Create output directory if not exist
            if not os.path.isdir(input_path):
                os.makedirs(input_path)
            if not os.path.isdir(output_path):
                os.makedirs(output_path)
            
            # Save the ZIP file
            with open(zip_file_path, 'wb') as temp_zip:
                temp_zip.write(post_data)
            
            try:
                # Unzip the file
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(input_path)
            except:
                print("Failed to unzip the uploaded payload.")
                self.gen_response(400, "Failed to unzip the uploaded payload.")
                return

            # Create a temporary file for the subprocess output
            temp_output_path = os.path.join(output_path, "results.txt")
            with open(temp_output_path, 'w+') as temp_output:
                subprocess.run(["python3", "mypythoncode.py", input_path, output_path], stdout=temp_output, stderr=subprocess.STDOUT)
                
            # Let it run
            sleep(5)

            # try:
            #     subprocess.run(["false"], check=True)
            # except subprocess.CalledProcessError as e:
            #     print("With check=True: Command failed with return code", e.returncode)

            # Create a temporary file for the ZIP to be sent in response
            zip_output_fd, zip_output_path = tempfile.mkstemp(suffix='.zip')
            os.close(zip_output_fd)  # Close the file descriptor

            # Create a ZIP file to include the output folder
            with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(output_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=os.path.dirname(output_path))
                        zipf.write(file_path, arcname=arcname)

            # Send the ZIP file as the response
            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="result.zip"')
            self.end_headers()

            with open(zip_output_path, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)

            # Clean up the temporary ZIP file after sending it
            os.remove(zip_output_path)

    def gen_response(self, status_code, content: bytes):
        if isinstance(content, str):
            content = content.encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/text")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
