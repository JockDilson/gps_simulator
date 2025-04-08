import tkinter as tk
from tkinter import scrolledtext
import math
import random
import time
from datetime import datetime
import threading

# Constants
STEP_SIZE = 0.0001  # Small step size for realistic random walk (0.0001 = 11 meters)
EARTH_RADIUS = 6371000  # In meters (for haversine calculation)

# Global flags
simulating = False
previous_coords = None

# --- Utility Functions ---

# Calculate distance in meters between two GPS points
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return EARTH_RADIUS * 2 * math.asin(math.sqrt(a))

# Calculate compass direction between two GPS points
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lat2 = map(math.radians, [lat1, lat2])
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

# Generate speed, heading, altitude, accuracy
def generate_metadata(prev_lat, prev_lon, lat, lon, time_delta):
    distance = haversine(prev_lat, prev_lon, lat, lon)
    speed = distance / time_delta if time_delta > 0 else 0
    heading = calculate_bearing(prev_lat, prev_lon, lat, lon)
    return speed, heading

# --- Simulation Loop ---

# Main loop that emits GPS data every second
def simulate_loop(start_lat, start_lon, update_callback):
    global simulating, previous_coords

    lat, lon = start_lat, start_lon
    previous_coords = (lat, lon)
    last_time = time.time()

    while simulating:
        # Small random walk step
        lat += random.uniform(-STEP_SIZE, STEP_SIZE)
        lon += random.uniform(-STEP_SIZE, STEP_SIZE)

        # Time since last point
        current_time = time.time()
        time_delta = current_time - last_time
        last_time = current_time

        # Generate extra metadata
        speed, heading= generate_metadata(
            previous_coords[0], previous_coords[1], lat, lon, time_delta
        )
        previous_coords = (lat, lon)

        # Final output payload
        payload = {
            "device_id": "mock_tracker_01",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "speed": round(speed, 2),
            "heading": round(heading, 2)
        }

        # Send to UI in thread-safe way
        update_callback(payload)
        time.sleep(1)

# --- UI Functions ---

# Start simulation in background thread
def start_simulation(output_widget):
    global simulating
    if not simulating:
        simulating = True

        # Safe way to update tkinter widgets from thread
        def update_output(payload):
            output_widget.after(0, lambda: (
                output_widget.insert(tk.END, str(payload) + "\n"),
                output_widget.see(tk.END)
            ))

        thread = threading.Thread(target=simulate_loop, args=(12.9356, 77.6145, update_output))
        thread.daemon = True
        thread.start()

# Stop the simulation
def stop_simulation():
    global simulating
    simulating = False

# Clear output area
def clear_output(output_widget):
    output_widget.delete(1.0, tk.END)

# --- UI Setup ---

root = tk.Tk()
root.title("GPS Simulator")
root.geometry("650x450")

# Output display area
output = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 10))
output.pack(padx=10, pady=10, expand=True, fill="both")

# Button controls
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

start_btn = tk.Button(btn_frame, text="▶ Start", width=10, command=lambda: start_simulation(output))
start_btn.grid(row=0, column=0, padx=5)

stop_btn = tk.Button(btn_frame, text="⏹ Stop", width=10, command=stop_simulation)
stop_btn.grid(row=0, column=1, padx=5)

clear_btn = tk.Button(btn_frame, text="🧹 Clear", width=10, command=lambda: clear_output(output))
clear_btn.grid(row=0, column=2, padx=5)

# Start the GUI event loop
root.mainloop()
