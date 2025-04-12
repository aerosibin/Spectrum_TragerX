import cv2
from pyzbar.pyzbar import decode
import time

class QRScanner:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.last_scan = None
        self.last_scan_time = 0
    
    def start(self):
        """Start the camera"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
    
    def scan(self):
        """Scan for QR codes and return decoded data"""
        if not self.cap or not self.cap.isOpened():
            self.start()
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Decode QR codes in the frame
        qr_codes = decode(frame)
        
        # Return the first QR code data if found
        if qr_codes:
            qr_data = qr_codes[0].data.decode('utf-8')
            self.last_scan = qr_data
            self.last_scan_time = time.time()
            return qr_data
        
        return None
    
    def get_frame(self):
        """Get current camera frame"""
        if not self.cap or not self.cap.isOpened():
            self.start()
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        return frame
    
    def stop(self):
        """Stop the camera"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

