import math


class Robot:
    def __init__(self, position, angle, id=0, stationary=False, location=None):
        self.position = position
        self.angle = angle
        self.sensor_angle = 0  # New: Sensor starts at 0°
        self.sensor_rotation_speed = 1  # New: Degrees per frame (adjust for speed)
        self.speed = 2  
        self.rotation_speed = 2
        self.radius = 20  
        
        self.current_path = None
        self.current_target = None
        self.path_index = 0
        self.target_reached_threshold = 15  
        self.stuck_counter = 0  
        self.stuck_threshold = 20  
        self.last_position = position.copy()  
        
        self.destination = None
        self.has_reached_destination = False

        # properties for multi-robot system
        self.id = id  # Unique identifier for each robot
        self.stationary = stationary  # Whether the robot should stay in place
        self.location = location  # Current location name (e.g., "source", "counter1-A")
        self.wait_timer = 0  # Timer for waiting at counters
        self.wait_duration = 5 * 30  # 5 seconds at 30 frames per second
        self.is_waiting = False
        self.returning_to_source = False
        self.next_destination = None  # Store next destination for multi-point navigation
        
        # New workflow state for the robot
        self.workflow_state = "idle"  # Initial state is idle

    def simulate_ultrasonic(self, obstacles):
        """Simulates an ultrasonic sensor scanning at multiple angles while moving."""
        max_distance = 200  
        step_size = 5  
        
        sensor_readings = {}

        for scan_angle in range(0, 360, 30):  # Scan every 30° (adjust for resolution)
            actual_angle = (self.sensor_angle + scan_angle) % 360  # Relative to robot

            for distance in range(0, max_distance, step_size):
                x = self.position[0] + distance * math.cos(math.radians(actual_angle))
                y = self.position[1] + distance * math.sin(math.radians(actual_angle))

                for obstacle in obstacles:
                    if obstacle.collidepoint(x, y):
                        sensor_readings[actual_angle] = distance  # Store obstacle distance
                        break
                else:
                    sensor_readings[actual_angle] = max_distance  # No obstacle

        # Rotate sensor continuously
        self.sensor_angle = (self.sensor_angle + self.sensor_rotation_speed) % 360

        return sensor_readings  # Return all scanned angles


    def set_destination(self, x, y):
        """Set the destination (Point B) for the robot"""
        self.destination = [x, y]
        self.has_reached_destination = False
        print(f"Robot {self.id}: Destination set to ({x}, {y})")

    def set_next_destination(self, x, y):
        """Set the next destination to go to after reaching current destination"""
        self.next_destination = [x, y]
        print(f"Robot {self.id}: Next destination set to ({x}, {y})")

    def update_navigation(self, slam_map):
        """Update robot movement for A to B navigation"""
        # If robot is stationary, don't move
        if self.stationary:
            return
            
        # If robot is waiting at counter
        if self.is_waiting:
            # We handle the wait timer in main.py now with the workflow state machine
            return
                
        # Check if we're stuck by comparing current position to last position
        position_diff = math.sqrt((self.position[0] - self.last_position[0])**2 + 
                                 (self.position[1] - self.last_position[1])**2)
        if position_diff < 0.5:  # If we've barely moved
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
            
        # Save current position for next comparison
        self.last_position = self.position.copy()
        
        # If we're stuck for too long, request a new path
        if self.stuck_counter > self.stuck_threshold:
            self.current_path = None
            self.stuck_counter = 0
            
        # If we have a current target point from the path
        if self.current_path and self.path_index < len(self.current_path):
            # Convert grid coordinates to world coordinates (center of grid cell)
            target_x = self.current_path[self.path_index][0] * 10 + 5
            target_y = self.current_path[self.path_index][1] * 10 + 5
            
            # Calculate angle to target
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            target_angle = math.degrees(math.atan2(dy, dx)) % 360
            
            # Calculate distance to target
            distance = math.sqrt(dx**2 + dy**2)
            
            # If we've reached the current target, move to the next one
            if distance < self.target_reached_threshold:
                self.path_index += 1
                
                # Check if we've reached the end of the path (destination)
                if self.path_index >= len(self.current_path) and self.destination:
                    # Calculate distance to actual destination (not just the last grid point)
                    dest_distance = math.sqrt((self.destination[0] - self.position[0])**2 + 
                                           (self.destination[1] - self.position[1])**2)
                  
                    self.has_reached_destination = True
                    print(f"Robot {self.id}: Destination reached!")
                return
                
            # Rotate towards the target
            angle_diff = (target_angle - self.angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
                
            # Apply rotation
            if abs(angle_diff) > 5:  # Only rotate if the angle difference is significant
                if angle_diff > 0:
                    self.angle += min(self.rotation_speed, angle_diff)
                else:
                    self.angle -= min(self.rotation_speed, abs(angle_diff))
                self.angle %= 360
            else:
                # Move forward when pointing in the right direction
                self.position[0] += self.speed * math.cos(math.radians(self.angle))
                self.position[1] += self.speed * math.sin(math.radians(self.angle))