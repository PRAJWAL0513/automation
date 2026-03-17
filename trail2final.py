import sys
import threading
import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Global variable for the production counter
counter = 0
flag_connected = 0

# MQTT Callback functions
def on_connect(client, userdata, flags, rc):
    global flag_connected
    flag_connected = 1
    client.subscribe("esp32/sensor1")  # Replace with your MQTT topic
    print("Connected to MQTT server")

def on_disconnect(client, userdata, rc):
    global flag_connected
    flag_connected = 0
    print("Disconnected from MQTT server")

def callback_esp32_sensor1(client, userdata, msg):
    global counter
    if msg.payload.decode('utf-8') == '1':  # Check if the payload matches '1'
        counter += 1
        print('ESP sensor1 data: ', counter)
        
        # Update the GUI safely using QTimer
        QTimer.singleShot(0, lambda: userdata.update_production(counter))

# PyQt GUI Class
class MachinePerformance(QWidget):
    def __init__(self, mqtt_client):
        super().__init__()
        
        self.mqtt_client = mqtt_client
        self.mqtt_client.user_data_set(self)  # Set this GUI as user data for the callback
        
        self.setWindowTitle('Machine Performance')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #4d94ff;")
        
        # Apply a fixed monospaced font (Courier) and black color for all text
        self.setStyleSheet("""
            QWidget {
                font-family: Courier;
                font-size: 12pt;
                color: black;
            }
            QLabel, QLineEdit {
                background-color: white;
                border: 1px solid black;
            }
        """)

        self.layout = QVBoxLayout()
        
        # SHIFT Label
        self.shift_label = QLabel("SHIFT", self)
        self.shift_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.shift_label)
        
        # MACHINE Label
        self.machine_label = QLabel("MACHINE 1", self)
        self.machine_label.setAlignment(Qt.AlignCenter)
        self.machine_label.setStyleSheet("background-color: white; border: 2px solid black;")
        self.layout.addWidget(self.machine_label)
        
        # Target, Actual, Delta, Production input fields
        self.data_layout = QVBoxLayout()
        self.add_data_input("TARGET")
        self.add_data_input("ACTUAL", readonly=True)
        self.add_data_input("DELTA", readonly=True)
        self.add_data_input("PRODUCTION", readonly=True)
        
        self.layout.addLayout(self.data_layout)
        
        # Graph canvas for 3D plot
        self.canvas = FigureCanvas(plt.Figure(figsize=(5, 3)))
        self.layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.add_subplot(111, projection='3d')
        
        self.update_graph(4, 0)  # Default values for the first graph
        
        # Set a timer to automatically refresh the graph every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_graph)
        self.timer.start(1000)  # Refresh every 1 second
        
        self.setLayout(self.layout)
        self.setMinimumSize(800, 600)  # Ensure a minimum window size

    def add_data_input(self, label_text, readonly=False):
        """Helper function to add input rows for TARGET, ACTUAL, DELTA, and PRODUCTION."""
        label = QLabel(label_text, self)
        label.setAlignment(Qt.AlignLeft)
        
        input_field = QLineEdit(self)
        input_field.setFont(QFont("Courier", 14))  # Apply Courier font for input fields
        if readonly:
            input_field.setReadOnly(True)
        
        setattr(self, f"{label_text.lower()}_input", input_field)
        
        row_layout = QHBoxLayout()
        row_layout.addWidget(label)
        row_layout.addWidget(input_field)
        
        self.data_layout.addLayout(row_layout)
    
    def update_production(self, new_counter):
        """Update the ACTUAL and PRODUCTION fields with the counter value."""
        self.actual_input.setText(str(new_counter))
        self.production_input.setText(str(new_counter))
        try:
            target = float(self.target_input.text())
            delta = target - new_counter
            self.delta_input.setText(str(delta))
            self.update_graph(target, new_counter)
        except ValueError:
            pass  # Handle cases where TARGET input is not valid

    def refresh_graph(self):
        """Refresh the graph using the latest counter and target values.""" 
        try:
            target = float(self.target_input.text())
            actual = counter  # Use the global counter for ACTUAL
            delta = target - actual
            self.actual_input.setText(str(actual))
            self.delta_input.setText(str(delta))
            self.update_graph(target, actual)
        except ValueError:
            # Handle case when input fields are not valid numbers
            self.delta_input.setText("Invalid Input")
    
    def update_graph(self, target, actual):
        """Redraw the 3D bar chart with TARGET, ACTUAL, and DELTA values."""
        delta = target - actual
        
        # Clear previous graph
        self.ax.clear()
        
        # Data for 3D bars
        colors = ['#0000FF', '#FF8000', '#C0C0C0']
        labels = ['TARGET', 'ACTUAL', 'DELTA']
        values = [target, actual, delta]
        
        x = [0, 1, 2]  # x positions
        y = [0, 0, 0]  # y positions
        z = [0, 0, 0]  # z base (starts from 0)
        dx = dy = [0.4, 0.4, 0.4]  # Bar width and depth
        dz = values  # Heights of the bars
        
        # Plot 3D bars
        self.ax.bar3d(x, y, z, dx, dy, dz, color=colors)
        
        # Configure axes
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(labels)
        self.ax.set_zlim(0, max(target, actual, delta) + 1)
        
        # Update canvas
        self.canvas.draw()

def run_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.message_callback_add("esp32/sensor1", callback_esp32_sensor1)
    client.connect("mqtt_broker_address", 1883, 60)  # Replace with your broker's address
    client.loop_start()
    return client

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mqtt_client = run_mqtt_client()
    window = MachinePerformance(mqtt_client)
    window.show()
    sys.exit(app.exec_())
