import pygame
import time
import random
import numpy as np
import os
from utils.config import *
from gui.retro_theme import RetroTheme
from gui.pause_menu import PauseMenu
from logic.adaptive_logic import AdaptiveMazeGame
from logic.ai_bot_logic import EnhancedMazeBot

class PlayerVsBotGame:
    """Player vs Bot racing game mode."""
    
    def __init__(self, screen, player_id="Player1"):
        """Initialize the player vs bot game."""
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Initialize game state
        self.running = True
        self.paused = False
        self.clock = pygame.time.Clock()
        self.state = STATE_PLAYER_VS_BOT
        
        # Load theme
        self.theme = RetroTheme()
        
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
        
        # Create pause menu
        self.pause_menu = PauseMenu(self.screen, self.resume_game, self.return_to_main_menu)
        
        # Load level and start AI timer
        self.load_new_level()
        pygame.time.set_timer(AI_UPDATE_EVENT, AI_UPDATE_INTERVAL)
    
    def init_ai_solver(self):
        """Initialize AI bot for the AI's maze"""
        current_size = self.ai_game.maze.shape
        bot_filename = f"bot_{current_size[0]}x{current_size[1]}_lvl_1.npy"
        
        # Look for the AI model in assets/bots folder
        bot_dir = os.path.join(ASSET_DIR, "bots")
        if not os.path.exists(bot_dir):
            os.makedirs(bot_dir)
        
        # Initialize EnhancedMazeBot with appropriate difficulty level
        self.ai_bot = EnhancedMazeBot(self.ai_game, level=self.player_game.current_level)
        
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
        # Generate player maze with adaptive difficulty
        self.player_game.generate_maze()
        self.player_tracker = self.player_game.create_player_tracker()
        self.player_tracker.start_tracking()
        
        # Store maze data for player
        self.player_maze = self.player_game.maze.copy()
        self.maze_height, self.maze_width = self.player_maze.shape
        
        # Create identical maze for AI
        self.ai_game.maze = self.player_maze.copy()
        self.ai_maze = self.ai_game.maze
        
        # Player starts at entry point (value 2 in maze)
        self.player_pos = np.argwhere(self.player_maze == 2)[0].astype(float)
        
        # Calculate pixel dimensions
        self.maze_pixel_width = self.maze_width * TILE_SIZE
        self.maze_pixel_height = self.maze_height * TILE_SIZE
        
        # Calculate panel dimensions (constrained to 800x800 total for both panels)
        max_panel_width = min(800, self.maze_pixel_width * 2) // 2
        self.panel_width = max_panel_width
        self.panel_height = min(800, self.maze_pixel_height)
        
        # Initialize AI
        self.init_ai_solver()
        
        # Reset race status
        self.current_winner = None
        self.game_over = False
        self.player_path = [tuple(self.player_pos.astype(int))]
        self.ai_path = [self.ai_bot.state]
        self.player_made_first_move = False
        self.ai_resetting = False
        
        # Timer
        self.start_time = time.time()
    
    def complete_level(self, winner):
        """Progress to next level with difficulty adjustment."""
        # Record completion for player
        self.player_tracker.complete_maze()
        
        # Update player difficulty based on performance
        player_performance = self.player_tracker.get_performance_data()
        self.player_game.update_difficulty(player_performance)
        
        # Update AI difficulty based on race results
        ai_performance = self.ai_bot.get_performance_data()
        
        # Adjust AI difficulty - make it harder if AI loses, easier if AI wins
        if winner == "PLAYER":
            # Increase AI difficulty slightly when player wins
            ai_performance["completion_time"] = max(30, ai_performance["completion_time"] * 0.85)
        else:
            # Decrease AI difficulty slightly when AI wins
            ai_performance["completion_time"] = min(240, ai_performance["completion_time"] * 1.15)
        
        self.ai_game.update_difficulty(ai_performance)
        
        # Explicitly adjust levels to match
        self.ai_game.current_level = self.player_game.current_level
        
        # Load new level with updated difficulty
        self.load_new_level()
    
    def reset_ai_path(self):
        """Reset AI to starting position when it gets stuck"""
        start_pos = np.argwhere(self.ai_maze == 2)[0]
        self.ai_bot.state = tuple(start_pos)
        self.ai_position = np.array([start_pos[0], start_pos[1]], dtype=float)
        self.ai_path = [tuple(start_pos)]
        self.ai_backtracks = 0
        self.ai_resetting = False
    
    def calculate_player_camera(self):
        """Calculate camera position for player view"""
        # Center camera on player
        cam_x = self.player_pos[1] * TILE_SIZE - self.panel_width // 2
        cam_y = self.player_pos[0] * TILE_SIZE - self.panel_height // 2
        
        # Clamp camera to maze boundaries
        max_cam_x = max(0, self.maze_pixel_width - self.panel_width)
        max_cam_y = max(0, self.maze_pixel_height - self.panel_height)
        
        return (max(0, min(cam_x, max_cam_x)), 
                max(0, min(cam_y, max_cam_y)))
    
    def calculate_ai_camera(self):
        """Calculate camera position for AI view"""
        # Center on AI position if available
        if self.ai_bot:
            ai_pos_col, ai_pos_row = self.ai_bot.state[1], self.ai_bot.state[0]
        else:
            # Fallback to start position
            ai_pos = np.argwhere(self.ai_maze == 2)[0]
            ai_pos_row, ai_pos_col = ai_pos[0], ai_pos[1]
        
        # Center camera on AI
        cam_x = ai_pos_col * TILE_SIZE - self.panel_width // 2
        cam_y = ai_pos_row * TILE_SIZE - self.panel_height // 2
        
        # Clamp camera to maze boundaries
        max_cam_x = max(0, self.maze_pixel_width - self.panel_width)
        max_cam_y = max(0, self.maze_pixel_height - self.panel_height)
        
        return (max(0, min(cam_x, max_cam_x)), 
                max(0, min(cam_y, max_cam_y)))
    
    def draw_game(self):
        """Draw the game screen with both mazes side by side."""
        # Fill background
        self.screen.fill(BLACK)
        
        # Calculate camera positions
        player_cam_x, player_cam_y = self.calculate_player_camera()
        ai_cam_x, ai_cam_y = self.calculate_ai_camera()
        
        # Calculate panel positions (center horizontally with spacing between)
        panel_spacing = 20
        total_width = (self.panel_width * 2) + panel_spacing
        start_x = (self.width - total_width) // 2
        panel_y = (self.height - self.panel_height) // 2
        
        player_panel_x = start_x
        ai_panel_x = start_x + self.panel_width + panel_spacing
        
        # Create game panels
        player_panel = pygame.Surface((self.panel_width, self.panel_height))
        ai_panel = pygame.Surface((self.panel_width, self.panel_height))
        player_panel.fill(BLACK)
        ai_panel.fill(BLACK)
        
        # Draw player maze
        for row in range(self.maze_height):
            for col in range(self.maze_width):
                # Calculate tile position within panel
                x = col * TILE_SIZE - player_cam_x
                y = row * TILE_SIZE - player_cam_y
                
                # Skip tiles outside the panel
                if (x + TILE_SIZE <= 0 or x >= self.panel_width or
                    y + TILE_SIZE <= 0 or y >= self.panel_height):
                    continue
                
                # Draw appropriate tile
                if self.player_maze[row, col] == 1:  # Wall
                    player_panel.blit(self.theme.wall_tile, (x, y))
                elif self.player_maze[row, col] == 0:  # Path
                    player_panel.blit(self.theme.path_tile, (x, y))
                elif self.player_maze[row, col] == 2:  # Start
                    player_panel.blit(self.theme.start_tile, (x, y))
                elif self.player_maze[row, col] == 3:  # Goal
                    player_panel.blit(self.theme.goal_tile, (x, y))
        
        # Draw player path
        if len(self.player_path) > 1:
            for i in range(1, len(self.player_path)):
                prev = (self.player_path[i-1][1]*TILE_SIZE - player_cam_x + TILE_SIZE//2, 
                       self.player_path[i-1][0]*TILE_SIZE - player_cam_y + TILE_SIZE//2)
                curr = (self.player_path[i][1]*TILE_SIZE - player_cam_x + TILE_SIZE//2, 
                       self.player_path[i][0]*TILE_SIZE - player_cam_y + TILE_SIZE//2)
                pygame.draw.line(player_panel, NEON_BLUE, prev, curr, 3)
        
        # Draw player sprite
        player_x = self.player_pos[1] * TILE_SIZE - player_cam_x
        player_y = self.player_pos[0] * TILE_SIZE - player_cam_y
        player_panel.blit(self.theme.player_sprite, (player_x, player_y))
        
        # Draw player label
        player_label = self.theme.get_glowing_text("PLAYER", 24, NEON_BLUE)
        player_panel.blit(player_label, ((self.panel_width - player_label.get_width()) // 2, 10))
        
        # Draw AI maze
        for row in range(self.maze_height):
            for col in range(self.maze_width):
                # Calculate tile position within panel
                x = col * TILE_SIZE - ai_cam_x
                y = row * TILE_SIZE - ai_cam_y
                
                # Skip tiles outside the panel
                if (x + TILE_SIZE <= 0 or x >= self.panel_width or
                    y + TILE_SIZE <= 0 or y >= self.panel_height):
                    continue
                
                # Draw appropriate tile
                if self.ai_maze[row, col] == 1:  # Wall
                    ai_panel.blit(self.theme.wall_tile, (x, y))
                elif self.ai_maze[row, col] == 0:  # Path
                    ai_panel.blit(self.theme.path_tile, (x, y))
                elif self.ai_maze[row, col] == 2:  # Start
                    ai_panel.blit(self.theme.start_tile, (x, y))
                elif self.ai_maze[row, col] == 3:  # Goal
                    ai_panel.blit(self.theme.goal_tile, (x, y))
        
        # Draw AI path
        if len(self.ai_path) > 1:
            for i in range(1, len(self.ai_path)):
                prev = (self.ai_path[i-1][1]*TILE_SIZE - ai_cam_x + TILE_SIZE//2, 
                       self.ai_path[i-1][0]*TILE_SIZE - ai_cam_y + TILE_SIZE//2)
                curr = (self.ai_path[i][1]*TILE_SIZE - ai_cam_x + TILE_SIZE//2, 
                       self.ai_path[i][0]*TILE_SIZE - ai_cam_y + TILE_SIZE//2)
                pygame.draw.line(ai_panel, NEON_PURPLE, prev, curr, 3)
        
        # Draw AI sprite (with modified color)
        if self.ai_bot and not self.ai_reached_goal:
            ai_x = self.ai_bot.state[1] * TILE_SIZE - ai_cam_x
            ai_y = self.ai_bot.state[0] * TILE_SIZE - ai_cam_y
            
            # Use a modified version of player sprite with different color
            bot_sprite = self.theme.bot_sprite
            ai_panel.blit(bot_sprite, (ai_x, ai_y))
        
        # Draw AI label
        ai_label = self.theme.get_glowing_text("AI", 24, NEON_PURPLE)
        ai_panel.blit(ai_label, ((self.panel_width - ai_label.get_width()) // 2, 10))
        
        # Blit panels to screen
        self.screen.blit(player_panel, (player_panel_x, panel_y))
        self.screen.blit(ai_panel, (ai_panel_x, panel_y))
        
        # Draw panel borders
        pygame.draw.rect(self.screen, NEON_BLUE, 
                        (player_panel_x-2, panel_y-2, self.panel_width+4, self.panel_height+4), 2)
        pygame.draw.rect(self.screen, NEON_PURPLE, 
                        (ai_panel_x-2, panel_y-2, self.panel_width+4, self.panel_height+4), 2)
        
        # Draw stats
        stats_x = ai_panel_x + self.panel_width + 20
        stats_y = panel_y
        self.draw_stats(stats_x, stats_y)
        
        # Draw winner announcement if game is over
        if self.game_over and self.current_winner:
            self.draw_winner_announcement()
    
    def draw_stats(self, x, y):
        """Draw game statistics."""
        stats = [
            f"Level: {self.player_game.current_level}",
            f"Time: {time.time() - self.start_time:.1f}s",
            f"Player Moves: {self.player_tracker.total_moves}",
            f"AI Moves: {self.ai_moves}",
            f"Player Backtracks: {self.player_tracker.backtracks}",
            f"AI Backtracks: {self.ai_backtracks}/{10}",
            f"Score: {self.player_wins} - {self.ai_wins}"
        ]
        
        for i, stat in enumerate(stats):
            text = self.theme.medium_font.render(stat, True, NEON_GREEN)
            self.screen.blit(text, (x, y + i * 30))
        
        # Show a prompt for the player to move first if they haven't yet
        if not self.player_made_first_move:
            prompt_y = y + (len(stats) + 1) * 30
            waiting_text = self.theme.get_glowing_text("Move to start the race!", 24, NEON_YELLOW)
            self.screen.blit(waiting_text, (x, prompt_y))
        
        # Show AI reset warning if applicable
        if self.ai_resetting:
            reset_y = y + (len(stats) + 2) * 30
            reset_text = self.theme.get_glowing_text("AI is resetting...", 24, NEON_PINK)
            self.screen.blit(reset_text, (x, reset_y))
    
    def draw_winner_announcement(self):
        """Draw winner announcement overlay."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Create winner text
        winner_color = NEON_GREEN if self.current_winner == "PLAYER" else NEON_PURPLE
        winner_text = self.theme.get_glowing_text(f"{self.current_winner} WINS!", 48, winner_color)
        continue_text = self.theme.get_glowing_text("Press SPACE to continue", 28, NEON_CYAN)
        
        # Center and draw texts
        winner_x = (self.width - winner_text.get_width()) // 2
        continue_x = (self.width - continue_text.get_width()) // 2
        
        self.screen.blit(winner_text, (winner_x, self.height // 2 - 50))
        self.screen.blit(continue_text, (continue_x, self.height // 2 + 20))
    
    def move_player(self, dx, dy):
        """Move player with collision detection."""
        # Don't allow moves if game is over
        if self.game_over or self.paused:
            return
        
        new_pos = self.player_pos + [dy, dx]
        new_row, new_col = new_pos.astype(int)
        
        # Check if move is valid (within bounds and not a wall)
        if (0 <= new_row < self.maze_height and 
            0 <= new_col < self.maze_width and 
            self.player_maze[new_row, new_col] != 1):
            
            # Mark that player has made their first move
            if not self.player_made_first_move:
                self.player_made_first_move = True
                # Reset the start time to be fair
                self.start_time = time.time()
            
            # Check for backtracking
            current = (new_row, new_col)
            if current in self.player_path[:-1]:
                self.player_tracker.backtracks += 1
            
            # Update position
            self.player_pos = new_pos
            self.player_path.append(current)
            self.player_tracker.total_moves += 1
            
            # Check if reached goal
            if self.player_maze[new_row, new_col] == 3:
                if not self.ai_reached_goal:
                    # Player won!
                    self.current_winner = "PLAYER"
                    self.game_over = True
                    self.player_wins += 1
                    self.races += 1
                self.player_tracker.complete_maze()
    
    def run_ai_step(self):
        """Process AI movement."""
        # Only move AI if player has made their first move and game is not paused
        if not self.player_made_first_move or self.paused:
            return
        
        # Don't move AI if game is over
        if self.game_over or self.ai_reached_goal or not self.ai_bot:
            return
        
        # Check if AI needs to reset due to excessive backtracks
        if self.ai_backtracks > AI_BACKTRACK_LIMIT:
            self.ai_resetting = True
            self.reset_ai_path()
            return
        
        # Let the AI decide its next move
        prev_state = self.ai_bot.state
        try:
            new_state = self.ai_bot.step()
        except Exception:
            return
        
        # Handle valid moves
        if new_state != "regenerate" and (0 <= new_state[0] < self.maze_height and 0 <= new_state[1] < self.maze_width):
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
        """Show game completion screen with final scores."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Create completion texts
        completion_text = self.theme.get_glowing_text("GAME COMPLETED!", 48, NEON_YELLOW)
        score_text = self.theme.get_glowing_text(f"Final Score: Player {self.player_wins} - AI {self.ai_wins}", 28, NEON_CYAN)
        action_text = self.theme.get_glowing_text("Press SPACE to play again", 28, NEON_GREEN)
        
        # Center and draw texts
        completion_x = (self.width - completion_text.get_width()) // 2
        score_x = (self.width - score_text.get_width()) // 2
        action_x = (self.width - action_text.get_width()) // 2
        
        self.screen.blit(completion_text, (completion_x, self.height // 2 - 100))
        self.screen.blit(score_text, (score_x, self.height // 2 - 20))
        self.screen.blit(action_text, (action_x, self.height // 2 + 50))
        
        pygame.display.flip()
        
        # Wait for player to press SPACE
        waiting = True
        while waiting and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
                        # Reset game stats and load new level
                        self.player_wins = 0
                        self.ai_wins = 0
                        self.races = 0
                        self.load_new_level()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                        waiting = False
    
    def handle_events(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.toggle_pause()
                elif event.key == pygame.K_UP:
                    self.move_player(0, -1)
                elif event.key == pygame.K_DOWN:
                    self.move_player(0, 1)
                elif event.key == pygame.K_LEFT:
                    self.move_player(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_player(1, 0)
                elif self.game_over and event.key == pygame.K_SPACE:
                    if self.player_game.current_level > MAX_LEVELS:
                        self.show_game_completion()
                    else:
                        self.complete_level(self.current_winner)
            
            elif event.type == AI_UPDATE_EVENT and not self.paused and not self.game_over:
                self.run_ai_step()
    
    def toggle_pause(self):
        """Toggle the pause state of the game."""
        self.paused = not self.paused
    
    def resume_game(self):
        """Resume the game from pause."""
        self.paused = False
    
    def return_to_main_menu(self):
        """Return to main menu."""
        self.running = False
    
    def run(self):
        """Main game loop."""
        while self.running:
            if self.paused:
                self.pause_menu.draw()
                self.pause_menu.handle_events()
            else:
                self.handle_events()
                self.draw_game()
            
            pygame.display.flip()
            self.clock.tick(FPS)