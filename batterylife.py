import pickle
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import serial
import time
import threading

# --- Load Model ---
with open("battery_health_model.pkl", "rb") as file:
    model, feature_names = pickle.load(file)

# --- Parse ESP32 Data ---
def parse_esp_data(line):
    try:
        parts = line.split('|')
        voltage = float(parts[0].split(':')[1].strip().replace('V', ''))
        current = float(parts[1].split(':')[1].strip().replace('A', ''))
        temperature = float(parts[2].split(':')[1].strip())
        return voltage, current, temperature
    except:
        return None, None, None

# --- Get Average Sensor Data ---
def get_average_sensor_data(port='COM6', baudrate=115200, duration=60, callback=None):
    def read_loop():
        ser = serial.Serial(port, baudrate, timeout=5)
        voltages, currents, temperatures = [], [], []
        start_time = time.time()

        while time.time() - start_time < duration:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "Measured Voltage" in line:
                    v, c, t = parse_esp_data(line)
                    if v is not None:
                        voltages.append(v)
                        currents.append(c)
                        temperatures.append(t)

        ser.close()

        if voltages:
            avg_v = sum(voltages) / len(voltages)
            avg_c = sum(currents) / len(currents)
            avg_t = sum(temperatures) / len(temperatures)
            callback(avg_v, avg_c, avg_t)
        else:
            callback(None, None, None)

    thread = threading.Thread(target=read_loop)
    thread.start()

# --- GUI App ---
class BatteryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🔋 Bike Battery Health Monitor")
        self.geometry("500x450")
        self.configure(bg="#1e1e1e")

        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))

        ttk.Label(self, text="🔌 Initial Voltage").pack(pady=5)
        self.init_voltage_entry = ttk.Entry(self)
        self.init_voltage_entry.pack()

        ttk.Label(self, text="📅 Purchase Date (YYYY-MM-DD)").pack(pady=5)
        self.purchase_date_entry = ttk.Entry(self)
        self.purchase_date_entry.pack()

        self.status_label = tk.Label(self, text="", fg="yellow", bg="#1e1e1e", font=("Segoe UI", 10))
        self.status_label.pack(pady=10)

        ttk.Button(self, text="⚙️ Start Prediction", command=self.run_prediction).pack(pady=15)

        self.result_health = tk.Label(self, text="🔋 Health: --%", fg="lime", bg="#1e1e1e", font=("Courier", 14))
        self.result_health.pack(pady=5)

        self.result_cycles = tk.Label(self, text="🔁 Cycle Count: --", fg="aqua", bg="#1e1e1e", font=("Courier", 14))
        self.result_cycles.pack(pady=5)

        self.result_life = tk.Label(self, text="⏳ Remaining Life: -- days", fg="orange", bg="#1e1e1e", font=("Courier", 14))
        self.result_life.pack(pady=5)

    def run_prediction(self):
        try:
            initial_voltage = float(self.init_voltage_entry.get())
            purchase_date = self.purchase_date_entry.get()
            datetime.strptime(purchase_date, "%Y-%m-%d")  # basic validation
        except Exception as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return

        self.status_label.config(text="⏳ Reading sensor data for 60 seconds...")
        get_average_sensor_data(callback=lambda v, c, t: self.display_results(v, c, t, initial_voltage))

    def display_results(self, voltage, current, temperature, initial_voltage):
        if voltage is None:
            self.status_label.config(text="⚠️ Failed to read data from ESP32")
            return

        voltage_drop = initial_voltage - voltage

        input_data = {feature: 0 for feature in feature_names}
        if "Voltage_Drop" in input_data:
            input_data["Voltage_Drop"] = voltage_drop
        if "Current" in input_data:
            input_data["Current"] = current
        if "Temperature" in input_data:
            input_data["Temperature"] = temperature

        input_df = pd.DataFrame([input_data])
        prediction = model.predict(input_df)

        health, cycles, life = prediction[0]
        self.status_label.config(text="✅ Prediction complete!")

        self.result_health.config(text=f"🔋 Health: {round(health, 2)}%")
        self.result_cycles.config(text=f"🔁 Cycle Count: {int(cycles)}")
        self.result_life.config(text=f"⏳ Remaining Life: {int(life)} days")

if __name__ == "__main__":
    app = BatteryApp()
    app.mainloop() 


