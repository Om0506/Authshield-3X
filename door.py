import time
import serial
from datetime import datetime
from firebase import firebase

# Replace with your Firebase Realtime Database URL
firebase_url = "https://iotbasedentrysystem-c2669-default-rtdb.asia-southeast1.firebasedatabase.app/"
firebase_app = firebase.FirebaseApplication(firebase_url, None)

# Initialize serial communication with Arduino (Replace with the correct COM port)
arduino = serial.Serial('COM3', 9600)
time.sleep(2)  # Allow time for Arduino initialization

last_command = None  
while True:
    try:
        # Fetch off-hours data from Firebase
        off_hours = firebase_app.get('/door/offHours', None)
        start_time = off_hours.get('startTime', "00:00")
        end_time = off_hours.get('endTime', "00:00")

        # Get the current time in HH:MM format
        current_time = datetime.now().strftime("%H:%M")

        # Fetch the door access status from Firebase
        status = firebase_app.get('/door/access/status', None)
        print(f"Firebase Status: {status}")

        # Prepare time data to send to Arduino
        time_string = f"{start_time},{end_time},{current_time}\n"
        
        arduino.write(time_string.encode())  # Send times to Arduino
        print(f"Sent to Arduino: {time_string.strip()}")

        # Send door access command based on Firebase status
        if status == "granted" :
            arduino.write(b'open\n')
            print("Sent 'open' command to Arduino")
            last_command = "open"
            time.sleep(5)  # Wait 5 seconds before next check

        elif status == "denied" :
            arduino.write(b'close\n')
            print("Sent 'close' command to Arduino")
            last_command = "close"
            time.sleep(1)

        # Wait 1 second before sending the next data packet
        time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)  # Retry after 3 seconds in case of an error
