import tkinter as tk
from tkinter import messagebox
import random
import time
import datetime
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from twilio.rest import Client

# 🔥 Twilio Credentials (Replace with your actual Twilio details)
TWILIO_SID = "SID"
TWILIO_AUTH_TOKEN = "TOKEn"
TWILIO_PHONE_NUMBER = "UR NO"  # No spaces


# Firebase Setup16DLUL769W8YM8WBHK14Y3AH
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://iotbasedentrysystem-4d243-default-rtdb.firebaseio.com/"
})

# Twilio Client Setup
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# Tkinter Window Setup
root = tk.Tk()
root.title("🔐 OTP-Based Entry System")
root.configure(bg="#edf5ff")
root.geometry("550x500")

# Outer Frame
outer_frame = tk.Frame(root, bg="white", bd=6, relief="ridge")
outer_frame.pack(pady=15, padx=15, fill="both", expand=True)

# UI Title
title_label = tk.Label(outer_frame, text="📲 Secure OTP-Based Entry", fg="#222", bg="white",
                        font=("Arial", 18, "bold"))
title_label.pack(pady=12)

# Mobile Number Input
tk.Label(outer_frame, text="📞 Enter Mobile Number:", fg="#444", bg="white", font=("Arial", 13)).pack(pady=5)
mobile_entry = tk.Entry(outer_frame, font=("Arial", 12), width=20, bd=3, relief="solid")
mobile_entry.pack(pady=5)

# OTP Entry (Hidden initially)
otp_label = tk.Label(outer_frame, text="🔢 Enter OTP:", fg="#444", bg="white", font=("Arial", 13))
otp_entry = tk.Entry(outer_frame, font=("Arial", 12), width=10, bd=3, relief="solid")

# Global Variable for OTP
otp_generated = None

def send_otp():
    """ Generates and sends OTP via Twilio """
    global otp_generated
    mobile = mobile_entry.get().strip()

    if len(mobile) != 10 or not mobile.isdigit():
        messagebox.showerror("Error", "Please enter a valid 10-digit mobile number.")
        return

    otp_generated = random.randint(100000, 999999)  # 6-digit OTP

    # Sending OTP via Twilio
    try:
        twilio_client.messages.create(
            body=f"Your OTP for door access is: {otp_generated}",
            from_=TWILIO_PHONE_NUMBER,
            to=f"+91{mobile}"  # Change the country code if needed
        )
        messagebox.showinfo("OTP Sent", f"OTP sent to {mobile}")

        # Show OTP input fields
        otp_label.pack(pady=5)
        otp_entry.pack(pady=5)
        verify_button.pack(pady=8)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to send OTP: {e}")

def verify_otp():
    """ Verifies OTP and updates Firebase """
    global otp_generated
    mobile = mobile_entry.get().strip()
    entered_otp = otp_entry.get().strip()

    if not entered_otp.isdigit():
        messagebox.showerror("Error", "OTP must be a number.")
        return

    if int(entered_otp) == otp_generated:
        messagebox.showinfo("Success", "✅ Access Granted!")
        update_access_status("granted", mobile)

        # Log Access in CSV
        ts = time.time()
        date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        access_log = pd.DataFrame([[mobile, date, timeStamp]], columns=['Mobile', 'Date', 'Time'])
        access_log.to_csv("AccessLogs.csv", mode='a', header=False, index=False)

        # ✅ Clear input fields after successful verification
        mobile_entry.delete(0, tk.END)
        otp_entry.delete(0, tk.END)

        # Hide OTP input fields
        otp_label.pack_forget()
        otp_entry.pack_forget()
        verify_button.pack_forget()

    else:
        messagebox.showerror("Failed", "❌ Access Denied. Incorrect OTP.")
        update_access_status("denied", mobile)


def update_access_status(status, mobile):
    """ Updates Firebase with access result """
    db.reference("door/access").update({
        "status": status,
        "user": mobile  # Storing mobile number instead of username
    })

# Buttons
send_otp_button = tk.Button(outer_frame, text="📩 Send OTP", font=("Arial", 11, "bold"), bg="#007bff", fg="white",
                            padx=8, pady=6, borderwidth=2, relief="ridge", cursor="hand2",
                            command=send_otp)
send_otp_button.pack(pady=8)

verify_button = tk.Button(outer_frame, text="✅ Verify OTP", font=("Arial", 11, "bold"), bg="#28a745", fg="white",
                          padx=8, pady=6, borderwidth=2, relief="ridge", cursor="hand2",
                          command=verify_otp)
verify_button.pack_forget()

# Professional Notes Section (Always at Bottom)
notes_frame = tk.Frame(outer_frame, bg="#edf5ff", bd=2, relief="ridge")
notes_frame.pack(side="bottom", fill="x", pady=10)

notes_title = tk.Label(notes_frame, text="📌 Professional Notes on OTP-Based Entry:", fg="#222", bg="#edf5ff",
                        font=("Arial", 12, "bold"))
notes_title.pack(pady=4)

notes_text = tk.Label(notes_frame, text="1. Ensure your mobile number is entered correctly before requesting OTP.\n"
                                        "2. OTPs are time-sensitive—use them quickly before they expire.\n"
                                        "3. If OTP is not received, check for network issues or request a resend.\n"
                                        "4. Do not share your OTP with anyone for security reasons.\n"
                                        "5. Make sure your phone is not in 'Do Not Disturb' mode to receive messages.",
                      fg="#555", bg="#edf5ff", font=("Arial", 10), justify="left")
notes_text.pack(pady=4, padx=8, anchor="w")

# Run Tkinter UI
root.mainloop()
