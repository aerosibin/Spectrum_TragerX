import RPi.GPIO as GPIO
import time
import threading
import math

class UltrasonicSensor:
    def __init__(self, trigger_pin, echo_pin, name="sensor", angle_offset=0):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.name = name
        self.angle_offset = angle_offset  # Angle offset relative to robot front
        self.distance = 0
        self.running = False
        self.thread = None
        
        # Setup GPIO pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # Ensure trigger is low
        GPIO.output(self.trigger_pin, False)
        time.sleep(0.1)  # Allow sensor to settle
    
    def measure_distance(self):
        # Send 10us pulse to trigger
        GPIO.output(self.trigger_pin, False)
        time.sleep(0.000002)  # 2us delay to ensure clean pulse
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)  # 10us pulse
        GPIO.output(self.trigger_pin, False)
        
        # Wait for echo to start
        pulse_start = time.time()
        timeout = pulse_start + 0.1  # 100ms timeout
        
        while GPIO.input(self.echo_pin) == 0 and time.time() < timeout:
            pulse_start = time.time()
        
        # Wait for echo to end
        pulse_end = time.time()
        timeout = pulse_end + 0.1  # 100ms timeout
        
        while GPIO.input(self.echo_pin) == 1 and time.time() < timeout:
            pulse_end = time.time()
        
        # Calculate distance
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # Speed of sound = 343m/s
        distance = round(distance, 2)
        
        # Limit to valid range (2cm to 400cm)
        if distance > 400:
            distance = 400
        elif distance < 2:
            distance = 0
            
        return distance
    
    def continuous_measurement(self):
        self.running = True
        while self.running:
            self.distance = self.measure_distance()
            time.sleep(0.1)  # 10 measurements per second
    
    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.continuous_measurement)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(1.0)
    
    def get_distance(self):
        return self.distance
    
    def get_angle(self):
        return self.angle_offset
    
    def cleanup(self):
        self.stop()
        # GPIO cleanup is handled by the main program

class ServoSensor(UltrasonicSensor):
    def __init__(self, trigger_pin, echo_pin, servo_pin, name="servo_sensor"):
        super().__init__(trigger_pin, echo_pin, name)
        self.servo_pin = servo_pin
        self.current_angle = 90  # Start at center position
        self.scan_direction = 1  # 1 for increasing angle, -1 for decreasing
        self.min_angle = 0
        self.max_angle = 180
        self.step_angle = 10  # Degrees to move per step
        
        # Setup servo
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.servo_pin, 50)  # 50Hz frequency
        self.pwm.start(self._angle_to_duty_cycle(self.current_angle))
        time.sleep(0.5)  # Allow servo to reach position
    
    def _angle_to_duty_cycle(self, angle):
        # Convert angle (0-180) to duty cycle (2.5-12.5)
        return 2.5 + (angle / 18)
    
    def set_angle(self, angle):
        # Ensure angle is within bounds
        angle = max(self.min_angle, min(self.max_angle, angle))
        self.current_angle = angle
        self.pwm.ChangeDutyCycle(self._angle_to_duty_cycle(angle))
        time.sleep(0.1)  # Allow servo to reach position
        
    def scan_step(self):
        # Move servo one step in the current scan direction
        next_angle = self.current_angle + (self.step_angle * self.scan_direction)
        
        # If we've reached a limit, change direction
        if next_angle >= self.max_angle or next_angle <= self.min_angle:
            self.scan_direction *= -1
            next_angle = self.current_angle + (self.step_angle * self.scan_direction)
        
        self.set_angle(next_angle)
        return self.current_angle
    
    def get_angle(self):
        return self.current_angle
    
    def cleanup(self):
        super().cleanup()
        self.pwm.stop()

