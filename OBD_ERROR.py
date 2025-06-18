import pandas as pd
import serial
import time
import tkinter as tk
from tkinter import Label, Button, Canvas, Scrollbar, Text
from datetime import datetime
import pyttsx3

# --- CONFIGURATION ---
SERIAL_PORT = 'COM10'
BAUD_RATE = 115200
REFRESH_INTERVAL = 5000  # ms
CSV_PATH = r"C:\Users\kannan\Desktop\obd-trouble-codes.csv"
LOG_FILE = "error_log.csv"

# --- Load CSV into dictionary ---
def load_error_codes(file_path):
    df = pd.read_csv(file_path)
    return df.set_index('Error Code')['Description'].to_dict()

# --- Read valid error code from ESP32 ---
def get_serial_error_code(port=SERIAL_PORT, baudrate=BAUD_RATE):
    try:
        with serial.Serial(port, baudrate, timeout=2) as ser:
            time.sleep(2)  # Let ESP32 reset
            while True:
                line = ser.readline().decode('utf-8').strip().upper()
                print(f"[ESP32] Received: {line}")
                if line.startswith(("P", "B", "C", "U")) and len(line) == 5:
                    return line
    except Exception as e:
        print("Serial Error:", e)
    return None

# --- Text-to-Speech alert ---
def speak_error(code, description):
    engine = pyttsx3.init()
    engine.say(f"Error Code {code}. {description}")
    engine.runAndWait()

# --- Log errors to CSV ---
def log_error_to_file(code, description):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()},{code},{description}\n")

# --- Update dashboard UI ---
def update_dashboard():
    code = get_serial_error_code()
    if code:
        error_label.config(text=code)
        description = error_dict.get(code, "❌ Description not found in dataset.")
        description_label.config(text=description)
        speak_error(code, description)
        log_error_to_file(code, description)
        error_log.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {code}: {description}\n")
        error_log.see(tk.END)
    else:
        error_label.config(text="--")
        description_label.config(text="No valid error code received.")

    if auto_refresh.get():
        root.after(REFRESH_INTERVAL, update_dashboard)

# --- Create GUI Interface ---
def create_dashboard_ui():
    global root, error_label, description_label, error_log, auto_refresh

    root = tk.Tk()
    root.title("Bike OBD Instrument Cluster")
    root.geometry("600x500")
    root.configure(bg="black")

    canvas = Canvas(root, width=500, height=250, bg="black", highlightthickness=0)
    canvas.pack()
    canvas.create_oval(50, 50, 450, 450, outline="white", width=5)
    canvas.create_text(250, 100, text="OBD ERROR", font=("Arial", 20, "bold"), fill="red")

    error_label = Label(root, text="--", font=("Arial", 20, "bold"), fg="yellow", bg="black")
    error_label.pack(pady=10)

    description_label = Label(root, text="Description: -", font=("Arial", 12), fg="white", bg="black", wraplength=500, justify="center")
    description_label.pack(pady=10)

    Button(root, text="Read Error from ESP32", command=update_dashboard, font=("Arial", 14), bg="red", fg="white").pack(pady=10)

    auto_refresh = tk.BooleanVar()
    tk.Checkbutton(root, text="Auto Refresh", variable=auto_refresh, font=("Arial", 10),
                   bg="black", fg="white", selectcolor="black").pack()

    Label(root, text="Error Log:", font=("Arial", 12, "bold"), bg="black", fg="cyan").pack(pady=5)
    error_log = Text(root, height=8, width=70, bg="black", fg="white")
    error_log.pack()

    Scrollbar(root, command=error_log.yview).pack(side=tk.RIGHT, fill=tk.Y)
    error_log.config(yscrollcommand=lambda f, l: Scrollbar.set)

    root.mainloop()

# --- Main Execution ---
error_dict = load_error_codes(CSV_PATH)
create_dashboard_ui()


