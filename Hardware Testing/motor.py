import serial
import time
import threading

class MotorDriver:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        """
        Initialize motor driver that communicates with Arduino via serial
        
        Args:
            port: Serial port where Arduino is connected
            baudrate: Communication speed (must match Arduino sketch)
        """
        self.port = port
        self.baudrate = baudrate
        self.arduino = None
        self.connected = False
        self.lock = threading.Lock()  # Thread lock for serial communication
        
        # Connect to Arduino
        self.connect()
        
        # Speed factors for simulation
        self._speed_factor = 2
        self._rotation_speed_factor = 2
    
    def connect(self):
        """Establish connection with Arduino"""
        try:
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            # Read initial message from Arduino
            initial_message = self.arduino.readline().decode('utf-8').strip()
            print(f"Arduino says: {initial_message}")
            
            self.connected = True
            print(f"Connected to Arduino on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            self.connected = False
            return False
    
    def send_command(self, command):
        """Send command to Arduino and wait for acknowledgment"""
        if not self.connected:
            print(f"Not connected to Arduino. Command not sent: {command}")
            return False
        
        with self.lock:
            try:
                # Send command with newline terminator
                self.arduino.write(f"{command}\n".encode())
                
                # Wait for acknowledgment
                response = self.arduino.readline().decode('utf-8').strip()
                print(f"Arduino response: {response}")
                
                return "OK" in response
            except Exception as e:
                print(f"Error sending command to Arduino: {e}")
                self.connected = False
                return False
    
    def move_forward(self, speed=100):
        """Move robot forward"""
        # Convert speed from 0-100 to 0-255 for Arduino
        arduino_speed = int(speed * 2.55)
        return self.send_command(f"FORWARD:{arduino_speed}")
    
    def move_backward(self, speed=100):
        """Move robot backward"""
        # Convert speed from 0-100 to 0-255 for Arduino
        arduino_speed = int(speed * 2.55)
        return self.send_command(f"BACKWARD:{arduino_speed}")
    
    def turn_left(self, speed=100):
        """Turn robot left (counter-clockwise)"""
        # Convert speed from 0-100 to 0-255 for Arduino
        arduino_speed = int(speed * 2.55)
        return self.send_command(f"LEFT:{arduino_speed}")
    
    def turn_right(self, speed=100):
        """Turn robot right (clockwise)"""
        # Convert speed from 0-100 to 0-255 for Arduino
        arduino_speed = int(speed * 2.55)
        return self.send_command(f"RIGHT:{arduino_speed}")
    
    def stop(self):
        """Stop all motors"""
        return self.send_command("STOP")
    
    def set_servo_speed(self, speed):
        """
        Set continuous rotation servo speed
        
        Args:
            speed: 0-180 (90=stop, <90=CCW, >90=CW)
        """
        return self.send_command(f"SERVO:{speed}")
    
    def speed_factor(self):
        """Return speed factor for simulation"""
        return self._speed_factor
    
    def rotation_speed_factor(self):
        """Return rotation speed factor for simulation"""
        return self._rotation_speed_factor
    
    def cleanup(self):
        """Clean up and close connection"""
        self.stop()
        self.set_servo_speed(90)  # Stop servo
        
        if self.arduino and self.connected:
            self.arduino.close()
            print("Arduino connection closed")	
