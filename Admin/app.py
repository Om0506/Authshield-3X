from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Endpoint to trigger addimage.py execution with a username
@app.route('/take_image', methods=['POST'])
def take_image():
    try:
        # Get the username from the POST request
        username = request.json.get('username')
        
        if not username:
            return jsonify({'status': 'error', 'message': 'Username is required.'})

        # Get the absolute path of addimage.py in the parent folder (project)
        addimage_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'addimage.py')

        # Run the addimage.py script and pass the username as an argument
        subprocess.run(['python', addimage_script_path, username], check=True)
        
        return jsonify({'status': 'success', 'message': f'Image captured and training initiated for {username}.'})
    
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': f'Error occurred: {e}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'An unexpected error occurred: {e}'})
        
if __name__ == '__main__':
    app.run(debug=True)
