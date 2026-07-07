import time
import serial
from datetime import datetime
from firebase import firebase

# Firebase initialization
firebase_url = "https://iotbasedentrysystem-c2669-default-rtdb.asia-southeast1.firebasedatabase.app/"
firebase_app = firebase.FirebaseApplication(firebase_url, None)

arduino = serial.Serial('COM3', 9600)  # Adjust 'COM3' to your Arduino port
time.sleep(2)  # Allow time for Arduino to initialize

while True:
    try:
        # Fetch off-hours data from Firebase
        off_hours = firebase_app.get('/door/offHours', None)
        start_time = off_hours.get('startTime', "00:00")
        end_time = off_hours.get('endTime', "00:00")

        # Get current system time (HH:MM format)
        current_time = datetime.now().strftime("%H:%M")

        # Send start_time, end_time, and current_time to Arduino
        time_string = f"{start_time},{end_time},{current_time}\n"
        arduino.write(time_string.encode())
        print(f"Sent to Arduino: {time_string.strip()}")

        time.sleep(1)  # Update every 1 second (1000 ms)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)  # Retry after 1 second in case of an error
