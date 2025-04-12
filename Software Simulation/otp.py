import tkinter as tk
from tkinter import messagebox
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class OTPVerificationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OTP Verification System")
        self.root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")
        
        # Variables
        self.email_var = tk.StringVar()
        self.otp_var = tk.StringVar()
        self.generated_otp = None
        
        # Create Canvas
        self.canvas = tk.Canvas(root, bg="#ffffff", width=450, height=350)
        self.canvas.place(x=25, y=25)
        
        # Heading
        tk.Label(self.canvas, text="OTP Verification", font=("Arial", 20, "bold"), bg="#ffffff").place(x=130, y=30)
        
        # Email Entry
        tk.Label(self.canvas, text="Enter Email:", font=("Arial", 12), bg="#ffffff").place(x=80, y=100)
        self.email_entry = tk.Entry(self.canvas, textvariable=self.email_var, width=25, font=("Arial", 12))
        self.email_entry.place(x=180, y=100)
        
        # Send OTP Button
        self.send_button = tk.Button(self.canvas, text="Send OTP", command=self.send_otp, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.send_button.place(x=180, y=150)
        
        # OTP Entry
        tk.Label(self.canvas, text="Enter OTP:", font=("Arial", 12), bg="#ffffff").place(x=80, y=200)
        self.otp_entry = tk.Entry(self.canvas, textvariable=self.otp_var, width=10, font=("Arial", 12))
        self.otp_entry.place(x=180, y=200)
        
        # Verify Button
        self.verify_button = tk.Button(self.canvas, text="Verify OTP", command=self.verify_otp, bg="#2196F3", fg="white", font=("Arial", 12))
        self.verify_button.place(x=180, y=250)
        
        # Resend Button
        self.resend_button = tk.Button(self.canvas, text="Resend OTP", command=self.send_otp, bg="#FF9800", fg="white", font=("Arial", 12))
        self.resend_button.place(x=300, y=250)
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def send_otp(self):
        email = self.email_var.get()
        if not email:
            messagebox.showerror("Error", "Please enter an email address")
            return
        
        self.generated_otp = self.generate_otp()
        
        # For demonstration, we'll just show the OTP in a messagebox
        # In a real application, you would send this via email or SMS
        messagebox.showinfo("OTP Generated", f"Your OTP is: {self.generated_otp}\n\nIn a real application, this would be sent to your email.")
        
        # Uncomment the below code to actually send email
        # self.send_email_otp(email, self.generated_otp)
    
    def send_email_otp(self, email, otp):
        """Send OTP via email"""
        try:
            # Configure your email settings here
            sender_email = "your_email@gmail.com"
            sender_password = "your_app_password"  # Use app password for Gmail
            
            # Create message
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = email
            message["Subject"] = "Your OTP Verification Code"
            
            # Email body
            body = f"Your OTP verification code is: {otp}"
            message.attach(MIMEText(body, "plain"))
            
            # Connect to server and send email
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, message.as_string())
            
            messagebox.showinfo("Success", "OTP has been sent to your email")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send OTP: {str(e)}")
    
    def verify_otp(self):
        entered_otp = self.otp_var.get()
        if not entered_otp:
            messagebox.showerror("Error", "Please enter the OTP")
            return
        
        if not self.generated_otp:
            messagebox.showerror("Error", "Please generate an OTP first")
            return
        
        if entered_otp == self.generated_otp:
            messagebox.showinfo("Success", "OTP verification successful!")
            # You can add your post-verification logic here
        else:
            messagebox.showerror("Error", "Invalid OTP. Please try again.")

if __name__ == "__main__":
    root = tk.Tk()
    app = OTPVerificationApp(root)
    root.mainloop()
