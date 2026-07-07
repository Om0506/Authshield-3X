import cv2
import numpy as np
import pandas as pd
import os
import time
import datetime
import random
from flask import Flask, render_template, Response, jsonify, request
import firebase_admin
from firebase_admin import credentials, db
from twilio.rest import Client

# Flask App Initialization
app = Flask(__name__)

# Firebase Setup (Avoid duplicate initialization)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://iotbasedentrysystem-c2669-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

# Twilio Credentials (Replace with actual credentials)
TWILIO_SID = "SID"
TWILIO_AUTH_TOKEN = "TOKEN"
TWILIO_PHONE_NUMBER = "NO"

twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Store OTPs Temporarily (with Expiry)
otp_store = {}

# Load Face Recognizer Model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("TrainingImageLabel/Trainner.yml")
faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
df = pd.read_csv("StudentDetails/StudentDetails.csv")
cam = cv2.VideoCapture(0)

scan_result = {"status": "", "user": ""}  # Global variable to store scan result


# Function to update Firebase
import threading  # Import threading for delayed status reset

# Function to update Firebase logs with serial numbering
def update_logs(username, access_type):
    ts = time.time()
    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    time_stamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')

    # Reference to the logs path for the current date
    date_ref = db.reference(f"logs/{date}")
    
    # Get the count of existing log entries to use as serial number
    serial_number = len(date_ref.get() or {}) + 1  # Incrementing serial number

    # Create the log data
    log_data = {
        "username": username,
        "time": time_stamp,
        "access_type": access_type,
    }

    # Push the log entry under the serial number
    date_ref.child(str(serial_number)).set(log_data)

 


# Function to update Firebase and reset status after 5 seconds
def update_firebase(status, user, access_type="face"):
    global scan_result
    scan_result = {"status": status, "user": user}
    ref = db.reference("door/access")
    ref.update(scan_result)

    if status == "granted":
        update_logs(user, access_type)  # Store logs in Firebase

        def reset_status():
            time.sleep(5)
            ref.update({"status": "denied", "user": "unknown"})

        threading.Thread(target=reset_status).start()

# Face Recognition Logic
def detect_faces():
    start_time = time.time()
    face_matched = False  # Stop scanning if face is matched

    while time.time() - start_time < 5:  # Scan for 5 seconds
        ret, frame = cam.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.2, 5)

        detected_name = "Face Not Matched"
        color = (0, 0, 255)  # Red for failure

        for (x, y, w, h) in faces:
            Id, conf = recognizer.predict(gray[y:y+h, x:x+w])

            if conf < 50:  # Adjust threshold for accuracy
                matched_user = df[df['Id'] == Id]
                if not matched_user.empty:
                    name = matched_user['Name'].values[0]  # Safe lookup
                    detected_name = f" Welcome {name}"
                    color = (0, 255, 0)  # Green for success
                    face_matched = True

                    # Save attendance
                    ts = time.time()
                    date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                    attendance = pd.DataFrame([[Id, name, date, timeStamp]], columns=['Id', 'Name', 'Date', 'Time'])
                    attendance.to_csv(f"Attendance/Attendance_{date}.csv", mode='a', header=False, index=False)

                    # Update Firebase with "granted" status and user's name
                    update_firebase("granted", name)

                    # Reset Firebase status to "denied" after 5 seconds
                    def reset_status():
                        time.sleep(5)
                        ref = db.reference("door/access")
                        if ref.get()["status"] == "granted":  # Double-check status
                            ref.update({"status": "denied", "user": "unknown"})

                    threading.Thread(target=reset_status).start()

                    break  # Stop scanning after a successful match

            else:
                detected_name = "Face Not Matched"
                update_firebase("denied", "unknown")

            # Draw rectangle around face
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

        # Draw the detection message on the frame
        cv2.putText(frame, detected_name, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3, cv2.LINE_AA)

        # Convert frame to JPEG format
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

        if face_matched:
            break  # Stop scanning if face matched

    if not face_matched:
        update_firebase("denied", "unknown")


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/otp')
def otp():
    return render_template('otp_verification.html')

@app.route('/admin')
def admin():
    return render_template('admin_approval.html')

@app.route('/video_feed')
def video_feed():
    return Response(detect_faces(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/scan_status')
def scan_status():
    """ Returns the last scan result to the frontend """
    return jsonify(scan_result)

# OTP Verification Routes
@app.route("/send_otp", methods=["POST"])
def send_otp():
    data = request.json
    mobile = data.get("mobile")

    if not mobile or len(mobile) != 10 or not mobile.isdigit():
        return jsonify({"status": "error", "message": "Invalid mobile number"}), 400

    otp = random.randint(100000, 999999)
    otp_store[mobile] = {"otp": otp, "timestamp": time.time()}  # Store OTP with timestamp

    # Send OTP via Twilio
    try:
        twilio_client.messages.create(
            body=f"Your OTP for door access is: {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=f"+91{mobile}"  # Change country code if needed
        )
        return jsonify({"status": "success", "message": "OTP sent successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to send OTP: {e}"}), 500

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.json
    mobile = data.get("mobile")
    entered_otp = data.get("otp")

    if not mobile or not entered_otp or not entered_otp.isdigit():
        return jsonify({"status": "error", "message": "Invalid OTP"}), 400

    # Check OTP expiry (5 minutes)
    stored_data = otp_store.get(mobile)
    if not stored_data or time.time() - stored_data["timestamp"] > 300:
        return jsonify({"status": "error", "message": "OTP expired"}), 400

    if int(entered_otp) == stored_data["otp"]:
        ref = db.reference("door/access")
        update_logs(mobile, "otp")  # Log OTP-based access
        ref.update({"status": "granted", "user": mobile})

        # Log access to CSV
        ts = time.time()
        date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        access_log = pd.DataFrame([[mobile, date, timeStamp]], columns=['Mobile', 'Date', 'Time'])
        access_log.to_csv("AccessLogs.csv", mode='a', header=False, index=False)

        # Remove OTP after successful verification
        del otp_store[mobile]

        # Reset status to "denied" after 5 seconds (if it was granted)
        def reset_status():
            time.sleep(5)
            if ref.get()["status"] == "granted":  # Double-check status before resetting
                ref.update({"status": "denied", "user": "unknown"})

        threading.Thread(target=reset_status).start()

        return jsonify({"status": "success", "message": "Access Granted!"})
    else:
        return jsonify({"status": "error", "message": "Incorrect OTP"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5001) 