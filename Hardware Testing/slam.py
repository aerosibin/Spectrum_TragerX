import numpy as np
import math

class GridBasedSLAM:
    def __init__(self, initial_grid_width, initial_grid_height):
        """
        Initialize the SLAM system with an occupancy grid.
        Occupancy Grid:
        - 0 = Unknown
        - 1 = Free
        - 2 = Tentative Obstacle
        - 3 = Confirmed Obstacle
        """
        self.occupancy_grid = np.zeros((initial_grid_width, initial_grid_height), dtype=int)
        self.obstacle_detection_count = np.zeros((initial_grid_width, initial_grid_height), dtype=int)  # Track obstacle detection
        self.grid_width = initial_grid_width
        self.grid_height = initial_grid_height

    def expand_occupancy_grid(self, new_width, new_height):
        """Expands the occupancy grid when the robot explores beyond current bounds."""
        new_occupancy_grid = np.zeros((new_width, new_height), dtype=int)
        new_obstacle_detection_count = np.zeros((new_width, new_height), dtype=int)

        # Copy old grid and detection count data to the new expanded arrays
        new_occupancy_grid[:self.occupancy_grid.shape[0], :self.occupancy_grid.shape[1]] = self.occupancy_grid
        new_obstacle_detection_count[:self.obstacle_detection_count.shape[0], :self.obstacle_detection_count.shape[1]] = self.obstacle_detection_count

        # Replace the old grid and detection count arrays with the new ones
        self.occupancy_grid = new_occupancy_grid
        self.obstacle_detection_count = new_obstacle_detection_count
        self.grid_width, self.grid_height = new_width, new_height

    def world_to_grid(self, world_position):
        """Converts world coordinates to grid coordinates."""
        grid_x = int(world_position[0] // 10)
        grid_y = int(world_position[1] // 10)
        return grid_x, grid_y

    def sensor_update(self, robot_pose, sensor_angle, sensor_distance, max_sensor_range=200):
        """
        Updates the occupancy grid based on sensor readings.
        
        Args:
            robot_pose: (x, y) position of the robot in world coordinates.
            sensor_angle: Angle of the sensor relative to the robot's orientation.
            sensor_distance: Distance measured by the sensor.
            max_sensor_range: Maximum range of the sensor (default is 200 cm).
        """
        # Convert robot pose to grid coordinates
        grid_x, grid_y = self.world_to_grid(robot_pose)

        # Expand occupancy grid if necessary
        if grid_x >= self.grid_width or grid_y >= self.grid_height:
            self.expand_occupancy_grid(max(grid_x + 10, self.grid_width), max(grid_y + 10, self.grid_height))

        # Mark robot's current position as explored (1 = clear space)
        self.occupancy_grid[grid_x, grid_y] = 1

        # Ensure sensor_distance is an integer for range()
        sensor_distance = int(sensor_distance)

        # Simulate clear space detection along the full sensor beam
        for ray_distance in range(10, min(sensor_distance, max_sensor_range), 10):  # Limit ray distance to max_sensor_range
            clear_x = grid_x + int(ray_distance * math.cos(math.radians(sensor_angle)) / 10)
            clear_y = grid_y + int(ray_distance * math.sin(math.radians(sensor_angle)) / 10)

            # Expand grid if needed when marking clear space
            if clear_x >= self.grid_width or clear_y >= self.grid_height:
                self.expand_occupancy_grid(max(clear_x + 10, self.grid_width), max(clear_y + 10, self.grid_height))

            # Only mark clear space if it's not already a confirmed obstacle
            if self.occupancy_grid[clear_x, clear_y] != 3:
                self.occupancy_grid[clear_x, clear_y] = 1

        # If an obstacle is detected within range, mark it as tentative or confirmed
        if sensor_distance < max_sensor_range:
            obstacle_x = grid_x + int(sensor_distance * math.cos(math.radians(sensor_angle)) / 10)
            obstacle_y = grid_y + int(sensor_distance * math.sin(math.radians(sensor_angle)) / 10)

            # Expand grid if needed
            if obstacle_x >= self.grid_width or obstacle_y >= self.grid_height:
                self.expand_occupancy_grid(max(obstacle_x + 10, self.grid_width), max(obstacle_y + 10, self.grid_height))

            # Increment detection count for the detected obstacle
            self.obstacle_detection_count[obstacle_x, obstacle_y] += 1

            # Mark obstacles based on detection count
            if self.obstacle_detection_count[obstacle_x, obstacle_y] == 1:
                self.occupancy_grid[obstacle_x, obstacle_y] = 2  # First detection (tentative)
            elif self.obstacle_detection_count[obstacle_x, obstacle_y] >= 3:
                self.occupancy_grid[obstacle_x, obstacle_y] = 3  # Confirmed obstacle

    def get_map(self):
        """Returns the current occupancy grid."""
        return self.occupancy_grid

