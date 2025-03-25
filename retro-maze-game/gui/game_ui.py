import pygame
import time
import numpy as np
from utils.config import *
from gui.retro_theme import RetroTheme
from gui.pause_menu import PauseMenu
from logic.adaptive_logic import AdaptiveMazeGame

class SinglePlayerGame:
    """Single player maze game mode."""
    
    def __init__(self, screen, player_id="Player1"):
        """Initialize the single player game."""
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Initialize game state
        self.running = True
        self.paused = False
        self.clock = pygame.time.Clock()
        self.state = STATE_SINGLE_PLAYER
        
        # Load theme
        self.theme = RetroTheme()
        
        # Create adaptive maze game
        self.game = AdaptiveMazeGame(player_id)
        
        # Initialize game elements
        self.load_new_level()
        
        # Create pause menu
        self.pause_menu = PauseMenu(self.screen, self.resume_game, self.return_to_main_menu)
    
    def load_new_level(self):
        """Generate new level with player tracking."""
        # Generate maze
        self.game.generate_maze()
        self.player_tracker = self.game.create_player_tracker()
        self.player_tracker.start_tracking()
        
        # Get maze dimensions
        self.maze = self.game.maze
        self.maze_height, self.maze_width = self.maze.shape
        
        # Player starts at entry point (value 2 in maze)
        self.player_pos = np.argwhere(self.maze == 2)[0].astype(float)
        
        # Calculate pixel dimensions
        self.maze_pixel_width = self.maze_width * TILE_SIZE
        self.maze_pixel_height = self.maze_height * TILE_SIZE
        
        # Calculate game panel dimensions (constrained to 800x800)
        self.panel_width = min(800, self.maze_pixel_width)
        self.panel_height = min(800, self.maze_pixel_height)
        
        # Path tracking for backtracking detection
        self.path = [tuple(self.player_pos.astype(int))]
        
        # Timer 
        self.start_time = time.time()
    
    def calculate_camera(self):
        """Calculate camera position to follow player."""
        # Center camera on player
        cam_x = self.player_pos[1] * TILE_SIZE - self.panel_width // 2
        cam_y = self.player_pos[0] * TILE_SIZE - self.panel_height // 2
        
        # Clamp camera to maze boundaries
        max_cam_x = max(0, self.maze_pixel_width - self.panel_width)
        max_cam_y = max(0, self.maze_pixel_height - self.panel_height)
        
        return (max(0, min(cam_x, max_cam_x)), 
                max(0, min(cam_y, max_cam_y)))
    
    def draw_game(self):
        """Draw the game screen."""
        # Fill background
        self.screen.fill(BLACK)
        
        # Calculate camera position
        cam_x, cam_y = self.calculate_camera()
        
        # Calculate panel position (center it on screen)
        panel_x = (self.width - self.panel_width) // 2
        panel_y = (self.height - self.panel_height) // 2
        
        # Create game panel
        game_panel = pygame.Surface((self.panel_width, self.panel_height))
        game_panel.fill(BLACK)
        
        # Draw maze tiles on panel
        for row in range(self.maze_height):
            for col in range(self.maze_width):
                # Calculate tile position within panel
                x = col * TILE_SIZE - cam_x
                y = row * TILE_SIZE - cam_y
                
                # Skip tiles outside the panel
                if (x + TILE_SIZE <= 0 or x >= self.panel_width or
                    y + TILE_SIZE <= 0 or y >= self.panel_height):
                    continue
                
                # Draw appropriate tile
                if self.maze[row, col] == 1:  # Wall
                    game_panel.blit(self.theme.wall_tile, (x, y))
                elif self.maze[row, col] == 0:  # Path
                    game_panel.blit(self.theme.path_tile, (x, y))
                elif self.maze[row, col] == 2:  # Start
                    game_panel.blit(self.theme.start_tile, (x, y))
                elif self.maze[row, col] == 3:  # Goal
                    game_panel.blit(self.theme.goal_tile, (x, y))
        
        # Draw player
        player_x = self.player_pos[1] * TILE_SIZE - cam_x
        player_y = self.player_pos[0] * TILE_SIZE - cam_y
        game_panel.blit(self.theme.player_sprite, (player_x, player_y))
        
        # Blit panel to screen
        self.screen.blit(game_panel, (panel_x, panel_y))
        
        # Draw game panel border
        pygame.draw.rect(self.screen, NEON_BLUE, 
                       (panel_x-2, panel_y-2, self.panel_width+4, self.panel_height+4), 
                       2)
        
        # Draw stats
        self.draw_stats(panel_x + self.panel_width + 20, panel_y)
    
    def draw_stats(self, x, y):
        """Draw game statistics."""
        stats = [
            f"Level: {self.game.current_level}",
            f"Time: {time.time() - self.start_time:.1f}s",
            f"Moves: {self.player_tracker.total_moves}",
            f"Backtracks: {self.player_tracker.backtracks}",
            f"Difficulty: {self.game.difficulty}"
        ]
        
        for i, stat in enumerate(stats):
            text = self.theme.medium_font.render(stat, True, NEON_GREEN)
            self.screen.blit(text, (x, y + i * 30))
    
    def move_player(self, dx, dy):
        """Move player with collision detection."""
        new_pos = self.player_pos + [dy, dx]
        new_row, new_col = new_pos.astype(int)
        
        # Check if move is valid (within bounds and not a wall)
        if (0 <= new_row < self.maze_height and 
            0 <= new_col < self.maze_width and 
            self.maze[new_row, new_col] != 1):
            
            # Check for backtracking
            current = (new_row, new_col)
            if current in self.path[:-1]:
                self.player_tracker.backtracks += 1
            
            # Update position
            self.player_pos = new_pos
            self.path.append(current)
            self.player_tracker.total_moves += 1
            
            # Check if reached goal
            if self.maze[new_row, new_col] == 3:
                self.complete_level()
    
    def complete_level(self):
        """Progress to next level."""
        self.player_tracker.complete_maze()
        self.game.update_difficulty(self.player_tracker.get_performance_data())
        self.load_new_level()
    
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