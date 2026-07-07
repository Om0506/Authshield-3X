import cv2
import numpy as np
import pandas as pd
import os
import time
import datetime
import tkinter as tk
from tkinter import Label, Frame, Button
from PIL import Image, ImageTk
import firebase_admin
from firebase_admin import credentials, db

# Firebase Setup
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://iotbasedentrysystem-4d243-default-rtdb.firebaseio.com/"
})

# Load Face Recognizer Model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("TrainingImageLabel/Trainner.yml")
faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
df = pd.read_csv("StudentDetails/StudentDetails.csv")

# Create Tkinter Window
root = tk.Tk()
root.title("🔒 Secure Entry System")
root.configure(bg="#edf5ff")
root.geometry("550x650")

# Outer Frame
outer_frame = Frame(root, bg="white", bd=6, relief="ridge")
outer_frame.pack(pady=15, padx=15, fill="both", expand=True)

# UI Title
title_label = Label(outer_frame, text="🔒 Secure Face Recognition Entry", fg="#222", bg="white",
                    font=("Arial", 18, "bold"))
title_label.pack(pady=12)

# Frame for Camera
frame = Frame(outer_frame, bg="#007bff", bd=4, relief="solid")
frame.pack(pady=10)
frame.pack_forget()

# Camera Feed Label Inside the Frame
image_label = Label(frame, bg="black")
image_label.pack()

# Message Label
message_label = Label(outer_frame, text="Click 'Scan Now' to Start", fg="#444", bg="white", font=("Arial", 13, "bold"))
message_label.pack(pady=8)

# Open Camera
cam = cv2.VideoCapture(0)
scanning = False

def update_firebase(status, user):
    """ Updates the Firebase Realtime Database with access status """
    ref = db.reference("door/access")
    ref.update({
        "status": status,
        "user": user
    })

def recognize_face():
    global scanning
    scanning = True
    scan_button.pack_forget()
    frame.pack()
    message_label.config(text="🔍 Scanning Face...", fg="black")

    start_time = time.time()
    face_matched = False  

    while time.time() - start_time < 5:  # Scan for 5 seconds
        ret, im = cam.read()
        if not ret:
            continue
        
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.2, 5)

        detected_name = "❌ Face Not Matched"
        color = (255, 0, 0)  

        for (x, y, w, h) in faces:
            Id, conf = recognizer.predict(gray[y:y+h, x:x+w])

            if conf < 50:
                name = df.loc[df['Id'] == Id]['Name'].values[0]
                detected_name = f"✅ Welcome {name}"
                color = (0, 255, 0)  
                face_matched = True  

                # Save attendance
                ts = time.time()
                date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                attendance = pd.DataFrame([[Id, name, date, timeStamp]], columns=['Id', 'Name', 'Date', 'Time'])
                attendance.to_csv("Attendance/Attendance_" + date + ".csv", mode='a', header=False, index=False)

                # Update Firebase with success
                update_firebase("granted", name)

            else:
                if conf > 75:
                    noOfFile = len(os.listdir("ImagesUnknown")) + 1
                    cv2.imwrite(f"ImagesUnknown/Image{noOfFile}.jpg", im[y:y+h, x:x+w])

            cv2.rectangle(im, (x, y), (x + w, y + h), color, 3)

        # Update Message UI
        message_label.config(text=detected_name, fg="green" if "Welcome" in detected_name else "red")

        # Convert Image to Tkinter Format
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(im)
        im = im.resize((450, 300))
        img_tk = ImageTk.PhotoImage(image=im)
        image_label.img_tk = img_tk
        image_label.configure(image=img_tk)
        root.update()

        if face_matched:
            time.sleep(2)
            message_label.config(text="")
            break  

    if not face_matched:
        update_firebase("denied", "unknown")

    scanning = False
    frame.pack_forget()
    scan_button.pack(pady=10)

# Scan Button
scan_button = Button(outer_frame, text="📸 Scan Now", font=("Arial", 11, "bold"), bg="#007bff", fg="white", 
                     padx=8, pady=6, borderwidth=2, relief="ridge", cursor="hand2",
                     activebackground="#0056b3", activeforeground="white", 
                     highlightthickness=1, highlightbackground="#0056b3",
                     command=lambda: recognize_face() if not scanning else None)
scan_button.pack(pady=8)

# Spacer to push notes to the bottom
spacer = Label(outer_frame, text="", bg="white")
spacer.pack(expand=True)

# Professional Notes Section (Always at Bottom)
notes_frame = Frame(outer_frame, bg="#edf5ff", bd=2, relief="ridge")
notes_frame.pack(side="bottom", fill="x", pady=10)

notes_title = Label(notes_frame, text="📌 Professional Notes on Facial Recognition:", fg="#222", bg="#edf5ff",
                     font=("Arial", 12, "bold"))
notes_title.pack(pady=4)

notes_text = Label(notes_frame, text="1. Ensure proper lighting for accurate recognition.\n"
                                     "2. Maintain a clear and stable face position.\n"
                                     "3. If recognition fails, try re-registering with better image quality.\n"
                                     "4. Avoid covering the face with accessories like sunglasses or hats.\n"
                                     "5. Regularly update face data for improved accuracy.",
                   fg="#555", bg="#edf5ff", font=("Arial", 10), justify="left")
notes_text.pack(pady=4, padx=8, anchor="w")

# Run the Tkinter UI
root.mainloop()

# Release Camera on Close
cam.release()
cv2.destroyAllWindows()
