import time
import serial
import joblib
import numpy as np
import pandas as pd
import re
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# Load the trained model and scaler
model, scaler = joblib.load(r"C:\Users\kannan\Downloads\battery_life_model.pkl")

def start_prediction():
    purchase_date_str = entry_date.get()
    initial_voltage = float(entry_voltage.get())
    
    # Convert purchase date to datetime object
    purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")
    current_date = datetime.now()
    days_used = (current_date - purchase_date).days
    
    # Configure the serial port (COM6, 9600 baud rate)
    ser = serial.Serial('COM6', 115200, timeout=1)
    time.sleep(2)  # Wait for connection to establish
    
    lbl_status.config(text="Collecting data from COM6...")
    root.update()
    
    # Collect data for 1 minute
    data_list = []
    start_time = time.time()
    while time.time() - start_time < 60:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                matches = re.findall(r"[-+]?\d*\.\d+|\d+", line)
                if len(matches) == 3:
                    data_list.append([float(matches[0]), float(matches[1]), float(matches[2])])
        except Exception as e:
            lbl_status.config(text=f"Error reading serial data: {e}")
            root.update()
    
    ser.close()
    
    if len(data_list) > 0:
        avg_data = np.mean(data_list, axis=0)  # Take the average over 1 minute
        measured_voltage = avg_data[0]
        
        # Compare with initial voltage
        voltage_drop = initial_voltage - measured_voltage
        
        # Create a dataframe with only the required features
        new_data = pd.DataFrame([[measured_voltage, avg_data[1], avg_data[2], days_used, voltage_drop]],
                                columns=["Measured Voltage (V)", "Measured Current (A)", "Temperature (C)", "Days Used", "Voltage Drop"])
        new_data_trimmed = new_data[["Measured Voltage (V)", "Measured Current (A)", "Temperature (C)"]]
        
        # Scale input data
        new_data_scaled = scaler.transform(new_data_trimmed)
        
        # Make predictions
        predictions = model.predict(new_data_scaled)
        battery_health, cycle_life, lifespan = predictions[0]
        
        # Display results
        lbl_status.config(text=f"Battery Health: {battery_health:.2f}%\nCycle Life: {cycle_life:.0f} cycles\nLifespan: {lifespan:.2f} hours\nVoltage Drop: {voltage_drop:.2f} V over {days_used} days")
    else:
        lbl_status.config(text="No valid data collected from COM6.")
    
# Create GUI window
root = tk.Tk()
root.title("Battery Health Predictor")
root.geometry("400x400")
root.configure(bg='black')

tk.Label(root, text="Enter Battery Purchase Date (YYYY-MM-DD):", bg='black', fg='white').pack()
entry_date = tk.Entry(root)
entry_date.pack()

tk.Label(root, text="Enter Battery Initial Voltage (V):", bg='black', fg='white').pack()
entry_voltage = tk.Entry(root)
entry_voltage.pack()

tk.Button(root, text="Start Prediction", command=start_prediction, bg='green', fg='white').pack(pady=10)

lbl_status = tk.Label(root, text="", bg='black', fg='white')
lbl_status.pack()

root.mainloop()

