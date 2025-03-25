import pygame
import time
import random
import numpy as np
from adaptivemaze import AdaptiveMazeGame
from ai_bot_trainer_multicore import EnhancedMazeBot
import os

# Constants
TILE_SIZE = 40
MAX_FPS = 120  # Maintain high FPS for smooth animations
STATS_WIDTH = 250
MAX_WINDOW_SIZE = (800, 600)  # Maximum window dimensions
WHITE, BLACK, GREEN, RED, BLUE = (255,)*3, (0,)*3, (0,255,0), (255,0,0), (0,0,255)
AI_UPDATE_EVENT = pygame.USEREVENT + 1
SAVE_INTERVAL = 1
AI_SPEED = 100  # Increased from 100 to slow down the AI (in milliseconds)

class MazeGameUI:
    def __init__(self, player_id="Player1"):
        pygame.init()
        self.game = AdaptiveMazeGame(player_id)
        self.running = True
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.path = []
        self.load_new_level()
        self.ai_mode = False
        self.ai_path = []
        self.ai_bot = None
        self.ai_trail_surface = None
        pygame.time.set_timer(AI_UPDATE_EVENT, AI_SPEED)  # Using the new speed constant

    def toggle_ai(self):
        """Switch between human and AI control"""
        self.ai_mode = not self.ai_mode
        if self.ai_mode:
            self.init_ai_solver()

    def init_ai_solver(self):
        """Load the best trained AI model for the current maze size."""
        current_size = self.game.maze.shape
        bot_filename = f"bot_{current_size[0]}x{current_size[1]}_combined.npy"
        
        # Check both local and Google Drive paths
        possible_paths = [
            os.path.join("Bots", bot_filename),  # Local storage
            os.path.join("/content/drive/MyDrive/MazeBot_Models", bot_filename)  # Google Drive
        ]
        bot_path = next((path for path in possible_paths if os.path.exists(path)), None)
        
        # Initialize EnhancedMazeBot with current maze dimensions
        self.ai_bot = EnhancedMazeBot(self.game, level=0, use_astar_hints=True)
        
        # Initialize Q-table with correct dimensions
        rows, cols = current_size
        actions = 4  # Up, Down, Left, Right
        self.ai_bot.agent.q_table = np.zeros((rows, cols, actions))
        
        if bot_path:
            print(f"✅ Loading AI bot: {bot_path}")
            try:
                loaded_q_table = np.load(bot_path)
                if loaded_q_table.shape[:2] == current_size:
                    self.ai_bot.agent.q_table = loaded_q_table
                    print("✅ Q-table loaded successfully")
                else:
                    print(f"⚠️ Q-table dimensions mismatch. Expected {current_size}, got {loaded_q_table.shape[:2]}")
            except Exception as e:
                print(f"⚠️ Error loading Q-table: {e}")
        else:
            print("⚠️ No combined bot found. Using default Q-table")
        
        # Initialize AI state and goal
        start_pos = np.argwhere(self.maze == 2)[0]
        goal_pos = np.argwhere(self.maze == 3)[0]
        
        self.ai_bot.state = tuple(start_pos)
        self.ai_bot.goal = tuple(goal_pos)
        self.ai_path = [tuple(start_pos)]
        
        # Set maze bounds
        self.ai_bot.maze_bounds = current_size
        print(f"AI initialized at position: {start_pos}, goal at: {goal_pos}")
        print(f"Maze bounds: {current_size}")

    def draw_ai_path(self, cam_x, cam_y):
        """Visualize AI's pathfinding process"""
        if self.ai_mode and len(self.ai_path) > 1:
            # Draw path trail
            for i in range(1, len(self.ai_path)):
                prev = (self.ai_path[i-1][1]*TILE_SIZE - cam_x, self.ai_path[i-1][0]*TILE_SIZE - cam_y)
                curr = (self.ai_path[i][1]*TILE_SIZE - cam_x, self.ai_path[i][0]*TILE_SIZE - cam_y)
                pygame.draw.line(self.window, (255,165,0,100), prev, curr, 3)
                
            # Draw current AI position
            ai_x = self.ai_bot.state[1]*TILE_SIZE - cam_x
            ai_y = self.ai_bot.state[0]*TILE_SIZE - cam_y
            pygame.draw.circle(self.window, (255,215,0), (ai_x+TILE_SIZE//2, ai_y+TILE_SIZE//2), 8)

    def load_new_level(self):
        """Generate new level with dynamic window sizing"""
        self.game.generate_maze()
        
        # Ensure start position has two openings
        maze = self.game.maze
        start_positions = np.argwhere(maze == 2)
        if len(start_positions) > 0:
            start_pos = start_positions[0]
            rows, cols = maze.shape
            neighbors = []
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx = start_pos[0] + dx
                ny = start_pos[1] + dy
                if 0 <= nx < rows and 0 <= ny < cols:
                    neighbors.append((nx, ny))
            
            # Count current open paths
            open_count = 0
            for (nx, ny) in neighbors:
                if maze[nx, ny] != 1:  # Check if path or exit
                    open_count += 1
            
            # Open walls if needed
            if open_count < 2:
                needed = 2 - open_count
                random.shuffle(neighbors)
                for (nx, ny) in neighbors:
                    if maze[nx, ny] == 1 and needed > 0:
                        maze[nx, ny] = 0
                        needed -= 1
                        if needed == 0:
                            break
        
        self.player_tracker = self.game.create_player_tracker()
        self.player_tracker.start_tracking()
        
        self.maze = self.game.maze
        self.height, self.width = self.maze.shape
        
        # Player starts at entry point (where maze value is 2)
        self.player_pos = np.argwhere(self.maze == 2)[0].astype(float)
        
        # Calculate required window size
        maze_pixel_width = self.width * TILE_SIZE
        maze_pixel_height = self.height * TILE_SIZE
        
        # Apply window size constraints
        window_width = min(maze_pixel_width + STATS_WIDTH, MAX_WINDOW_SIZE[0])
        window_height = min(maze_pixel_height, MAX_WINDOW_SIZE[1])
        
        # Set up display
        self.window = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption(f"Adaptive Maze - Level {self.game.current_level}")
        self.start_time = time.time()
        self.path = [tuple(self.player_pos.astype(int))]

    def calculate_camera(self):
        """Dynamic camera system with boundary checks"""
        viewport_width = self.window.get_width() - STATS_WIDTH
        viewport_height = self.window.get_height()
        
        # Use raw coordinates without inversion
        cam_x = self.player_pos[1] * TILE_SIZE - viewport_width // 2  # x position
        cam_y = self.player_pos[0] * TILE_SIZE - viewport_height // 2  # y position
        
        # Clamp to maze boundaries (existing correct code)
        max_cam_x = max(0, self.width * TILE_SIZE - viewport_width)
        max_cam_y = max(0, self.height * TILE_SIZE - viewport_height)
        
        return (
            np.clip(cam_x, 0, max_cam_x),
            np.clip(cam_y, 0, max_cam_y)
        )

    def draw_maze(self):
        """Render maze with textures and smooth camera"""
        cam_x, cam_y = self.calculate_camera()
        viewport_width = self.window.get_width() - STATS_WIDTH
        
        # Background
        bg = pygame.transform.scale(
            pygame.image.load("assets/grass.jpeg"),
            (self.width*TILE_SIZE, self.height*TILE_SIZE)
        )
        self.window.blit(bg, (-cam_x, -cam_y))
        
        # Load assets
        wall = pygame.transform.scale(pygame.image.load("assets/wall.jpeg"), (TILE_SIZE, TILE_SIZE))
        exit_img = pygame.transform.scale(pygame.image.load("assets/finish.png"), (TILE_SIZE, TILE_SIZE))
        player = pygame.transform.scale(pygame.image.load("assets/player.png"), (TILE_SIZE, TILE_SIZE))
        start_img = pygame.transform.scale(pygame.image.load("assets/start.png"), (TILE_SIZE, TILE_SIZE))

        # Draw maze elements
        for row in range(self.height):
            for col in range(self.width):
                x = col*TILE_SIZE - cam_x
                y = row*TILE_SIZE - cam_y
                
                # Culling off-screen tiles
                if not (-TILE_SIZE <= x <= viewport_width + TILE_SIZE and 
                        -TILE_SIZE <= y <= self.window.get_height() + TILE_SIZE):
                    continue
                
                if self.maze[row, col] == 1:
                    self.window.blit(wall, (x, y))
                elif self.maze[row, col] == 3:
                    self.window.blit(exit_img, (x, y))
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    glow.fill((0, 255, 0, 100))
                    self.window.blit(glow, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
                elif self.maze[row, col] == 2:
                    self.window.blit(start_img, (x, y))

        # Draw AI visualization FIRST (so player appears on top)
        if self.ai_mode and hasattr(self, 'ai_bot') and self.ai_bot:
            self.draw_ai_path(cam_x, cam_y)

        # Determine player/AI position
        if self.ai_mode and hasattr(self, 'ai_bot') and self.ai_bot:
            px = self.ai_bot.state[1] * TILE_SIZE - cam_x  # state is (y,x)
            py = self.ai_bot.state[0] * TILE_SIZE - cam_y
        else:
            px = self.player_pos[1] * TILE_SIZE - cam_x
            py = self.player_pos[0] * TILE_SIZE - cam_y

        # Draw player ONCE
        self.window.blit(player, (px, py))

        # Draw stats panel
        panel_x = viewport_width
        pygame.draw.rect(self.window, (30,30,30), (panel_x, 0, STATS_WIDTH, self.window.get_height()))
        pygame.draw.rect(self.window, (200,200,200), (panel_x, 0, STATS_WIDTH, self.window.get_height()), 3)
        
        # Display statistics with backtrack limit for AI mode
        max_backtracks = self.height * self.width * 10 if self.ai_mode else float('inf')
        stats = [
            (f"Level {self.game.current_level}", 50),
            (f"Time: {time.time()-self.start_time:.1f}s", 100),
            (f"Moves: {self.player_tracker.total_moves}", 150),
            (f"Backtracks: {self.player_tracker.backtracks}/{max_backtracks}", 200),
            (f"Difficulty: {self.game.difficulty}", 250),
            (f"AI Mode: {'ON' if self.ai_mode else 'OFF'}", 300)
        ]
        
        for text, ypos in stats:
            color = WHITE
            if "Backtracks" in text and self.ai_mode:
                # Change color to red if approaching limit
                if self.player_tracker.backtracks > max_backtracks * 0.8:
                    color = RED
                elif self.player_tracker.backtracks > max_backtracks * 0.5:
                    color = (255, 165, 0)  # Orange
            self.window.blit(self.font.render(text, True, color), (panel_x+20, ypos))

    def move_player(self, dx, dy):
        """Smooth movement with backtracking detection"""
        new_pos = self.player_pos + [dx, dy]
        new_x, new_y = new_pos.astype(int)

        if (0 <= new_x < self.height and 
            0 <= new_y < self.width and 
            self.maze[new_x, new_y] != 1):
            
            # Backtrack detection
            current = (new_x, new_y)
            if current in self.path[:-1]:
                self.player_tracker.backtracks += 1

            # Smooth animation (more frames)
            prev_pos = self.player_pos.copy()
            for t in np.linspace(0, 1, 5):  # More steps for smooth movement
                self.player_pos = prev_pos + (dx * t, dy * t)
                self.draw_maze()
                pygame.display.flip()
                self.clock.tick(60)  # Increase FPS for smoother animation

            # Finalize position
            self.player_pos = new_pos
            self.path.append(current)
            self.player_tracker.total_moves += 1

            # Check level completion
            if self.maze[new_x, new_y] == 3:
                self.complete_level()

    def complete_level(self):
        """Progress only if trained model exists"""
        if self.ai_mode and not self.can_progress():
            print("Bot needs training for higher levels!")
            self.toggle_ai()
            return

        self.player_tracker.complete_maze()
        self.game.update_difficulty(self.player_tracker.get_performance_data())
        self.load_new_level()
        
        # Reset AI bot to starting position if in AI mode
        if self.ai_mode and self.ai_bot:
            # Find the start position (where maze value is 2)
            start_pos = np.argwhere(self.maze == 2)[0]
            self.ai_bot.state = tuple(start_pos)  # Update AI bot's state
            self.player_pos = start_pos.astype(float)  # Update player position
            self.ai_path = [tuple(start_pos)]  # Reset the AI path
            print(f"AI bot reset to starting position: {start_pos}")

    def handle_events(self):
        """Process keyboard input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:  # Press A to toggle AI
                    self.toggle_ai()
                elif event.key == pygame.K_UP:
                    self.move_player(-1, 0)
                elif event.key == pygame.K_DOWN:
                    self.move_player(1, 0)
                elif event.key == pygame.K_LEFT:
                    self.move_player(0, -1)
                elif event.key == pygame.K_RIGHT:
                    self.move_player(0, 1)
            elif event.type == AI_UPDATE_EVENT and self.ai_mode:
                print("AI Step Triggered")  # Debugging
                self.run_ai_step()  # Directly call without can_progress()
    
    def run_ai_step(self):
        """Execute one step of AI movement with bounds checking"""
        if not self.ai_bot:
            print("AI bot not initialized. Skipping step.")
            return

        # Get current maze dimensions and calculate max backtracks
        maze_height, maze_width = self.maze.shape
        max_allowed_backtracks = maze_height * maze_width * 10

        # Check if backtrack limit exceeded
        if self.player_tracker.backtracks > max_allowed_backtracks:
            print(f"⚠️ AI bot exceeded backtrack limit ({max_allowed_backtracks})! Resetting maze.")
            self._reset_current_maze()
            return

        # Validate current state
        if not (0 <= self.ai_bot.state[0] < maze_height and 0 <= self.ai_bot.state[1] < maze_width):
            print(f"Invalid state detected: {self.ai_bot.state}. Resetting to start.")
            start_pos = np.argwhere(self.maze == 2)[0]
            self.ai_bot.state = tuple(start_pos)
            self.ai_path = [tuple(start_pos)]
            return

        # Let the EnhancedMazeBot decide its next move
        prev_state = self.ai_bot.state
        try:
            new_state = self.ai_bot.step()
        except IndexError as e:
            print(f"Error during AI step: {e}")
            return

        # Validate new state
        if new_state == "regenerate":
            print("Regenerating maze due to unsolvable state.")
            self.load_new_level()
            return

        if not (0 <= new_state[0] < maze_height and 0 <= new_state[1] < maze_width):
            print(f"Invalid move detected: {new_state}. Staying at current position.")
            return

        # Record the new position
        self.player_pos = np.array([new_state[0], new_state[1]])
        if new_state != prev_state:
            self.ai_path.append(new_state)
            self.player_tracker.total_moves += 1
            if tuple(new_state) in [tuple(pos) for pos in self.ai_path[:-1]]:
                self.player_tracker.backtracks += 1
            print(f"Successfully moved to {new_state}")

        # Check if we've reached the goal
        if new_state == self.ai_bot.goal:
            print("Goal reached!")
            self.complete_level()

    def _reset_current_maze(self):
        """Reset the current maze while keeping AI mode on"""
        # Store current maze for reset
        current_maze = self.maze.copy()
        
        # Reset player tracker stats
        self.player_tracker = self.game.create_player_tracker()
        self.player_tracker.start_tracking()
        
        # Reset maze state
        self.maze = current_maze
        start_pos = np.argwhere(self.maze == 2)[0]
        goal_pos = np.argwhere(self.maze == 3)[0]
        
        # Reset AI state
        self.ai_bot.state = tuple(start_pos)
        self.ai_bot.goal = tuple(goal_pos)
        self.player_pos = start_pos.astype(float)
        self.ai_path = [tuple(start_pos)]
        
        # Reset timing
        self.start_time = time.time()
        
        print(f"🔄 Maze reset. Starting fresh attempt from {start_pos}")

    def _try_random_valid_move(self, state):
        """Try to make any valid move from the current position"""
        print("Attempting a random valid move")
        
        # Try all four directions in random order
        action_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        random.shuffle(action_directions)
        
        for dy, dx in action_directions:
            new_pos = (state[0] + dy, state[1] + dx)
            
            # Check if this move is valid
            if (0 <= new_pos[0] < self.maze.shape[0] and 
                0 <= new_pos[1] < self.maze.shape[1] and 
                self.maze[new_pos[0], new_pos[1]] != 1):
                
                print(f"Found valid move to {new_pos}")
                self.ai_bot.state = new_pos
                return new_pos
        
        print("No valid moves available - bot is trapped!")
        return state
    
    def print_maze_debug(self):
        """Print the full maze state for debugging"""
        print("\nFULL MAZE STATE:")
        for i in range(self.maze.shape[0]):
            row = ""
            for j in range(self.maze.shape[1]):
                if (i, j) == self.ai_bot.state:
                    row += "P "  # Player
                elif (i, j) == self.ai_bot.goal:
                    row += "G "  # Goal
                else:
                    row += f"{self.maze[i, j]} "
            print(row)
        print("\n")

    def get_max_trained_level(self):
        """Find the highest trained level for the current maze size."""
        current_shape = self.game.maze.shape
        try:
            models = [
                int(f.split("_lvl_")[1].split(".")[0])
                for f in os.listdir("Bots")
                if f.startswith(f"bot_{current_shape[0]}x{current_shape[1]}_lvl_")
            ]
            return max(models) if models else 0
        except FileNotFoundError:
            return 0

    def can_progress(self):
        current_shape = self.game.maze.shape
        try:
            return any(
                np.load(os.path.join("Bots", f)).shape[:2] == current_shape
                for f in os.listdir("Bots") if f.startswith("bot_")  # Broader search
            )
        except FileNotFoundError:
            return False

    def run(self):
        """Main game loop with FPS control"""
        while self.running:
            self.handle_events()
            self.draw_maze()
            pygame.display.flip()
            self.clock.tick(MAX_FPS)
        pygame.quit()

if __name__ == "__main__":
    game = MazeGameUI()
    game.run()