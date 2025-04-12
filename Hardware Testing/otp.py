import random
import time
import tkinter as tk
from tkinter import messagebox

class OTPSystem:
    def __init__(self):
        self.current_otp = None
        self.generation_time = None
        self.expiry_time = 30  # OTP expires after 30 seconds

    def generate_otp(self):
        """Generate a 4-digit OTP."""
        self.current_otp = str(random.randint(1000, 9999))
        self.generation_time = time.time()
        return self.current_otp

    def verify_otp(self, entered_otp):
        """Verify if entered OTP is correct and not expired."""
        if not self.current_otp:
            return False, "No OTP has been generated."

        # Check if OTP has expired
        if time.time() - self.generation_time > self.expiry_time:
            return False, "OTP has expired."

        # Check if OTP matches
        if entered_otp == self.current_otp:
            self.current_otp = None  # Invalidate OTP after successful verification
            return True, "OTP verification successful."
        else:
            return False, "Invalid OTP."

    def is_expired(self):
        """Check if the current OTP has expired."""
        if not self.current_otp or not self.generation_time:
            return True

        return time.time() - self.generation_time > self.expiry_time

    def time_remaining(self):
        """Get remaining time before OTP expires (in seconds)."""
        if not self.current_otp or not self.generation_time:
            return 0

        remaining = self.expiry_time - (time.time() - self.generation_time)
        return max(0, int(remaining))


class OTPVerificationApp:
    def __init__(self, root, otp_system, callback=None):
        """
        Initialize the OTP verification app.

        Args:
            root: Tkinter root window.
            otp_system: Instance of the OTPSystem class.
            callback: Function to call after verification (optional).
        """
        self.root = root
        self.otp_system = otp_system
        self.callback = callback

        # Configure window properties
        self.root.title("OTP Verification")
        self.root.geometry("400x300")
        self.root.configure(bg="#f0f0f0")

        # Variables for user input and status display
        self.otp_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.status_var.set("Enter the OTP below")

        # Create UI elements
        self.create_ui()

    def create_ui(self):
        """Create the UI elements for the OTP verification app."""
        
        # Canvas for background
        canvas = tk.Canvas(self.root, bg="#ffffff", width=350, height=250)
        canvas.place(x=25, y=25)

        # Heading label
        tk.Label(canvas, text="OTP Verification", font=("Arial", 18, "bold"), bg="#ffffff").place(x=100, y=20)

        # Status label
        status_label = tk.Label(canvas, textvariable=self.status_var, font=("Arial", 12), bg="#ffffff", fg="#333333")
        status_label.place(x=50, y=60)

        # Timer label
        timer_label = tk.Label(canvas, text="Time remaining:", font=("Arial", 12), bg="#ffffff", fg="#FF5733")
        timer_label.place(x=50, y=90)
        
        # Timer variable (updates dynamically)
        timer_var = tk.StringVar()
        
        def update_timer():
            remaining = self.otp_system.remaining

