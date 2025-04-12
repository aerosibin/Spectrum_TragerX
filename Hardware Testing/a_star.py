import heapq
import numpy as np

class AStar:
    def __init__(self, grid):
        self.grid = grid
        self.directions = [
            (0, 1),   # right
            (1, 0),   # down
            (0, -1),  # left
            (-1, 0),  # up
            (1, 1),   # down-right
            (1, -1),  # down-left
            (-1, 1),  # up-right
            (-1, -1)  # up-left
        ]

    def heuristic(self, a, b):
        """Octile distance heuristic (better for 8-directional movement)"""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + (1.4 - 1) * min(dx, dy)


    def get_neighbors(self, node, grid):
        """Returns valid neighboring cells"""
        neighbors = []
        for dx, dy in self.directions:
            nx, ny = node[0] + dx, node[1] + dy
            
            # Check if the neighbor is within grid bounds
            if 0 <= nx < grid.shape[0] and 0 <= ny < grid.shape[1]:
                # Check if the neighbor is traversable (not an obstacle)
                # 0 = Unknown, 1 = Free, 2 = Tentative Obstacle, 3 = Confirmed Obstacle
                if grid[nx, ny] != 3:  # Not a confirmed obstacle
                    # Diagonal movement costs more
                    cost = 1.4 if abs(dx) + abs(dy) == 2 else 1
                    
                    # Prefer known free spaces (1) over unknown spaces (0) and tentative obstacles (2)
                    if grid[nx, ny] == 1:
                        cost *= 1  # Normal cost for known free space
                    elif grid[nx, ny] == 0:
                        cost *= 2  # Higher cost for unknown space
                    elif grid[nx, ny] == 2:
                        cost *= 3  # Even higher cost for tentative obstacles
                    
                    neighbors.append((nx, ny, cost))
                    
        return neighbors

    def find_path(self, start, goal):
        """
        Finds a path from start to goal using A* algorithm
        
        Args:
            start: (x, y) tuple for starting position
            goal: (x, y) tuple for goal position
            
        Returns:
            List of (x, y) tuples representing the path
        """
        # Initialize data structures
        open_set = []  # Priority queue
        heapq.heappush(open_set, (0, start))  # (f_score, node)
        
        came_from = {}  # Dictionary to reconstruct the path
        
        g_score = {start: 0}  # Cost from start to node
        f_score = {start: self.heuristic(start, goal)}  # Estimated total cost
        
        open_set_hash = {start}  # Set for faster lookup
        
        # Main loop
        while open_set:
            # Get node with lowest f_score
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)
            
            # Goal reached
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)  # Add start position
                return path[::-1]  # Return reversed path
            
            # Check all neighbors
            for neighbor in self.get_neighbors(current, self.grid):
                next_node = (neighbor[0], neighbor[1])  # Extract (x, y) properly
                cost = neighbor[2]

                # Calculate tentative g_score
                tentative_g_score = g_score.get(current, float('inf')) + cost
                
                # Check if this path is better
                if tentative_g_score < g_score.get(next_node, float('inf')):
                    # Update path and scores
                    came_from[next_node] = current
                    g_score[next_node] = tentative_g_score
                    f_score[next_node] = tentative_g_score + self.heuristic(next_node, goal)
                    
                    # Add to open set if not already there
                    if next_node not in open_set_hash:
                        heapq.heappush(open_set, (f_score[next_node], next_node))
                        open_set_hash.add(next_node)
        
        # No path found
        return None
    
