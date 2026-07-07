import subprocess

# Paths to your scripts (modify the paths accordingly)
script1_path = "app.py"            # Path to the main app script
script2_path = "door.py"           # Path to the door control script
script3_path = "admin/app.py"      # Path to the admin app script

try:
    # Run app.py, door.py, admin/app.py, and the HTTP server simultaneously
    process1 = subprocess.Popen(['python', script1_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process2 = subprocess.Popen(['python', script2_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process3 = subprocess.Popen(['python', script3_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process4 = subprocess.Popen(['python', '-m', 'http.server', '7070'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("All scripts and the HTTP server are running simultaneously...")

    # Print outputs from all processes (optional)
    while process1.poll() is None or process2.poll() is None or process3.poll() is None or process4.poll() is None:
        line1 = process1.stdout.readline()
        if line1:
            print("Script 1 (Main App) Output:", line1.decode().strip())
        
        line2 = process2.stdout.readline()
        if line2:
            print("Script 2 (Door Control) Output:", line2.decode().strip())
        
        line3 = process3.stdout.readline()
        if line3:
            print("Script 3 (Admin App) Output:", line3.decode().strip())
        
        line4 = process4.stdout.readline()
        if line4:
            print("HTTP Server Output:", line4.decode().strip())

    # Wait for all processes to complete
    process1.wait()
    process2.wait()
    process3.wait()
    process4.wait()

    # Check for any errors
    if process1.returncode != 0:
        print("Script 1 (Main App) Error:", process1.stderr.read().decode())
    if process2.returncode != 0:
        print("Script 2 (Door Control) Error:", process2.stderr.read().decode())
    if process3.returncode != 0:
        print("Script 3 (Admin App) Error:", process3.stderr.read().decode())
    if process4.returncode != 0:
        print("HTTP Server Error:", process4.stderr.read().decode())

    print("All scripts and the HTTP server finished execution.")

except Exception as e:
    print(f"An error occurred while running the scripts: {e}")
