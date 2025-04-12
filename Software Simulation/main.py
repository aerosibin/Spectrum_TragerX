import pygame
import math
import time
from robot import Robot
from map import World
from slam import GridBasedSLAM
from a_star import AStar
import cv2
from pyzbar.pyzbar import decode
import tkinter as tk
from tkinter import messagebox
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 750
UI_HEIGHT = 150
MAP_HEIGHT = SCREEN_HEIGHT - UI_HEIGHT

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption('TragerX Simple SLAM Simulator with A* Navigation')

# Function to display intro
def show_intro():
    # Colors for intro
    BLACK = (0, 0, 0)
    GOLD = (255, 215, 0)
    
    # Font for intro
    intro_font = pygame.font.Font(None, 64)
    
    # Text for intro
    text = "Welcome to Chennai International Airport"
    
    # Clock for controlling the frame rate
    clock = pygame.time.Clock()
    
    # Main intro loop
    start_time = time.time()
    intro_running = True
    
    while intro_running and time.time() - start_time < 5:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            
            # Skip intro on key press
            if event.type == pygame.KEYDOWN:
                intro_running = False
        
        # Clear the screen
        screen.fill(BLACK)
        
        # Calculate alpha for fade-in and fade-out
        elapsed_time = time.time() - start_time
        if elapsed_time < 1:
            alpha = int(255 * elapsed_time)
        elif elapsed_time > 4:
            alpha = int(255 * (5 - elapsed_time))
        else:
            alpha = 255
        
        # Calculate pulsating effect
        pulse = math.sin(elapsed_time * 5) * 0.1 + 0.9
        
        # Render text with shadow
        shadow_surf = intro_font.render(text, True, BLACK)
        shadow_surf.set_alpha(alpha)
        text_surf = intro_font.render(text, True, GOLD)
        text_surf.set_alpha(alpha)
        
        # Get text position
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        shadow_rect = text_rect.move(4, 4)
        
        # Apply pulsating effect
        scaled_text = pygame.transform.scale(text_surf, 
                                            (int(text_rect.width * pulse), 
                                            int(text_rect.height * pulse)))
        scaled_shadow = pygame.transform.scale(shadow_surf, 
                                            (int(shadow_rect.width * pulse), 
                                            int(shadow_rect.height * pulse)))
        
        # Update text position after scaling
        text_rect = scaled_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        shadow_rect = scaled_shadow.get_rect(center=(SCREEN_WIDTH/2 + 4, SCREEN_HEIGHT/2 + 4))
        
        # Draw text
        screen.blit(scaled_shadow, shadow_rect)
        screen.blit(scaled_text, text_rect)
        
        # Update the display
        pygame.display.flip()
        
        # Control the frame rate
        clock.tick(60)
    
    return True

# Show intro before starting the main application
continue_app = show_intro()
if not continue_app:
    exit()

# Font for telemetry data and other texts
font = pygame.font.SysFont("Arial", 24)
small_red_font = pygame.font.SysFont("Arial", 18)

# Create world object
world = World()
slam = GridBasedSLAM(80, 60)  # Start with 80x60 grid for the map

# Define counter positions
counter_positions = {
    "source": [SCREEN_WIDTH // 2, UI_HEIGHT + MAP_HEIGHT // 2],  # Center of the map
    "customer": [SCREEN_WIDTH // 2 + 200, UI_HEIGHT + MAP_HEIGHT // 2 + 200],
    "counter1-A": [SCREEN_WIDTH // 2 - 300, UI_HEIGHT + MAP_HEIGHT // 2 - 100],
    "counter1-B": [SCREEN_WIDTH // 2 - 300, UI_HEIGHT + MAP_HEIGHT // 2 + 100],
    "counter2-A": [SCREEN_WIDTH // 2, UI_HEIGHT + MAP_HEIGHT // 2 - 300],
    "counter2-B": [SCREEN_WIDTH // 2, UI_HEIGHT + MAP_HEIGHT // 2 + 300],
    "counter3-A": [SCREEN_WIDTH // 2 + 300, UI_HEIGHT + MAP_HEIGHT // 2 - 100],
    "counter3-B": [SCREEN_WIDTH // 2 + 300, UI_HEIGHT + MAP_HEIGHT // 2 + 100],
}

# Create the robots
robots = []

# Create stationary robots at source (2)
for i in range(2):
    robot = Robot(counter_positions["source"].copy(), 0, id=i, stationary=True, location="source")
    robots.append(robot)

# Create robots at counter positions
locations = [
    "counter1-A", "counter1-A",  # 2 at 1-A
    "counter1-B",  # 1 at 1-B
    "counter3-A",  # 1 at 3-A
    "counter3-B"   # 1 at 3-B
]

for i, location in enumerate(locations, start=2):
    robot = Robot(counter_positions[location].copy(), 0, id=i, stationary=True, location=location)
    robots.append(robot)

# Create mobile robot (the one that will navigate from source to counters)
active_robot = Robot(counter_positions["source"].copy(), 0, id=len(robots), location="source")
active_robot.workflow_state = "idle"  # New state for workflow tracking
robots.append(active_robot)

# Add two more robots to reach 10 total
for i in range(len(robots), 10):
    robot = Robot(counter_positions["source"].copy(), 0, id=i, stationary=True, location="source")
    robots.append(robot)

# Initialize pathfinder
pathfinder = None  # We'll initialize this after the first SLAM update

# Timer for path recalculation
path_recalc_timer = 0
PATH_RECALC_INTERVAL = 30  # Recalculate path every 30 frames (about 1 second)

# Rest of your code continues...

# Function to find counter with fewest robots
def find_counter_with_fewest_robots(counter_num):
    counter_A = f"counter{counter_num}-A"
    counter_B = f"counter{counter_num}-B"
    
    count_A = sum(1 for robot in robots if robot.location == counter_A)
    count_B = sum(1 for robot in robots if robot.location == counter_B)
    
    if count_A <= count_B:
        return counter_A
    else:
        return counter_B

# Colors
BACKGROUND_COLOR = (0, 0, 0)  # Black for map background
UI_BACKGROUND_COLOR = (50, 50, 50)  # Darker grey for UI section
TEXT_COLOR = (255, 255, 255)  # White text for telemetry
CLEAR_SPACE_COLOR = (128, 128, 128)  # Grey for clear space
OBSTACLE_FIRST_DETECTED_COLOR = (255, 255, 0)  # Yellow for first detection of obstacle
OBSTACLE_CONFIRMED_COLOR = (0, 255, 0)  # Green for confirmed obstacles
FRONTIER_COLOR = (64, 64, 64)  # Dark grey for frontier
ROBOT_COLOR = (0, 0, 255)  # Blue for robot
ACTIVE_ROBOT_COLOR = (255, 0, 0)  # Red for active robot
PATH_COLOR = (255, 255, 255)  # White for path
PLANNED_PATH_COLOR = (255, 0, 255)  # Magenta for planned path
CURRENT_TARGET_COLOR = (255, 0, 0)  # Red for current target
DESTINATION_COLOR = (0, 255, 255)  # Cyan for destination point
RED_TEXT_COLOR = (255, 0, 0)  # Red for the custom simulator text

# Track robot path (real-world coordinates)
path_points = []

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
        tk.Label(self.canvas, text="Enter PNR:", font=("Arial", 12), bg="#ffffff").place(x=80, y=100)
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
        """Generate a 4-digit OTP"""
        return str(random.randint(1000, 9999))
    
    def send_otp(self):
        email = self.email_var.get()
        if not email:
            messagebox.showerror("Error", "Please enter a PNR")
            return
        
        self.generated_otp = self.generate_otp()
        

        messagebox.showinfo("OTP Generated", f"Your OTP is: {self.generated_otp}\n\n This would be sent to your Email.")
        
        #self.send_email_otp(email, self.generated_otp)
    
    def send_email_otp(self, email, otp):
        """Send OTP via email"""
        try:
            # Configure your email settings here
            sender_email = "abc@gmail.com"
            sender_password = "urpass"  
            
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
            root.destroy()
             
        else:
            messagebox.showerror("Error", "Invalid OTP. Please try again.")

qr_scan_result = None
k = 0


# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Exit on pressing the Escape key or 'Q'
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                running = False
            # Start the workflow cycle when at source and in idle state
            if event.key == pygame.K_SPACE and active_robot.workflow_state == "idle" and active_robot.location == "source":
                active_robot.workflow_state = "to_customer"
                active_robot.set_destination(counter_positions["customer"][0], counter_positions["customer"][1])
                print("Robot starting journey to customer")
            
            # Scan QR code when at customer
            if event.key == pygame.K_SPACE and active_robot.workflow_state == "at_customer":
                if k == 0:
                    root = tk.Tk()
                    app = OTPVerificationApp(root)
                    root.mainloop()
                    cap = cv2.VideoCapture(0)
                    qr_scan_result = None

                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            continue

                        qr_codes = decode(frame)
                        for qr in qr_codes:
                            qr_scan_result = qr.data.decode('utf-8')
                            cap.release()

                        cv2.imshow("QR Code Scanner", frame)

                        if cv2.waitKey(1) & 0xFF == ord('q') or qr_scan_result:
                            k = 1
                            break
                            
                    cap.release()
                    cv2.destroyAllWindows()

                if not qr_scan_result:
                    qr_scan_result = "1"  # Default to counter1

                counter = find_counter_with_fewest_robots(qr_scan_result)
                print(f"QR Scan Result: {qr_scan_result}, Selected Counter: {counter}")
                active_robot.set_destination(counter_positions[counter][0], counter_positions[counter][1])
                active_robot.location = counter
                active_robot.workflow_state = "to_counter"

    # Get sensor data for the active robot (now scanning in multiple directions)
    sensor_data = active_robot.simulate_ultrasonic(world.obstacles)

    # Update SLAM for each sensor angle from active robot
    for sensor_angle, distance in sensor_data.items():
        slam.sensor_update(active_robot.position, sensor_angle, distance)

    # Initialize or update pathfinder with current map
    if pathfinder is None:
        pathfinder = AStar(slam.occupancy_grid)
    else:
        pathfinder.grid = slam.occupancy_grid

    # Path planning for active robot
    path_recalc_timer += 1
    


    # Check if active robot needs to calculate a new path
    if active_robot.destination and (active_robot.current_path is None or path_recalc_timer >= PATH_RECALC_INTERVAL) and not active_robot.has_reached_destination:
        path_recalc_timer = 0
        
        # Convert robot position to grid coordinates
        robot_grid_x, robot_grid_y = slam.world_to_grid(active_robot.position)
        
        # Convert destination to grid coordinates
        dest_grid_x, dest_grid_y = slam.world_to_grid(active_robot.destination)
            
        # Make sure the destination coordinates are within grid bounds
        dest_grid_x = min(dest_grid_x, slam.occupancy_grid.shape[0] - 1)
        dest_grid_y = min(dest_grid_y, slam.occupancy_grid.shape[1] - 1)
        
        # Plan path to destination
        new_path = pathfinder.find_path((robot_grid_x, robot_grid_y), (dest_grid_x, dest_grid_y))
        
        if new_path:
            active_robot.current_path = new_path
            active_robot.path_index = 0
            print(f"New path planned for Robot {active_robot.id} with {len(new_path)} points")
        else:
            print(f"No path found for Robot {active_robot.id}, will try again later")
    
    # State machine for the workflow
    if active_robot.has_reached_destination:
        # Robot has reached the customer
        if active_robot.workflow_state == "to_customer":
            active_robot.workflow_state = "at_customer"
            print("Robot has reached customer. Ready for QR scan.")
        
        # Robot has reached the counter
        elif active_robot.workflow_state == "to_counter":
            active_robot.workflow_state = "at_counter"
            active_robot.is_waiting = True
            active_robot.wait_timer = 0
            print(f"Robot at counter {active_robot.location}. Waiting for service.")
        
        # Robot has reached the charging station after counter
        elif active_robot.workflow_state == "to_source":
            active_robot.workflow_state = "idle"
            active_robot.location = "source"
            print("Robot has returned to charging station. Ready for next customer.")
    
    # Check if robot has finished waiting at counter
    if active_robot.workflow_state == "at_counter" and active_robot.is_waiting:
        active_robot.wait_timer += 1
        if active_robot.wait_timer >= active_robot.wait_duration:
            active_robot.is_waiting = False
            active_robot.wait_timer = 0
            active_robot.workflow_state = "to_source"
            active_robot.set_destination(counter_positions["source"][0], counter_positions["source"][1])
            print("Finished at counter, returning to charging station.")

    # Update all robots' movements
    for robot in robots:
        robot.update_navigation(slam.occupancy_grid)

    # Clear the screen with background color
    screen.fill(BACKGROUND_COLOR)

    # Draw the UI section at the top
    pygame.draw.rect(screen, UI_BACKGROUND_COLOR, pygame.Rect(0, 0, SCREEN_WIDTH, UI_HEIGHT))

    # Text for Telemetry display and top UI
    title_text = small_red_font.render("TragerX SLAM simulation", True, RED_TEXT_COLOR)
    robot_text = font.render("Robot sensor: HC-SR04", True, TEXT_COLOR)
   
    # Show navigation status of active robot
    if active_robot.workflow_state == "idle":
        if active_robot.location == "source":
            status = "Ready at Charging Station (Press SPACE to start)"
        else:
            status = "Idle"
    elif active_robot.workflow_state == "to_customer":
        status = "Navigating to Customer"
    elif active_robot.workflow_state == "at_customer":
        status = "At Customer - Ready for QR Scan (Press SPACE)"
    elif active_robot.workflow_state == "to_counter":
        status = f"Navigating to {active_robot.location}"
    elif active_robot.workflow_state == "at_counter":
        status = f"At {active_robot.location} - Waiting {active_robot.wait_timer/30:.1f}s"
    elif active_robot.workflow_state == "to_source":
        status = "Returning to Charging Station"
   
    telemetry_text = font.render(f"Robot {active_robot.id} | Angle: {active_robot.angle:.2f}° | Position: ({int(active_robot.position[0])}, {int(active_robot.position[1])})", True, TEXT_COLOR)
    status_text = font.render(f"Status: {status}", True, TEXT_COLOR)
    
    screen.blit(title_text, (10, 10))
    screen.blit(robot_text, (10, 40))
    screen.blit(telemetry_text, (10, 70))
    screen.blit(status_text, (10, 100))

    # Track active robot's path
    path_points.append((active_robot.position[0], active_robot.position[1]))

    # Centering: Keep the active robot centered in the map area
    robot_screen_x = SCREEN_WIDTH // 2
    robot_screen_y = UI_HEIGHT + MAP_HEIGHT // 2

    # Calculate offset based on active robot's position relative to the grid
    offset_x = SCREEN_WIDTH // 2 - active_robot.position[0]
    offset_y = UI_HEIGHT + MAP_HEIGHT // 2 - active_robot.position[1]

    # Draw the SLAM map (only what the robot has detected)
    slam_map = slam.get_map()
    for x in range(slam_map.shape[0]):
        for y in range(slam_map.shape[1]):
            rect_x = x * 10 + offset_x
            rect_y = y * 10 + offset_y

            if rect_y > UI_HEIGHT:  # Ensure map is drawn below the UI section
                if slam_map[x, y] == 1:  # Clear space (grey)
                    pygame.draw.rect(screen, CLEAR_SPACE_COLOR, pygame.Rect(rect_x, rect_y, 10, 10), 1)
                elif slam_map[x, y] == 2:  # First detected obstacle (yellow)
                    pygame.draw.rect(screen, OBSTACLE_FIRST_DETECTED_COLOR, pygame.Rect(rect_x, rect_y, 10, 10))
                elif slam_map[x, y] == 3:  # Confirmed obstacle (green)
                    pygame.draw.rect(screen, OBSTACLE_CONFIRMED_COLOR, pygame.Rect(rect_x, rect_y, 10, 10))

    # Draw robot's path using the real-world positions
    if len(path_points) > 1:
        # Keep path static relative to the world, rather than shifting with the robot
        transformed_path = [(x - active_robot.position[0] + robot_screen_x, y - active_robot.position[1] + robot_screen_y) for (x, y) in path_points]
        # Ensure the path does not draw in the telemetry area
        transformed_path = [(x, y) for (x, y) in transformed_path if y > UI_HEIGHT]
        pygame.draw.lines(screen, PATH_COLOR, False, transformed_path, 2)
    
    # Draw all counter positions
    for name, pos in counter_positions.items():
        # Skip the source position as it might clutter the view
        if name == "source":
            # Draw charging station marker
            source_screen_x = pos[0] - active_robot.position[0] + robot_screen_x
            source_screen_y = pos[1] - active_robot.position[1] + robot_screen_y
            if source_screen_y > UI_HEIGHT:
                pygame.draw.circle(screen, (0, 255, 0), (source_screen_x, source_screen_y), 15)
                label = small_red_font.render("Charging Station", True, (0, 255, 255))
                screen.blit(label, (source_screen_x + 15, source_screen_y - 10))
            continue
        
        # Calculate screen coordinates for counter/customer
        pos_screen_x = pos[0] - active_robot.position[0] + robot_screen_x
        pos_screen_y = pos[1] - active_robot.position[1] + robot_screen_y
        
        if pos_screen_y > UI_HEIGHT:  # Don't draw in UI area
            if name == "customer":
                # Draw customer marker
                pygame.draw.circle(screen, (255, 165, 0), (pos_screen_x, pos_screen_y), 12)  # Orange for customer
                label = small_red_font.render("Customer", True, (255, 165, 0))
            else:
                # Draw counter marker
                pygame.draw.circle(screen, DESTINATION_COLOR, (pos_screen_x, pos_screen_y), 12)
                label = small_red_font.render(name, True, DESTINATION_COLOR)
            
            screen.blit(label, (pos_screen_x + 10, pos_screen_y - 10))
    
    # Draw the planned path
    if active_robot.current_path:
        # Draw all points in the planned path
        for i, (grid_x, grid_y) in enumerate(active_robot.current_path):
            # Convert grid coordinates to screen coordinates
            screen_x = grid_x * 10 + 5 + offset_x  # Center of the grid cell
            screen_y = grid_y * 10 + 5 + offset_y  # Center of the grid cell
            
            if screen_y > UI_HEIGHT:  # Don't draw in UI area
                # Highlight the current target
                if i == active_robot.path_index:
                    pygame.draw.circle(screen, CURRENT_TARGET_COLOR, (screen_x, screen_y), 5)
                else:
                    pygame.draw.circle(screen, PLANNED_PATH_COLOR, (screen_x, screen_y), 3)
        
        # Draw lines connecting the path points
        if len(active_robot.current_path) > 1:
            path_lines = [(p[0] * 10 + 5 + offset_x, p[1] * 10 + 5 + offset_y) for p in active_robot.current_path]
            path_lines = [(x, y) for (x, y) in path_lines if y > UI_HEIGHT]  # Filter out UI area
            if path_lines:
                pygame.draw.lines(screen, PLANNED_PATH_COLOR, False, path_lines, 1)

    # Draw all robots
    for robot in robots:
        # Calculate screen position for this robot
        screen_x = robot.position[0] - active_robot.position[0] + robot_screen_x
        screen_y = robot.position[1] - active_robot.position[1] + robot_screen_y
        
        if screen_y > UI_HEIGHT:  # Don't draw in UI area
            # Choose color based on whether it's the active robot
            color = ACTIVE_ROBOT_COLOR if robot is active_robot else ROBOT_COLOR
            
            # Draw the robot
            pygame.draw.circle(screen, color, (screen_x, screen_y), robot.radius)
            
            # Draw direction indicator
            line_length = robot.radius + 10
            direction_x = screen_x + line_length * math.cos(math.radians(robot.angle))
            direction_y = screen_y + line_length * math.sin(math.radians(robot.angle))
            pygame.draw.line(screen, (255, 255, 255), (screen_x, screen_y), (direction_x, direction_y), 2)
            
            # Draw robot ID
            id_text = small_red_font.render(str(robot.id), True, (255, 255, 255))
            screen.blit(id_text, (screen_x - 5, screen_y - 10))

    # Update the display
    pygame.display.flip()

    # Small delay to control the frame rate
    pygame.time.delay(30)

pygame.quit()