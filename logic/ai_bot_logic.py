import numpy as np
import random
import os
import heapq
import math
import time
from logic.adaptive_logic import AdaptiveMazeGame

# Constants
TILE_SIZE = 40
WHITE, BLACK, GREEN, RED, BLUE = (255,)*3, (0,)*3, (0,255,0), (255,0,0), (0,0,255)
ACTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
ALPHA = 0.1  # Learning rate
GAMMA = 0.9  # Discount factor
EPSILON = 0.2  # Exploration rate
SAVE_FOLDER = os.path.join("assets", "Bots")
MAX_BACKTRACKS = 5000  # Max backtracks before regenerating level
MAX_STEPS = 20000  # Max steps before regenerating level

# Ensure bots folder exists
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

class QLearningAgent:
    """AI decision-making agent that learns optimal paths through Q-learning."""
    
    def __init__(self, maze_shape, level):
        self.q_table = np.zeros((*maze_shape, len(ACTIONS)))
        self.visit_counts = {}  # Track state visits
        self.level = level
        self.maze_shape = maze_shape
        self.load_q_table(level, maze_shape)

    def choose_action(self, state, total_steps):
        """Select next action based on current state using epsilon-greedy strategy."""
        # Update visit count for current state
        self.visit_counts[state] = self.visit_counts.get(state, 0) + 1

        # Dynamically adjust exploration rate based on experience
        epsilon = max(0.05, 0.3 - (total_steps / 10000) - (self.level * 0.02))

        if random.uniform(0, 1) < epsilon:
            return self.explore_action(state)
        else:
            return np.argmax(self.q_table[state[0], state[1]])

    def explore_action(self, state):
        """Smart exploration prioritizing less-visited paths."""
        valid_actions = []
        for idx, (dx, dy) in enumerate(ACTIONS):
            new_state = (state[0] + dx, state[1] + dy)
            # Check if within maze bounds
            if 0 <= new_state[0] < self.q_table.shape[0] and 0 <= new_state[1] < self.q_table.shape[1]:
                valid_actions.append((idx, self.visit_counts.get(new_state, 0)))
        
        if valid_actions:
            # Choose least-visited state
            return min(valid_actions, key=lambda x: x[1])[0]
        return random.choice(range(len(ACTIONS)))

    def update_q_table(self, state, action, reward, next_state):
        """Update Q-values using the Q-learning formula."""
        best_next_action = np.max(self.q_table[next_state[0], next_state[1]])
        self.q_table[state[0], state[1], action] += ALPHA * (
            reward + GAMMA * best_next_action - self.q_table[state[0], state[1], action]
        )
    
    def save_q_table(self, level):
        """Save Q-table to disk."""
        filename = os.path.join(SAVE_FOLDER, f"bot_{self.maze_shape[0]}x{self.maze_shape[1]}_lvl_{level}.npy")
        np.save(filename, self.q_table)

    def load_q_table(self, current_level, maze_shape):
        """Load Q-table from disk or create a new one if not found."""
        try:
            # Look for Q-tables with the exact grid size
            pattern = f"bot_{maze_shape[0]}x{maze_shape[1]}_lvl_"
            available_models = []
            
            if os.path.exists(SAVE_FOLDER):
                for f in os.listdir(SAVE_FOLDER):
                    if f.startswith(pattern) and f.endswith(".npy"):
                        try:
                            level = int(f.split("_lvl_")[1].split(".")[0])
                            available_models.append(level)
                        except:
                            continue
            
            available_models.sort(reverse=True)
            
            if available_models:
                best_level = available_models[0]
                filename = os.path.join(SAVE_FOLDER, f"bot_{maze_shape[0]}x{maze_shape[1]}_lvl_{best_level}.npy")
                self.q_table = np.load(filename)
                return
        
        except Exception as e:
            pass
            
        # If we got here, either no model was found or there was an error
        self.q_table = np.zeros((*maze_shape, len(ACTIONS)))

class AStarMazeSolver:
    """Maze solver using A* pathfinding algorithm."""
    
    def __init__(self, game):
        self.game = game
        self.maze = game.maze
        self._validate_start_goal_positions()
        self.reset_stats()
    
    def _validate_start_goal_positions(self):
        """Ensure start/goal positions are within maze bounds."""
        self.start = tuple(np.argwhere(self.game.maze == 2)[0])
        self.goal = tuple(np.argwhere(self.game.maze == 3)[0])
        
        # Clip positions to maze dimensions
        max_y, max_x = self.game.maze.shape
        self.start = (np.clip(self.start[0], 0, max_y-1), np.clip(self.start[1], 0, max_x-1))
        self.goal = (np.clip(self.goal[0], 0, max_y-1), np.clip(self.goal[1], 0, max_x-1))
        self.state = self.start
    
    def reset_stats(self):
        """Reset solver statistics."""
        self.path = []
        self.step_count = 0
        self.visited_states = set()
        self.backtrack_count = 0
        self.start_time = time.time()
        self.path_index = 0
    
    def heuristic(self, a, b):
        """Manhattan distance heuristic."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def solve(self):
        """Find shortest path using A* algorithm."""
        # Priority queue: (f_score, count, position)
        open_set = [(0, 0, self.start)]
        heapq.heapify(open_set)
        
        counter = 0  # For tie-breaking
        came_from = {}  # Path tracking
        g_score = {self.start: 0}  # Cost from start to current
        f_score = {self.start: self.heuristic(self.start, self.goal)}  # Estimated total cost
        closed_set = set()  # Visited nodes
        
        while open_set:
            _, _, current = heapq.heappop(open_set)
            
            # Goal reached
            if current == self.goal:
                self.path = self._reconstruct_path(came_from, current)
                self.step_count = len(self.path)
                return self.path
            
            # Mark as visited
            closed_set.add(current)
            self.visited_states.add(current)
            
            # Check neighbors
            for dx, dy in ACTIONS:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Skip if invalid or already visited
                if (not (0 <= neighbor[0] < self.maze.shape[0] and 
                       0 <= neighbor[1] < self.maze.shape[1]) or
                    self.maze[neighbor[0], neighbor[1]] == 1 or
                    neighbor in closed_set):
                    continue
                
                # Calculate scores
                tentative_g = g_score.get(current, float('inf')) + 1
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    # This path is better, record it
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, self.goal)
                    
                    # Add to open set if not already there
                    if neighbor not in [item[2] for item in open_set]:
                        counter += 1
                        heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
        
        # No path found
        return []
    
    def _reconstruct_path(self, came_from, current):
        """Rebuild path from goal to start."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path))
    
    def get_action_sequence(self):
        """Convert path to sequence of action indices."""
        if not self.path:
            self.solve()
            
        if not self.path:
            return []
            
        actions = []
        for i in range(len(self.path) - 1):
            curr, next_pos = self.path[i], self.path[i+1]
            
            # Calculate direction
            dy = next_pos[0] - curr[0]
            dx = next_pos[1] - curr[1]
            
            # Find matching action
            for idx, (action_dy, action_dx) in enumerate(ACTIONS):
                if action_dy == dy and action_dx == dx:
                    actions.append(idx)
                    break
        
        return actions

class MazeBot:
    """Base maze-solving bot using Q-learning and simple heuristics."""
    
    def __init__(self, game, level):
        self.agent = QLearningAgent(game.maze.shape, level)
        self.game = game
        self._validate_start_goal_positions()
        self.visited_states = set()
        self.backtrack_count = 0
        self.step_count = 0
        self.start_time = time.time()
        self.visited_counts = {}
        self.last_state = None
    
    def step(self):
        """Take one step in the maze using Q-learning strategy."""
        # Check if we're stuck or taking too many steps
        if self.backtrack_count >= MAX_BACKTRACKS or self.step_count >= MAX_STEPS:
            solver = AStarMazeSolver(self.game)
            path = solver.solve()
            if not path:
                # Maze is unsolvable
                return "regenerate"
            else:
                # We're just stuck, adjust Q-values and continue
                self.agent.q_table *= 0.9  # Reduce overconfidence
                self.backtrack_count = 0
                self.step_count = 0
                return self.state

        # Choose and take action
        action_idx = self.agent.choose_action(self.state, self.step_count)
        action = ACTIONS[action_idx]
        next_state = (self.state[0] + action[0], self.state[1] + action[1])
        
        # Calculate rewards based on progress
        current_dist = self.heuristic(self.state, self.goal)
        new_dist = self.heuristic(next_state, self.goal) if self.is_valid(next_state) else current_dist
        progress_reward = (current_dist - new_dist) * 2  # Reward for moving closer to goal
        
        if self.is_valid(next_state):
            # Calculate reward based on situation
            if next_state == self.goal:
                reward = 100  # Big reward for reaching goal
            else:
                reward = progress_reward
                
                # Penalties for revisiting and backtracking
                visit_count = self.visited_counts.get(next_state, 0)
                reward -= 10 * (visit_count + 1)  # Increasing penalty for revisits
                
                if next_state == self.last_state:
                    reward -= 15  # Penalty for immediate backtrack

            # Update state and tracking variables
            self.visited_counts[next_state] = self.visited_counts.get(next_state, 0) + 1
            self.last_state = self.state
            self.state = next_state
            self.step_count += 1
        else:
            reward = -20  # Penalty for invalid move
        
        # Update Q-values
        self.agent.update_q_table(self.state, action_idx, reward, next_state)
        return self.state
    
    def heuristic(self, a, b):
        """Manhattan distance between two points."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def is_valid(self, state):
        """Check if a state is valid (within bounds and not a wall)."""
        return (0 <= state[0] < self.game.maze.shape[0] and 
                0 <= state[1] < self.game.maze.shape[1] and 
                self.game.maze[state[0], state[1]] != 1)
        
    def get_performance_data(self):
        """Return performance metrics for difficulty adjustment."""
        return {
            "completion_time": time.time() - self.start_time,
            "total_moves": self.step_count,
            "backtracks": self.backtrack_count,
            "revisits": len(self.visited_counts)
        }
    
    def _validate_start_goal_positions(self):
        """Set start and goal positions based on maze data."""
        self.start = tuple(np.argwhere(self.game.maze == 2)[0])
        self.goal = tuple(np.argwhere(self.game.maze == 3)[0])
        
        # Make sure positions are within valid range
        max_y, max_x = self.game.maze.shape
        self.start = (np.clip(self.start[0], 0, max_y-1), np.clip(self.start[1], 0, max_x-1))
        self.goal = (np.clip(self.goal[0], 0, max_y-1), np.clip(self.goal[1], 0, max_x-1))
        self.state = self.start

class EnhancedMazeBot(MazeBot):
    """Advanced maze-solving bot with A* pathfinding assistance."""
    
    def __init__(self, game, level, use_astar_hints=True):
        super().__init__(game, level)
        self.use_astar_hints = use_astar_hints
        self.astar_solver = AStarMazeSolver(game)
        self.optimal_path = []
        self.follow_optimal = False
        self.optimal_index = 0
        self.a_star_cache = {}
        self.dead_ends = set()
        self.current_direction = None
    
    def get_optimal_path(self, current_pos):
        """Get optimal path from current position using A*."""
        # Check cache first
        cache_key = (current_pos, self.goal)
        if cache_key in self.a_star_cache:
            return self.a_star_cache[cache_key]
            
        # Update A* solver with current position and solve
        self.astar_solver.start = current_pos
        self.astar_solver.state = current_pos
        self.astar_solver.reset_stats()
        
        path = self.astar_solver.solve()
        actions = self.astar_solver.get_action_sequence()
        
        # Cache and return result
        self.a_star_cache[cache_key] = actions
        return actions

    def step(self):
        """Take one step with enhanced A*-assisted strategy."""
        # Calculate backtrack limit based on maze size
        grid_size = self.game.maze.shape[0] * self.game.maze.shape[1]
        max_allowed_backtracks = 5 * math.sqrt(grid_size)
        
        # Check if we're stuck or taking too many steps
        if self.backtrack_count > max_allowed_backtracks or self.step_count >= MAX_STEPS:
            self.astar_solver.start = self.start
            self.astar_solver.goal = self.goal
            path = self.astar_solver.solve()
            
            if not path:
                return "regenerate"
            else:
                # Reset Q-values and continue
                self.agent.q_table *= 0.9
                self.backtrack_count = 0
                self.step_count = 0
                return self.state
        
        # Get optimal path from A*
        optimal_actions = self.get_optimal_path(self.state)
        
        # Decide whether to follow A* or explore based on how stuck we are
        stuck_factor = self.backtrack_count / max(1, self.step_count)
        follow_astar_prob = min(0.95, 0.7 + stuck_factor * 0.25)
        
        # Try following A* path first
        if optimal_actions and random.random() < follow_astar_prob:
            for i in range(min(3, len(optimal_actions))):  # Look ahead up to 3 steps
                action_idx = optimal_actions[i]
                next_state = (self.state[0] + ACTIONS[action_idx][0],
                              self.state[1] + ACTIONS[action_idx][1])
                
                # Skip known dead ends
                if next_state in self.dead_ends:
                    continue
                    
                if self.is_valid(next_state):
                    # Calculate momentum bonus for continuing in same direction
                    if self.current_direction is not None:
                        current_dir = ACTIONS[action_idx]
                        direction_change = current_dir != self.current_direction
                        momentum_factor = 0.8 if not direction_change else 0.5
                    else:
                        momentum_factor = 0.7
                    
                    # Update state
                    reward = 50 * momentum_factor
                    self.agent.update_q_table(self.state, action_idx, reward, next_state)
                    self.last_state = self.state
                    self.current_direction = ACTIONS[action_idx]
                    self.state = next_state
                    self.visited_states.add(self.state)
                    self.step_count += 1
                    
                    # Check if this is a dead end
                    valid_moves = self._count_valid_moves(self.state)
                    if valid_moves == 1 and self.state != self.goal:
                        self.dead_ends.add(self.state)
                    
                    return self.state
        
        # Fall back to smart exploration if A* path not followed
        valid_actions = []
        for idx, (dy, dx) in enumerate(ACTIONS):
            new_state = (self.state[0] + dy, self.state[1] + dx)
            
            if self.is_valid(new_state) and new_state not in self.dead_ends:
                # Calculate multiple factors for scoring moves
                is_visited = new_state in self.visited_states
                distance_to_goal = self.heuristic(new_state, self.goal)
                direction_change = (dy, dx) != self.current_direction if self.current_direction else True
                
                # Lower score is better
                score = distance_to_goal * 0.5  # Prefer closer to goal
                score += 50 if is_visited else 0  # Penalize revisits
                score += 20 if direction_change else 0  # Prefer same direction
                
                valid_actions.append((idx, new_state, score))
        
        if valid_actions:
            # Choose best action
            sorted_actions = sorted(valid_actions, key=lambda x: x[2])
            best_action = sorted_actions[0]
            action_idx, next_state = best_action[0], best_action[1]
            
            # Calculate reward
            if next_state in self.visited_states:
                reward = -30  # Penalty for revisiting
                if next_state == self.last_state:
                    reward = -60  # Larger penalty for immediate backtrack
                    self.backtrack_count += 1
            else:
                # Reward progress toward goal
                current_dist = self.heuristic(self.state, self.goal)
                new_dist = self.heuristic(next_state, self.goal)
                reward = (current_dist - new_dist) * 15
            
            # Update state
            self.agent.update_q_table(self.state, action_idx, reward, next_state)
            self.visited_states.add(next_state)
            self.last_state = self.state
            self.current_direction = ACTIONS[action_idx]
            self.state = next_state
            self.step_count += 1
            
            # Update dead end tracking
            valid_moves = self._count_valid_moves(self.state)
            if valid_moves == 1 and self.state != self.goal:
                self.dead_ends.add(self.state)
        else:
            # We're at a dead end with no valid moves
            self.dead_ends.add(self.state)
            
            # Try to escape by any valid move
            for idx, (dy, dx) in enumerate(ACTIONS):
                new_state = (self.state[0] + dy, self.state[1] + dx)
                if self.is_valid(new_state):
                    self.state = new_state
                    self.step_count += 1
                    return self.state
        
        return self.state

    def _count_valid_moves(self, state):
        """Count number of valid moves from current state."""
        count = 0
        for dy, dx in ACTIONS:
            new_state = (state[0] + dy, state[1] + dx)
            if self.is_valid(new_state):
                count += 1
        return count