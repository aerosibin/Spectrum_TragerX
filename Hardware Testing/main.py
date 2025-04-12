import pygame
import math
import RPi.GPIO as GPIO
import time
import threading
import numpy as np
import cv2
from pyzbar.pyzbar import decode

# Import our modules
from sensor import UltrasonicSensor
from motor import MotorDriver
from slam import GridBasedSLAM
from a_star import AStar
from qr_scanner import QRScanner

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define GPIO pins for sensors
# Front Ultrasonic Sensor (on Servo)
FRONT_TRIG = 5
FRONT_ECHO = 6

# Left Ultrasonic Sensor
LEFT_TRIG = 13
LEFT_ECHO = 19

# Right Ultrasonic Sensor
RIGHT_TRIG = 12
RIGHT_ECHO = 16

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
UI_HEIGHT = 150
MAP_HEIGHT = SCREEN_HEIGHT - UI_HEIGHT

# Create pygame display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('TragerX SLAM Simulator with HC-SR04 Sensors')

# Fonts
font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)

# Initialize components
front_sensor = UltrasonicSensor(FRONT_TRIG, FRONT_ECHO, "front_sensor")
left_sensor = UltrasonicSensor(LEFT_TRIG, LEFT_ECHO, "left_sensor", angle_offset=-90)
right_sensor = UltrasonicSensor(RIGHT_TRIG, RIGHT_ECHO, "right_sensor", angle_offset=90)
sensors = [front_sensor, left_sensor, right_sensor]

motor_driver = MotorDriver()  # Uses Arduino via serial
slam = GridBasedSLAM(80, 60)
qr_scanner = QRScanner(0)  # Use camera 0

# Robot position and angle
robot_position = [SCREEN_WIDTH // 2, UI_HEIGHT + MAP_HEIGHT // 2]
robot_angle = 0
robot_radius = 20

# Initialize pathfinder
pathfinder = None

# Colors
BACKGROUND_COLOR = (0, 0, 0)
UI_BACKGROUND_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)
CLEAR_SPACE_COLOR = (128, 128, 128)
OBSTACLE_FIRST_DETECTED_COLOR = (255, 255, 0)
OBSTACLE_CONFIRMED_COLOR = (0, 255, 0)
ROBOT_COLOR = (0, 0, 255)
PATH_COLOR = (255, 255, 255)
PLANNED_PATH_COLOR = (255, 0, 255)

# Define counter positions
counter_positions = {
    "source": [SCREEN_WIDTH // 2, UI_HEIGHT + MAP_HEIGHT // 2],
    "counter1": [SCREEN_WIDTH // 2 - 200, UI_HEIGHT + MAP_HEIGHT // 2 - 150],
    "counter2": [SCREEN_WIDTH // 2 + 200, UI_HEIGHT + MAP_HEIGHT // 2 - 150],
    "counter3": [SCREEN_WIDTH // 2, UI_HEIGHT + MAP_HEIGHT // 2 + 200]
}

# Robot state
current_path = None
path_index = 0
destination = None
workflow_state = "idle"
path_points = []
front_angle = 90  # Default servo angle (90 = center/stop)
servo_scan_direction = 1  # 1 = clockwise, -1 = counter-clockwise
last_servo_update = time.time()

# Start sensors
for sensor in sensors:
    sensor.start()

# Main loop
running = True
clock = pygame.time.Clock()

try:
    # Initial servo position (stop)
    motor_driver.set_servo_speed(90)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE and workflow_state == "idle":
                    workflow_state = "scanning_qr"
                    print("Starting QR code scanning...")
	
        # Handle different workflow states
        if workflow_state == "scanning_qr":
            qr_data = qr_scanner.scan()
            if qr_data:
                print(f"QR Code detected: {qr_data}")
                workflow_state = "navigating"
            else:
            	print(f"QR Code detected: 2")
            	workflow_state="navigating"
                
        elif workflow_state == "navigating":
            if destination is None:
                # Set destination based on QR code (default to counter1 if not specified)
                counter = f"counter{qr_data}" if qr_data in ["1", "2", "3"] else "counter1"
                destination = counter_positions[counter]
                print(f"Navigating to {counter}")
        
        # Update servo position for scanning
        current_time = time.time()
        if current_time - last_servo_update > 0.5:  # Update every 0.5 seconds
            # Oscillate servo between clockwise and counter-clockwise
            if servo_scan_direction == 1:
                front_angle = 110  # Clockwise rotation
                motor_driver.set_servo_speed(front_angle)
            else:
                front_angle = 70   # Counter-clockwise rotation
                motor_driver.set_servo_speed(front_angle)
                
            # Change direction every few seconds
            if current_time - last_servo_update > 3:
                servo_scan_direction *= -1
                last_servo_update = current_time
        
        # Get distances from all sensors
        front_distance = front_sensor.get_distance()
        left_distance = left_sensor.get_distance()
        right_distance = right_sensor.get_distance()
        
        # Update SLAM with sensor data
        # Front sensor (on servo)
        sensor_angle = (robot_angle + (front_angle - 90) * 2) % 360  # Adjust for servo orientation
        slam.sensor_update(robot_position, sensor_angle, front_distance)
        
        # Left sensor
        slam.sensor_update(robot_position, (robot_angle - 90) % 360, left_distance)
        
        # Right sensor
        slam.sensor_update(robot_position, (robot_angle + 90) % 360, right_distance)

        # Initialize or update pathfinder
        if pathfinder is None:
            pathfinder = AStar(slam.occupancy_grid)
        else:
            pathfinder.grid = slam.occupancy_grid

        # Path planning and navigation
        if workflow_state == "navigating" and destination:
            if current_path is None or path_index >= len(current_path):
                start = slam.world_to_grid(robot_position)
                end = slam.world_to_grid(destination)
                current_path = pathfinder.find_path(start, end)
                path_index = 0
                print(f"Path planned with {len(current_path) if current_path else 0} points")

            if current_path and path_index < len(current_path):
                target = current_path[path_index]
                target_world = [target[0] * 10 + 5, target[1] * 10 + 5]
                
                # Calculate angle and distance to target
                dx = target_world[0] - robot_position[0]
                dy = target_world[1] - robot_position[1]
                target_angle = math.degrees(math.atan2(dy, dx)) % 360
                distance = math.sqrt(dx**2 + dy**2)

                # Rotate towards target
                angle_diff = (target_angle - robot_angle) % 360
                if angle_diff > 180:
                    angle_diff -= 360
                
                if abs(angle_diff) > 5:
                    if angle_diff > 0:
                        motor_driver.turn_right(30)
                        robot_angle = (robot_angle + 2) % 360
                    else:
                        motor_driver.turn_left(30)
                        robot_angle = (robot_angle - 2) % 360
                else:
                    # Move forward
                    motor_driver.move_forward(50)
                    robot_position[0] += 2 * math.cos(math.radians(robot_angle))
                    robot_position[1] += 2 * math.sin(math.radians(robot_angle))

                # Check if target reached
                if distance < 15:
                    path_index += 1
                    if path_index >= len(current_path):
                        motor_driver.stop()
                        workflow_state = "idle"
                        destination = None
                        current_path = None
                        print("Destination reached!")
            else:
                motor_driver.stop()
                # Recalculate path if no valid path found
                current_path = None
        else:
            # Handle manual control when not navigating
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                motor_driver.move_forward(50)
                robot_position[0] += 2 * math.cos(math.radians(robot_angle))
                robot_position[1] += 2 * math.sin(math.radians(robot_angle))
            elif keys[pygame.K_DOWN]:
                motor_driver.move_backward(50)
                robot_position[0] -= 2 * math.cos(math.radians(robot_angle))
                robot_position[1] -= 2 * math.sin(math.radians(robot_angle))
            elif keys[pygame.K_LEFT]:
                motor_driver.turn_left(30)
                robot_angle = (robot_angle - 2) % 360
            elif keys[pygame.K_RIGHT]:
                motor_driver.turn_right(30)
                robot_angle = (robot_angle + 2) % 360
            else:
                motor_driver.stop()

        # Track robot path
        path_points.append((int(robot_position[0]), int(robot_position[1])))
        if len(path_points) > 100:  # Limit path length
            path_points.pop(0)

        # Clear the screen
        screen.fill(BACKGROUND_COLOR)

        # Draw UI section
        pygame.draw.rect(screen, UI_BACKGROUND_COLOR, pygame.Rect(0, 0, SCREEN_WIDTH, UI_HEIGHT))

        # Display telemetry data
        title_text = font.render("TragerX SLAM Simulator with HC-SR04 Sensors", True, TEXT_COLOR)
        status_text = font.render(f"Status: {workflow_state}", True, TEXT_COLOR)
        position_text = font.render(f"Position: ({int(robot_position[0])}, {int(robot_position[1])})", True, TEXT_COLOR)
        angle_text = font.render(f"Angle: {int(robot_angle)}°", True, TEXT_COLOR)
        
        screen.blit(title_text, (10, 10))
        screen.blit(status_text, (10, 40))
        screen.blit(position_text, (10, 70))
        screen.blit(angle_text, (10, 100))

        # Draw SLAM map
        slam_map = slam.get_map()
        for x in range(slam_map.shape[0]):
            for y in range(slam_map.shape[1]):
                rect_x = x * 10
                rect_y = y * 10 + UI_HEIGHT
                if rect_y < SCREEN_HEIGHT:  # Ensure we're drawing within screen bounds
                    if slam_map[x, y] == 1:  # Clear space
                        pygame.draw.rect(screen, CLEAR_SPACE_COLOR, pygame.Rect(rect_x, rect_y, 10, 10), 1)
                    elif slam_map[x, y] == 2:  # First detected obstacle
                        pygame.draw.rect(screen, OBSTACLE_FIRST_DETECTED_COLOR, pygame.Rect(rect_x, rect_y, 10, 10))
                    elif slam_map[x, y] == 3:  # Confirmed obstacle
                        pygame.draw.rect(screen, OBSTACLE_CONFIRMED_COLOR, pygame.Rect(rect_x, rect_y, 10, 10))

        # Draw robot
        pygame.draw.circle(screen, ROBOT_COLOR, (int(robot_position[0]), int(robot_position[1])), robot_radius)
        end_line = (int(robot_position[0] + 30 * math.cos(math.radians(robot_angle))),
                    int(robot_position[1] + 30 * math.sin(math.radians(robot_angle))))
        pygame.draw.line(screen, ROBOT_COLOR, (int(robot_position[0]), int(robot_position[1])), end_line, 2)
        
        # Draw servo direction indicator
        servo_angle = (robot_angle + (front_angle - 90) * 2) % 360
        servo_line = (int(robot_position[0] + 25 * math.cos(math.radians(servo_angle))),
                      int(robot_position[1] + 25 * math.sin(math.radians(servo_angle))))
        pygame.draw.line(screen, (255, 0, 0), (int(robot_position[0]), int(robot_position[1])), servo_line, 2)

        # Draw the robot's path
        if len(path_points) > 1:
            pygame.draw.lines(screen, PATH_COLOR, False, path_points, 2)
        
        # Draw the planned path if available
        if current_path:
            path_screen_points = [(p[0] * 10 + 5, p[1] * 10 + 5 + UI_HEIGHT) for p in current_path]
            pygame.draw.lines(screen, PLANNED_PATH_COLOR, False, path_screen_points, 2)
            
            # Highlight current target point
            if path_index < len(current_path):
                target = current_path[path_index]
                target_x = target[0] * 10 + 5
                target_y = target[1] * 10 + 5 + UI_HEIGHT
                pygame.draw.circle(screen, (255, 0, 0), (target_x, target_y), 5)
        
        # Draw destination if set
        if destination:
            pygame.draw.circle(screen, (0, 255, 255), (int(destination[0]), int(destination[1])), 10, 2)
        
        # Draw counter positions
        for name, pos in counter_positions.items():
            pygame.draw.circle(screen, (0, 255, 255), (int(pos[0]), int(pos[1])), 8, 2)
            label = small_font.render(name, True, TEXT_COLOR)
            screen.blit(label, (int(pos[0]) + 10, int(pos[1]) - 10))
        
        # Display sensor readings
        front_text = small_font.render(f"Front: {front_distance} cm", True, TEXT_COLOR)
        left_text = small_font.render(f"Left: {left_distance} cm", True, TEXT_COLOR)
        right_text = small_font.render(f"Right: {right_distance} cm", True, TEXT_COLOR)
        servo_text = small_font.render(f"Servo: {front_angle}°", True, TEXT_COLOR)
        
        screen.blit(front_text, (SCREEN_WIDTH - 150, 10))
        screen.blit(left_text, (SCREEN_WIDTH - 150, 40))
        screen.blit(right_text, (SCREEN_WIDTH - 150, 70))
        screen.blit(servo_text, (SCREEN_WIDTH - 150, 100))
        
        # Update display
        pygame.display.flip()
        
        # Control frame rate
        clock.tick(30)

except KeyboardInterrupt:
    print("Program terminated by user")
finally:
    # Clean up
    for sensor in sensors:
        sensor.cleanup()
    motor_driver.cleanup()
    qr_scanner.stop()
    GPIO.cleanup()
    pygame.quit()
