import pygame
import time
import random
import numpy as np
import os
from adaptivemaze import AdaptiveMazeGame
from ai_bot_trainer_multicore import EnhancedMazeBot

# Constants
TILE_SIZE = 40
MAX_FPS = 120
STATS_WIDTH = 250
MAX_WINDOW_SIZE = (1200, 600)  # Wider to accommodate two mazes
WHITE, BLACK, GREEN, RED, BLUE, ORANGE, PURPLE = (255,255,255), (0,0,0), (0,255,0), (255,0,0), (0,0,255), (255,165,0), (128,0,128)
AI_UPDATE_EVENT = pygame.USEREVENT + 1
AI_SPEED = 1000  # Higher value = slower AI (milliseconds between moves)
MAX_LEVELS = 10  # Maximum number of levels in the game
AI_BACKTRACK_LIMIT = 5  # Maximum number of backtracks before AI resets

class MazeRaceUI:
    def __init__(self, player_id="Player1"):
        pygame.init()
        self.running = True
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 48)
        self.state = "main_menu"  # Game state: "main_menu", "playing", "paused", "game_over"

        # Initialize games for player and AI
        self.player_game = AdaptiveMazeGame(player_id)
        self.ai_game = AdaptiveMazeGame(player_id + "_AI")

        # Initialize variables
        self.player_path = []
        self.ai_path = []
        self.player_wins = 0
        self.ai_wins = 0
        self.races = 0
        self.current_winner = None
        self.game_over = False
        self.player_made_first_move = False
        self.ai_resetting = False

        # Load level and start AI timer
        self.load_new_level()
        pygame.time.set_timer(AI_UPDATE_EVENT, AI_SPEED)

    def init_ai_solver(self):
        """Initialize AI bot for the AI's maze"""
        current_size = self.ai_game.maze.shape
        bot_filename = f"bot_{current_size[0]}x{current_size[1]}_combined.npy"
        
        # Look for the AI model in Bots folder
        bot_dir = "Bots"
        if not os.path.exists(bot_dir):
            os.makedirs(bot_dir)
            
        bot_path = os.path.join(bot_dir, bot_filename)
        
        # Initialize EnhancedMazeBot with current maze dimensions
        self.ai_bot = EnhancedMazeBot(self.ai_game, level=0, use_astar_hints=True)
        
        # Initialize Q-table with correct dimensions
        rows, cols = current_size
        actions = 4  # Up, Down, Left, Right
        self.ai_bot.agent.q_table = np.zeros((rows, cols, actions))
        
        # Try to load the specific size model
        model_loaded = False
        if os.path.exists(bot_path):
            try:
                loaded_q_table = np.load(bot_path)
                if loaded_q_table.shape[:2] == current_size:
                    self.ai_bot.agent.q_table = loaded_q_table
                    model_loaded = True
                else:
                    print(f"Model size mismatch: expected {current_size}, got {loaded_q_table.shape[:2]}")
            except Exception as e:
                print(f"Error loading model: {e}")
        
        # If no exact size match, look for the closest size (quietly)
        if not model_loaded:
            # Skip printing messages to reduce console spam
            closest_model = None
            smallest_diff = float('inf')
            
            # Find models that are close in size
            try:
                for file in os.listdir(bot_dir):
                    if file.startswith("bot_") and file.endswith("_combined.npy"):
                        try:
                            # Parse dimensions from filename
                            parts = file.split("_")[1].split("x")
                            model_rows, model_cols = int(parts[0]), int(parts[1])
                            
                            # Calculate size difference
                            diff = abs(model_rows - rows) + abs(model_cols - cols)
                            
                            if diff < smallest_diff:
                                smallest_diff = diff
                                closest_model = file
                        except:
                            continue
            except Exception:
                closest_model = None
        
            # Load the closest model if found
            if closest_model:
                try:
                    model_path = os.path.join(bot_dir, closest_model)
                    loaded_q_table = np.load(model_path)
                    
                    # Using A* pathfinding as primary navigation method
                    model_loaded = True
                except Exception:
                    pass
        
        # Initialize AI state and goal
        start_pos = np.argwhere(self.ai_maze == 2)[0]
        goal_pos = np.argwhere(self.ai_maze == 3)[0]
        
        self.ai_bot.state = tuple(start_pos)
        self.ai_bot.goal = tuple(goal_pos)
        self.ai_position = np.array([start_pos[0], start_pos[1]], dtype=float)
        self.ai_path = [tuple(start_pos)]
        self.ai_reached_goal = False
        self.ai_backtracks = 0
        self.ai_moves = 0

    def load_new_level(self):
        """Generate new level and initialize both player and AI with identical mazes"""
        # Generate player maze
        self.player_game.generate_maze()
        self.player_tracker = self.player_game.create_player_tracker()
        self.player_tracker.start_tracking()
        
        # Store maze data for player
        self.player_maze = self.player_game.maze.copy()
        self.height, self.width = self.player_maze.shape
        
        # Create identical maze for AI
        self.ai_game.maze = self.player_maze.copy()
        self.ai_maze = self.ai_game.maze
        
        # Player starts at entry point (where maze value is 2)
        self.player_pos = np.argwhere(self.player_maze == 2)[0].astype(float)
        
        # Calculate required window size for two mazes side by side
        maze_pixel_width = self.width * TILE_SIZE
        maze_pixel_height = self.height * TILE_SIZE
        
        # Apply window size constraints - wider to accommodate two mazes
        window_width = min(maze_pixel_width * 2 + STATS_WIDTH, MAX_WINDOW_SIZE[0])
        window_height = min(maze_pixel_height, MAX_WINDOW_SIZE[1])
        
        # Set up display
        self.window = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption(f"Maze Race - Level {self.player_game.current_level}/{MAX_LEVELS}")
        self.start_time = time.time()
        self.player_path = [tuple(self.player_pos.astype(int))]
        
        # Initialize AI
        self.init_ai_solver()
        
        # Reset race status
        self.current_winner = None
        self.game_over = False
        self.countdown = 0
        self.ai_reached_goal = False
        self.player_made_first_move = False  # Reset first move flag
        self.ai_resetting = False  # Reset AI reset flag

    def reset_ai_path(self):
        """Reset AI to starting position when it gets stuck"""
        start_pos = np.argwhere(self.ai_maze == 2)[0]
        self.ai_bot.state = tuple(start_pos)
        self.ai_position = np.array([start_pos[0], start_pos[1]], dtype=float)
        self.ai_path = [tuple(start_pos)]
        self.ai_backtracks = 0
        self.ai_resetting = False

    def calculate_player_camera(self):
        """Dynamic camera system for player view"""
        viewport_width = (self.window.get_width() - STATS_WIDTH) // 2
        viewport_height = self.window.get_height()
        
        cam_x = self.player_pos[1] * TILE_SIZE - viewport_width // 2
        cam_y = self.player_pos[0] * TILE_SIZE - viewport_height // 2
        
        max_cam_x = max(0, self.width * TILE_SIZE - viewport_width)
        max_cam_y = max(0, self.height * TILE_SIZE - viewport_height)
        
        return (
            np.clip(cam_x, 0, max_cam_x),
            np.clip(cam_y, 0, max_cam_y)
        )

    def calculate_ai_camera(self):
        """Dynamic camera system for AI view"""
        viewport_width = (self.window.get_width() - STATS_WIDTH) // 2
        viewport_height = self.window.get_height()
        
        # Center on AI position if available
        if self.ai_bot:
            ai_pos_col, ai_pos_row = self.ai_bot.state[1], self.ai_bot.state[0]
        else:
            # Fallback to start position
            ai_pos = np.argwhere(self.ai_maze == 2)[0]
            ai_pos_row, ai_pos_col = ai_pos[0], ai_pos[1]
            
        cam_x = ai_pos_col * TILE_SIZE - viewport_width // 2
        cam_y = ai_pos_row * TILE_SIZE - viewport_height // 2
        
        max_cam_x = max(0, self.width * TILE_SIZE - viewport_width)
        max_cam_y = max(0, self.height * TILE_SIZE - viewport_height)
        
        return (
            np.clip(cam_x, 0, max_cam_x),
            np.clip(cam_y, 0, max_cam_y)
        )

    def draw_maze(self):
        """Render both player and AI mazes side by side"""
        # Calculate camera positions for both views
        player_cam_x, player_cam_y = self.calculate_player_camera()
        ai_cam_x, ai_cam_y = self.calculate_ai_camera()
        
        # Calculate viewport widths with padding
        maze_viewport_width = (self.window.get_width() - STATS_WIDTH) // 2
        viewport_padding = 2  # Add padding between mazes
        
        # Clear the screen
        self.window.fill(BLACK)
        
        # Load shared assets
        wall = pygame.transform.scale(pygame.image.load("assets/wall.jpeg"), (TILE_SIZE, TILE_SIZE))
        exit_img = pygame.transform.scale(pygame.image.load("assets/finish.png"), (TILE_SIZE, TILE_SIZE))
        player_img = pygame.transform.scale(pygame.image.load("assets/player.png"), (TILE_SIZE, TILE_SIZE))
        ai_player_img = pygame.transform.scale(pygame.image.load("assets/player.png"), (TILE_SIZE, TILE_SIZE))
        start_img = pygame.transform.scale(pygame.image.load("assets/start.png"), (TILE_SIZE, TILE_SIZE))
        
        # Apply orange tint to AI player
        ai_player_img.fill((255, 165, 0), special_flags=pygame.BLEND_RGB_MULT)
        
        # Create background once
        bg = pygame.transform.scale(
            pygame.image.load("assets/grass.jpeg"),
            (self.width*TILE_SIZE, self.height*TILE_SIZE)
        )

        # Define viewport rectangles to prevent overlap
        player_viewport = pygame.Rect(0, 0, maze_viewport_width - viewport_padding, self.window.get_height())
        ai_viewport = pygame.Rect(maze_viewport_width + viewport_padding, 0, 
                                 maze_viewport_width - viewport_padding, self.window.get_height())
        
        # Create surfaces for each maze (with clipping)
        player_surface = self.window.subsurface(player_viewport)
        ai_surface = self.window.subsurface(ai_viewport)
        
        # Draw player maze background
        player_surface.blit(bg, (-player_cam_x, -player_cam_y))
        
        # Draw player maze elements
        for row in range(self.height):
            for col in range(self.width):
                x = col*TILE_SIZE - player_cam_x
                y = row*TILE_SIZE - player_cam_y
                
                # Culling off-screen tiles for player maze
                if not (-TILE_SIZE <= x <= player_viewport.width + TILE_SIZE and 
                        -TILE_SIZE <= y <= player_viewport.height + TILE_SIZE):
                    continue
                
                if self.player_maze[row, col] == 1:
                    player_surface.blit(wall, (x, y))
                elif self.player_maze[row, col] == 3:
                    player_surface.blit(exit_img, (x, y))
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    glow.fill((0, 255, 0, 100))
                    player_surface.blit(glow, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
                elif self.player_maze[row, col] == 2:
                    player_surface.blit(start_img, (x, y))
        
        # Draw player path (blue trail)
        if len(self.player_path) > 1:
            for i in range(1, len(self.player_path)):
                prev = (self.player_path[i-1][1]*TILE_SIZE - player_cam_x + TILE_SIZE//2, 
                       self.player_path[i-1][0]*TILE_SIZE - player_cam_y + TILE_SIZE//2)
                curr = (self.player_path[i][1]*TILE_SIZE - player_cam_x + TILE_SIZE//2, 
                       self.player_path[i][0]*TILE_SIZE - player_cam_y + TILE_SIZE//2)
                pygame.draw.line(player_surface, BLUE, prev, curr, 3)
        
        # Draw player character
        player_x = self.player_pos[1]*TILE_SIZE - player_cam_x
        player_y = self.player_pos[0]*TILE_SIZE - player_cam_y
        player_surface.blit(player_img, (player_x, player_y))
        
        # Draw "PLAYER" label at the top of player maze
        player_label = self.font.render("PLAYER", True, WHITE)
        player_surface.blit(player_label, 
                          (player_viewport.width//2 - player_label.get_width()//2, 10))

        # Draw divider
        pygame.draw.line(
            self.window, 
            WHITE, 
            (maze_viewport_width, 0), 
            (maze_viewport_width, self.window.get_height()), 
            2
        )
        
        # Draw AI maze background (right side)
        ai_surface.blit(bg, (-ai_cam_x, -ai_cam_y))
        
        # Draw AI maze (right side)
        for row in range(self.height):
            for col in range(self.width):
                x = col*TILE_SIZE - ai_cam_x
                y = row*TILE_SIZE - ai_cam_y
                
                # Culling off-screen tiles for AI maze
                if not (-TILE_SIZE <= x <= ai_viewport.width + TILE_SIZE and 
                        -TILE_SIZE <= y <= ai_viewport.height + TILE_SIZE):
                    continue
                
                if self.ai_maze[row, col] == 1:
                    ai_surface.blit(wall, (x, y))
                elif self.ai_maze[row, col] == 3:
                    ai_surface.blit(exit_img, (x, y))
                    glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    glow.fill((0, 255, 0, 100))
                    ai_surface.blit(glow, (x, y), special_flags=pygame.BLEND_RGBA_ADD)
                elif self.ai_maze[row, col] == 2:
                    ai_surface.blit(start_img, (x, y))
        
        # Draw AI path (orange trail)
        if len(self.ai_path) > 1:
            for i in range(1, len(self.ai_path)):
                prev = (self.ai_path[i-1][1]*TILE_SIZE - ai_cam_x + TILE_SIZE//2, 
                       self.ai_path[i-1][0]*TILE_SIZE - ai_cam_y + TILE_SIZE//2)
                curr = (self.ai_path[i][1]*TILE_SIZE - ai_cam_x + TILE_SIZE//2, 
                       self.ai_path[i][0]*TILE_SIZE - ai_cam_y + TILE_SIZE//2)
                pygame.draw.line(ai_surface, ORANGE, prev, curr, 3)
        
        # Draw AI character
        if self.ai_bot and not self.ai_reached_goal:
            ai_x = self.ai_bot.state[1]*TILE_SIZE - ai_cam_x
            ai_y = self.ai_bot.state[0]*TILE_SIZE - ai_cam_y
            ai_surface.blit(ai_player_img, (ai_x, ai_y))
        
        # Draw "AI" label at the top of AI maze
        ai_label = self.font.render("AI", True, ORANGE)
        ai_surface.blit(ai_label, 
                      (ai_viewport.width//2 - ai_label.get_width()//2, 10))
        
        # Draw stats panel
        panel_x = maze_viewport_width * 2
        pygame.draw.rect(self.window, (30,30,30), (panel_x, 0, STATS_WIDTH, self.window.get_height()))
        pygame.draw.rect(self.window, (200,200,200), (panel_x, 0, STATS_WIDTH, self.window.get_height()), 3)
        
        # Display race statistics
        stats = [
            (f"Level {self.player_game.current_level}/{MAX_LEVELS}", 50),
            (f"Time: {time.time()-self.start_time:.1f}s", 100),
            (f"Player Moves: {self.player_tracker.total_moves}", 150),
            (f"AI Moves: {self.ai_moves}", 200),
            (f"Player Backtracks: {self.player_tracker.backtracks}", 250),
            (f"AI Backtracks: {self.ai_backtracks}/{AI_BACKTRACK_LIMIT}", 300),
            (f"Score: {self.player_wins} - {self.ai_wins}", 350)
        ]
        
        for text, ypos in stats:
            self.window.blit(self.font.render(text, True, WHITE), (panel_x+20, ypos))
        
        # Show a prompt for the player to move first if they haven't yet
        if not self.player_made_first_move:
            waiting_text = "Move to start the race!"
            wait_surface = self.font.render(waiting_text, True, GREEN)
            self.window.blit(wait_surface, (panel_x+20, 400))
        
        # Show AI reset warning if applicable
        if self.ai_resetting:
            reset_text = "AI is resetting..."
            reset_surface = self.font.render(reset_text, True, ORANGE)
            self.window.blit(reset_surface, (panel_x+20, 420))
        
        # Show winner announcement if game is over
        if self.game_over and self.current_winner:
            overlay = pygame.Surface((self.window.get_width(), self.window.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))  # Semi-transparent black
            self.window.blit(overlay, (0, 0))
            
            winner_text = f"{self.current_winner} WINS!"
            continue_text = "Press SPACE to continue"
            winner_surface = self.big_font.render(winner_text, True, 
                                                 GREEN if self.current_winner == "PLAYER" else ORANGE)
            continue_surface = self.font.render(continue_text, True, WHITE)
            
            self.window.blit(winner_surface, 
                           (self.window.get_width()//2 - winner_surface.get_width()//2, 
                            self.window.get_height()//2 - 50))
            self.window.blit(continue_surface, 
                           (self.window.get_width()//2 - continue_surface.get_width()//2, 
                            self.window.get_height()//2 + 20))

    def move_player(self, dx, dy):
        """Player movement with collision detection"""
        # Don't allow moves if game is over
        if self.game_over:
            return
            
        new_pos = self.player_pos + [dx, dy]
        new_x, new_y = new_pos.astype(int)

        if (0 <= new_x < self.height and 
            0 <= new_y < self.width and 
            self.player_maze[new_x, new_y] != 1):
            
            # Mark that player has made their first move
            if not self.player_made_first_move:
                self.player_made_first_move = True
                # Reset the start time to be fair
                self.start_time = time.time()
            
            # Backtrack detection
            current = (new_x, new_y)
            if current in self.player_path[:-1]:
                self.player_tracker.backtracks += 1

            # Smooth animation
            prev_pos = self.player_pos.copy()
            for t in np.linspace(0, 1, 5):
                self.player_pos = prev_pos + (dx * t, dy * t)
                self.draw_maze()
                pygame.display.flip()
                self.clock.tick(60)

            # Finalize position
            self.player_pos = new_pos
            self.player_path.append(current)
            self.player_tracker.total_moves += 1

            # Check level completion
            if self.player_maze[new_x, new_y] == 3:
                if not self.ai_reached_goal:
                    # Player won!
                    self.current_winner = "PLAYER"
                    self.game_over = True
                    self.player_wins += 1
                    self.races += 1
                self.player_tracker.complete_maze()

    def run_ai_step(self):
        """Process AI movement"""
        # Only move AI if player has made their first move
        if not self.player_made_first_move:
            return
            
        # Don't move AI if game is over
        if self.game_over or self.ai_reached_goal or not self.ai_bot:
            return
            
        # Check if AI needs to reset due to excessive backtracks
        if self.ai_backtracks > AI_BACKTRACK_LIMIT:
            self.ai_resetting = True
            self.reset_ai_path()
            return
            
        # Get current maze dimensions
        maze_height, maze_width = self.ai_maze.shape
            
        # Let the AI decide its next move
        prev_state = self.ai_bot.state
        try:
            new_state = self.ai_bot.step()
        except Exception:
            return
            
        # Handle valid moves
        if new_state != "regenerate" and (0 <= new_state[0] < maze_height and 0 <= new_state[1] < maze_width):
            # Update AI position
            if new_state != prev_state:
                self.ai_path.append(new_state)
                self.ai_moves += 1
                
                # Detect backtracks
                if tuple(new_state) in [tuple(pos) for pos in self.ai_path[:-1]]:
                    self.ai_backtracks += 1
                    
                # Check if AI reached goal
                if new_state == self.ai_bot.goal:
                    self.ai_reached_goal = True
                    if self.current_winner is None:  # Only set winner if player hasn't won yet
                        self.current_winner = "AI"
                        self.game_over = True
                        self.ai_wins += 1
                        self.races += 1

    def show_game_completion(self):
        """Show game completion screen with final scores"""
        overlay = pygame.Surface((self.window.get_width(), self.window.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Darker semi-transparent black
        self.window.blit(overlay, (0, 0))
        
        texts = [
            ("GAME COMPLETED!", self.big_font, WHITE, -100),
            (f"Final Score: Player {self.player_wins} - AI {self.ai_wins}", self.font, WHITE, -20),
            ("Press SPACE to play again", self.font, WHITE, 50)
        ]
        
        for text, font, color, y_offset in texts:
            surface = font.render(text, True, color)
            self.window.blit(surface, 
                           (self.window.get_width()//2 - surface.get_width()//2, 
                            self.window.get_height()//2 + y_offset))
        
        pygame.display.flip()
        
        # Wait for player to press SPACE
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    waiting = False
                    # Reset game stats
                    self.player_wins = 0
                    self.ai_wins = 0
                    self.races = 0

    def draw_main_menu(self):
        """Render the main menu."""
        self.window.fill(BLACK)
        title = self.big_font.render("Maze Race", True, WHITE)
        start_text = self.font.render("Press ENTER to Start", True, GREEN)
        quit_text = self.font.render("Press Q to Quit", True, RED)

        self.window.blit(title, (self.window.get_width() // 2 - title.get_width() // 2, 100))
        self.window.blit(start_text, (self.window.get_width() // 2 - start_text.get_width() // 2, 200))
        self.window.blit(quit_text, (self.window.get_width() // 2 - quit_text.get_width() // 2, 250))
        pygame.display.flip()

    def draw_pause_menu(self):
        """Render the pause menu."""
        overlay = pygame.Surface((self.window.get_width(), self.window.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.window.blit(overlay, (0, 0))

        paused_text = self.big_font.render("Paused", True, WHITE)
        resume_text = self.font.render("Press R to Resume", True, GREEN)
        quit_text = self.font.render("Press Q to Quit", True, RED)

        self.window.blit(paused_text, (self.window.get_width() // 2 - paused_text.get_width() // 2, 100))
        self.window.blit(resume_text, (self.window.get_width() // 2 - resume_text.get_width() // 2, 200))
        self.window.blit(quit_text, (self.window.get_width() // 2 - quit_text.get_width() // 2, 250))
        pygame.display.flip()

    def handle_events(self):
        """Process user input and AI movement timer"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == "main_menu":
                    if event.key == pygame.K_RETURN:
                        self.state = "playing"
                    elif event.key == pygame.K_q:
                        self.running = False
                elif self.state == "playing":
                    if event.key == pygame.K_p:
                        self.state = "paused"
                    elif event.key == pygame.K_UP:
                        self.move_player(-1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.move_player(1, 0)
                    elif event.key == pygame.K_LEFT:
                        self.move_player(0, -1)
                    elif event.key == pygame.K_RIGHT:
                        self.move_player(0, 1)
                elif self.state == "paused":
                    if event.key == pygame.K_r:
                        self.state = "playing"
                    elif event.key == pygame.K_q:
                        self.running = False
            elif event.type == AI_UPDATE_EVENT and self.state == "playing":
                self.run_ai_step()

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            if self.state == "main_menu":
                self.draw_main_menu()
            elif self.state == "playing":
                self.draw_maze()
                pygame.display.flip()
                self.clock.tick(MAX_FPS)
            elif self.state == "paused":
                self.draw_pause_menu()
        pygame.quit()

if __name__ == "__main__":
    game = MazeRaceUI()
    game.run()