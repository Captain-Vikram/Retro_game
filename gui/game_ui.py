import pygame
import time
import random
import numpy as np
from utils.config import *
from gui.retro_theme import RetroTheme
from gui.pause_menu import PauseMenu
from logic.adaptive_logic import AdaptiveMazeGame
import math
import os

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
        
        # Load background music
        self.load_background_music()
        
        # Create adaptive maze game
        self.game = AdaptiveMazeGame(player_id)
        
        # Initialize game elements
        self.load_new_level()
        
        # Create pause menu
        self.pause_menu = PauseMenu(self.screen, self.resume_game, self.return_to_main_menu)
        
        # Create starfield for background
        self.stars = []
        self.create_starfield()
    
    def load_background_music(self):
        """Load and play the background music for gameplay and pause menu."""
        try:
            music_path = os.path.join('assets', 'sound', 'pausemenu1.mp3')
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.5)  # Set to 50% volume
                pygame.mixer.music.play(-1)  # Loop indefinitely
                print("Background music loaded and playing")
            else:
                print(f"Background music file not found at {music_path}")
        except Exception as e:
            print(f"Error loading background music: {e}")
    
    def create_starfield(self):
        """Create stars for the background animation."""
        # Calculate how many stars based on screen size
        stars_count = (self.width * self.height) // 1500
        
        # Create stars with random properties
        for _ in range(stars_count):
            # Ensure stars are outside the game panel area
            panel_x = (self.width - self.panel_width) // 2
            panel_y = (self.height - self.panel_height) // 2
            
            # Pick a side (0=top, 1=right, 2=bottom, 3=left)
            side = random.randint(0, 3)
            
            if side == 0:  # Top
                x = random.randint(0, self.width)
                y = random.randint(0, panel_y - 10)
            elif side == 1:  # Right
                x = random.randint(panel_x + self.panel_width + 10, self.width)
                y = random.randint(0, self.height)
            elif side == 2:  # Bottom
                x = random.randint(0, self.width)
                y = random.randint(panel_y + self.panel_height + 10, self.height)
            else:  # Left
                x = random.randint(0, panel_x - 10)
                y = random.randint(0, self.height)
                
            size = random.uniform(0.5, 3.0)
            brightness = random.random()
            twinkle_speed = random.uniform(0.01, 0.05)
            color_base = random.choice([
                NEON_BLUE, NEON_CYAN, WHITE, NEON_PURPLE
            ])
            
            self.stars.append({
                'x': x, 
                'y': y,
                'size': size,
                'brightness': brightness,
                'twinkle_speed': twinkle_speed,
                'twinkle_direction': random.choice([-1, 1]),
                'color_base': color_base
            })
    
    def update_stars(self):
        """Update star animation properties."""
        for star in self.stars:
            # Update brightness for twinkling effect
            star['brightness'] += star['twinkle_speed'] * star['twinkle_direction']
            
            # Reverse direction at brightness limits
            if star['brightness'] >= 1.0:
                star['brightness'] = 1.0
                star['twinkle_direction'] = -1
            elif star['brightness'] <= 0.2:
                star['brightness'] = 0.2
                star['twinkle_direction'] = 1
    
    def draw_stars(self):
        """Draw the animated starfield in the background."""
        for star in self.stars:
            # Calculate color based on brightness
            brightness = star['brightness']
            base_color = star['color_base']
            color = tuple(int(c * brightness) for c in base_color[:3])
            
            # Draw star with glow effect for larger stars
            if star['size'] > 1.5:
                # Draw glow first
                glow_radius = star['size'] * 2.5
                glow_surface = pygame.Surface((int(glow_radius*2), int(glow_radius*2)), pygame.SRCALPHA)
                glow_color = (*color, int(50 * brightness))
                pygame.draw.circle(glow_surface, glow_color, 
                                (int(glow_radius), int(glow_radius)), int(glow_radius))
                self.screen.blit(glow_surface, 
                               (int(star['x'] - glow_radius), int(star['y'] - glow_radius)))
            
            # Draw the actual star
            pygame.draw.circle(self.screen, color, (int(star['x']), int(star['y'])), star['size'])
    
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
        
        # Prepare the background image to match maze size
        if hasattr(self.theme, 'prepare_background'):
            self.theme.prepare_background(self.maze_pixel_width, self.maze_pixel_height)
        
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
        """Draw the game elements."""
        # Fill background with darker color
        self.screen.fill((3, 5, 10))
        
        # Draw stars in background first
        self.draw_stars()
        
        # Update star animation
        self.update_stars()
        
        # Calculate panel position to center it
        panel_x = (self.width - self.panel_width) // 2
        panel_y = (self.height - self.panel_height) // 2
        
        # Calculate camera position
        cam_x, cam_y = self.calculate_camera()
        
        # Create panel surface
        panel = pygame.Surface((self.panel_width, self.panel_height))
        
        # Draw maze on panel
        self._create_maze_panel(panel, cam_x, cam_y)
        
        # Blit panel to screen
        self.screen.blit(panel, (panel_x, panel_y))
        
        # Draw border
        pygame.draw.rect(self.screen, NEON_GREEN, 
                      (panel_x-2, panel_y-2, self.panel_width+4, self.panel_height+4), 2)
        
        # Draw stats
        self.draw_stats(10, 10)
        
        # Add glow effect to the finishing point
        for row in range(self.maze_height):
            for col in range(self.maze_width):
                if self.maze[row, col] == 3:  # 3 represents the finishing point
                    # Convert maze coordinates to screen coordinates
                    screen_x = panel_x + (col * TILE_SIZE - cam_x)
                    screen_y = panel_y + (row * TILE_SIZE - cam_y)
                    
                    # Only draw if visible on screen
                    if (0 <= screen_x <= self.width and 0 <= screen_y <= self.height):
                        # Create glow effect
                        glow_radius = TILE_SIZE * 1.5
                        glow_surface = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
                        
                        # Animated pulsing glow
                        pulse = (math.sin(time.time() * 3) + 1) * 0.5
                        glow_color = (255, 255, 0, int(100 * pulse + 50))  # Yellow glow with pulsing transparency
                        
                        pygame.draw.circle(glow_surface, glow_color, 
                                         (int(glow_radius), int(glow_radius)), int(glow_radius))
                        
                        # Position the glow centered on the finish tile
                        glow_x = screen_x - glow_radius + TILE_SIZE // 2
                        glow_y = screen_y - glow_radius + TILE_SIZE // 2
                        
                        # Blit the glow effect onto the screen
                        self.screen.blit(glow_surface, (int(glow_x), int(glow_y)))
    
    def _create_maze_panel(self, panel, cam_x, cam_y):
        """Create a maze panel with proper styling and optimal performance."""
        # Initialize common variables
        visible_rect = pygame.Rect(-TILE_SIZE, -TILE_SIZE, self.panel_width + 2*TILE_SIZE, self.panel_height + 2*TILE_SIZE)
        
        # Draw background - optimized for different background types
        if hasattr(self.theme, 'background_image') and self.theme.background_image:
            # Fill base color for better visibility
            panel.fill((15, 20, 35))
            
            # Use background image with parallax effect
            bg_img = self.theme.background_image
            bg_width, bg_height = bg_img.get_size()
            
            # Calculate offset for parallax scrolling (slower than camera)
            bg_offset_x = int(cam_x * 0.6) % bg_width
            bg_offset_y = int(cam_y * 0.6) % bg_height
            
            # Draw only necessary background tiles (optimization)
            for x in range(-bg_offset_x, self.panel_width + bg_width, bg_width):
                for y in range(-bg_offset_y, self.panel_height + bg_height, bg_height):
                    if (x + bg_width >= 0 and x <= self.panel_width and 
                        y + bg_height >= 0 and y <= self.panel_height):
                        panel.blit(bg_img, (x, y))
        else:
            # Grid fallback with optimized drawing
            panel.fill((15, 25, 45))
            
            # Draw grid with consistent appearance
            grid_color = (60, 100, 160, 70)
            grid_spacing = TILE_SIZE
            
            # Only draw visible grid lines (optimization)
            for x in range(int(cam_x) % grid_spacing - grid_spacing, self.panel_width + grid_spacing, grid_spacing):
                pygame.draw.line(panel, grid_color, (x, 0), (x, self.panel_height))
            for y in range(int(cam_y) % grid_spacing - grid_spacing, self.panel_height + grid_spacing, grid_spacing):
                pygame.draw.line(panel, grid_color, (0, y), (y, self.panel_height))
        
        # Draw maze tiles with culling optimization
        for row in range(self.maze_height):
            for col in range(self.maze_width):
                # Calculate tile position within viewport
                x = col * TILE_SIZE - cam_x
                y = row * TILE_SIZE - cam_y
                
                # Skip tiles outside visible area (major optimization)
                tile_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                if not visible_rect.colliderect(tile_rect):
                    continue
                
                # Draw appropriate tile
                if self.maze[row, col] == 1:  # Wall
                    if hasattr(self.theme, 'enhanced_wall_tile'):
                        panel.blit(self.theme.enhanced_wall_tile, (x, y))
                    else:
                        panel.blit(self.theme.wall_tile, (x, y))
                elif self.maze[row, col] == 2:  # Start
                    panel.blit(self.theme.start_tile, (x, y))
                elif self.maze[row, col] == 3:  # Goal/Finish
                    # Draw the goal tile
                    panel.blit(self.theme.goal_tile, (x, y))
        
        # Draw player
        player_x = self.player_pos[1] * TILE_SIZE - cam_x
        player_y = self.player_pos[0] * TILE_SIZE - cam_y
        
        # Add player glow effect
        glow_size = TILE_SIZE * 1.5
        glow_surface = pygame.Surface((int(glow_size), int(glow_size)), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*NEON_GREEN[:3], 50), 
                        (int(glow_size/2), int(glow_size/2)), int(glow_size/2))
        panel.blit(glow_surface, (player_x - (glow_size-TILE_SIZE)/2, player_y - (glow_size-TILE_SIZE)/2))
        
        # Draw player sprite
        panel.blit(self.theme.player_sprite, (player_x, player_y))
        
        return panel
    
    def draw_stats(self, x, y):
        """Draw game statistics with enhanced visual styling."""
        # Panel dimensions
        panel_width = 250
        panel_height = self.panel_height
        
        # Draw panel background with semi-transparency
        stats_panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        stats_panel.fill((20, 20, 30, 230))  # Dark blue with transparency
        
        # Draw panel border
        pygame.draw.rect(stats_panel, NEON_BLUE, (0, 0, panel_width, panel_height), 2)
        
        # Add header
        header_height = 40
        pygame.draw.rect(stats_panel, (40, 40, 60), (2, 2, panel_width-4, header_height))
        header_text = self.theme.medium_font.render("GAME STATISTICS", True, NEON_YELLOW)
        stats_panel.blit(header_text, 
                       (panel_width//2 - header_text.get_width()//2, 
                        header_height//2 - header_text.get_height()//2))
        
        # Add horizontal separator
        pygame.draw.line(stats_panel, NEON_BLUE, (15, header_height + 10), 
                       (panel_width - 15, header_height + 10), 1)
        
        # Group stats into categories
        categories = [
            {
                "name": "PLAYER",
                "color": NEON_GREEN,
                "stats": [
                    ("Moves", str(self.player_tracker.total_moves)),
                    ("Backtracks", str(self.player_tracker.backtracks))
                ]
            },
            {
                "name": "LEVEL",
                "color": NEON_CYAN,
                "stats": [
                    ("Current", str(self.game.current_level)),
                    ("Difficulty", str(self.game.difficulty))  # Changed from f"{self.game.difficulty:.1f}"
                ]
            },
            {
                "name": "TIME",
                "color": NEON_PURPLE,
                "stats": [
                    ("Elapsed", f"{time.time() - self.start_time:.1f}s")
                ]
            }
        ]
        
        # Position for first category
        category_y = header_height + 25
        
        # Draw each category
        for category in categories:
            # Category header
            cat_header = self.theme.small_font.render(category["name"], True, category["color"])
            stats_panel.blit(cat_header, (20, category_y))
            
            # Draw stats in this category
            stat_y = category_y + 25
            for label, value in category["stats"]:
                # Label on left (dimmed color)
                label_text = self.theme.small_font.render(label + ":", True, LIGHT_GRAY)
                stats_panel.blit(label_text, (30, stat_y))
                
                # Value on right (bright color)
                value_text = self.theme.medium_font.render(value, True, category["color"])
                stats_panel.blit(value_text, 
                               (panel_width - 30 - value_text.get_width(), stat_y))
                
                stat_y += 30
            
            # Add space between categories
            category_y = stat_y + 20
        
        # Draw score (special highlight at bottom)
        score_y = panel_height - 80
        pygame.draw.rect(stats_panel, (40, 40, 60), (2, score_y, panel_width-4, 60))
        
        score_label = self.theme.medium_font.render("SCORE", True, NEON_YELLOW)
        stats_panel.blit(score_label, 
                       (panel_width//2 - score_label.get_width()//2, score_y + 5))
        
        # Calculate score based on moves, backtracks and time
        score = max(0, 1000 - 
                  self.player_tracker.total_moves * 5 - 
                  self.player_tracker.backtracks * 20)
        
        score_text = self.theme.large_font.render(str(score), True, NEON_GREEN)
        stats_panel.blit(score_text, 
                       (panel_width//2 - score_text.get_width()//2, score_y + 30))
        
        # Blit the entire stats panel to the screen
        self.screen.blit(stats_panel, (x, y))
    
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
        # Stop the background music before returning to main menu
        pygame.mixer.music.stop()
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

class PlayerVsBotGame(SinglePlayerGame):
    """Player vs Bot race game mode."""
    
    def __init__(self, screen, player_id="Player1"):
        # Call the parent class constructor which will initialize everything including the music
        super().__init__(screen, player_id)
        self.state = STATE_PLAYER_VS_BOT
        self.bot_reached_goal = False
        
        # Initialize player and AI game instances
        self.player_game = AdaptiveMazeGame(player_id)
        self.ai_game = AdaptiveMazeGame(player_id + "_AI")
        
        # Set individual panel size for split view
        self.max_panel_size = 800
        # These will be recalculated in load_new_level
        self.player_panel_width = 400  # Default value before loading level
        self.player_panel_height = 400  # Default value before loading level
        self.bot_panel_width = 400
        self.bot_panel_height = 400
        
        # Load level and start AI timer
        self.load_new_level()
        pygame.time.set_timer(AI_UPDATE_EVENT, AI_UPDATE_INTERVAL)
    
    
    def load_new_level(self):
        """Generate new level with both player and bot."""
        # Generate maze using parent method first
        super().load_new_level()
        
        # Load tile images directly
        try:
            self.wall_tile = pygame.transform.scale(pygame.image.load("assets/wall.jpeg"), (TILE_SIZE, TILE_SIZE))
            self.exit_tile = pygame.transform.scale(pygame.image.load("assets/finish.png"), (TILE_SIZE, TILE_SIZE))
            self.player_sprite = pygame.transform.scale(pygame.image.load("assets/player.png"), (TILE_SIZE, TILE_SIZE))
            self.start_tile = pygame.transform.scale(pygame.image.load("assets/start.png"), (TILE_SIZE, TILE_SIZE))
            self.bot_sprite = pygame.transform.scale(pygame.image.load("assets/bot.png"), (TILE_SIZE, TILE_SIZE))
            
            # Update theme with loaded images
            self.theme.wall_tile = self.wall_tile
            self.theme.goal_tile = self.exit_tile
            self.theme.player_sprite = self.player_sprite
            self.theme.start_tile = self.start_tile
            self.theme.bot_sprite = self.bot_sprite
        except pygame.error as e:
            print(f"Warning: Could not load images from assets directory: {e}")
            # The theme's fallback tiles will be used
        
        # Set individual panel sizes
        self.player_panel_width = min(self.max_panel_size, self.maze_pixel_width)
        self.player_panel_height = min(self.max_panel_size, self.maze_pixel_height)
        self.bot_panel_width = self.player_panel_width
        self.bot_panel_height = self.player_panel_height
        
        # Bot starts at the same position as player
        self.bot_pos = self.player_pos.copy()
        
        # Path tracking for bot
        self.bot_path = [tuple(self.bot_pos.astype(int))]
        
        # Bot stats
        self.bot_moves = 0
        self.bot_backtracks = 0
        
        # Calculate bot's path using A*
        self.bot_next_moves = self.calculate_bot_path()
        self.bot_move_timer = time.time()
    
    def calculate_player_camera(self):
        """Calculate camera position to follow player."""
        # Center camera on player
        cam_x = self.player_pos[1] * TILE_SIZE - self.player_panel_width // 2
        cam_y = self.player_pos[0] * TILE_SIZE - self.player_panel_height // 2
        
        # Clamp camera to maze boundaries
        max_cam_x = max(0, self.maze_pixel_width - self.player_panel_width)
        max_cam_y = max(0, self.maze_pixel_height - self.player_panel_height)
        
        return (max(0, min(cam_x, max_cam_x)), 
                max(0, min(cam_y, max_cam_y)))
    
    def calculate_bot_camera(self):
        """Calculate camera position for AI view."""
        # Center camera on bot
        cam_x = self.bot_pos[1] * TILE_SIZE - self.bot_panel_width // 2
        cam_y = self.bot_pos[0] * TILE_SIZE - self.bot_panel_height // 2
        
        # Clamp camera to maze boundaries
        max_cam_x = max(0, self.maze_pixel_width - self.bot_panel_width)
        max_cam_y = max(0, self.maze_pixel_height - self.bot_panel_height)
        
        return (max(0, min(cam_x, max_cam_x)), 
                max(0, min(cam_y, max_cam_y)))
    
    def _draw_panel_border(self, x, y, width, height, color):
        """Draw an enhanced border around a panel."""
        border_width = 2
        glow_alpha = 100
        
        # Main border
        pygame.draw.rect(self.screen, color, (x-border_width, y-border_width, 
                                           width+border_width*2, height+border_width*2), 
                        border_width)
        
        # Inner highlight
        highlight = pygame.Surface((width+border_width, height+border_width), pygame.SRCALPHA)
        r, g, b = color
        pygame.draw.rect(highlight, (r, g, b, glow_alpha), 
                        (0, 0, width+border_width, height+border_width), 1)
        self.screen.blit(highlight, (x-border_width//2, y-border_width//2))
        
        # Corner accents
        corner_size = 10
        for corner in [(x, y), (x+width-corner_size, y), 
                     (x, y+height-corner_size), (x+width-corner_size, y+height-corner_size)]:
            pygame.draw.rect(self.screen, color, 
                           (corner[0], corner[1], corner_size, corner_size), 1)
    
    def draw_game(self):
        """Draw the cyberpunk-styled game screen for player vs bot mode with side-by-side mazes."""
        # Fill background with darker color
        self.screen.fill((3, 5, 10))
        
        # Draw stars in background first
        self.draw_stars()
        
        # Update star animation
        self.update_stars()
        
        # Calculate camera positions for player and bot
        player_cam_x, player_cam_y = self.calculate_player_camera()
        bot_cam_x, bot_cam_y = self.calculate_bot_camera()
        
        # Calculate panel positions - arrange side by side with spacing
        panel_spacing = 20
        total_width = self.player_panel_width + self.bot_panel_width + panel_spacing
        
        # Center the combined panels horizontally
        start_x = (self.width - total_width) // 2
        
        # Position individual panels
        player_panel_x = start_x
        bot_panel_x = start_x + self.player_panel_width + panel_spacing
        
        # Calculate the available vertical space
        available_height = self.height - 40  # 20px margin at top and bottom
        
        # If stats panel below, allocate space for it
        stats_height = 150
        panel_y_with_stats = (available_height - self.player_panel_height - stats_height - 20) // 2
        
        # If not enough space for stats below, position panels centered vertically
        panel_y = max(20, panel_y_with_stats) 
        
        # Create player panel with same styling as SinglePlayerGame
        player_panel = self._create_maze_panel(
            self.player_panel_width, 
            self.player_panel_height, 
            player_cam_x, 
            player_cam_y, 
            is_player=True
        )
        
        # Create bot panel with similar styling
        bot_panel = self._create_maze_panel(
            self.bot_panel_width, 
            self.bot_panel_height, 
            bot_cam_x, 
            bot_cam_y, 
            is_player=False
        )
        
        # Blit panels to screen
        self.screen.blit(player_panel, (player_panel_x, panel_y))
        self.screen.blit(bot_panel, (bot_panel_x, panel_y))
        
        # Draw panel borders with enhanced styling
        self._draw_panel_border(player_panel_x, panel_y, self.player_panel_width, 
                              self.player_panel_height, NEON_GREEN)
        self._draw_panel_border(bot_panel_x, panel_y, self.bot_panel_width, 
                              self.bot_panel_height, NEON_PURPLE)
        
        # Check if there's enough space for stats panel below
        if panel_y + self.player_panel_height + stats_height + 20 <= self.height - 20:
            # Draw stats panel at the bottom
            stats_width = total_width
            stats_x = start_x
            stats_y = panel_y + self.player_panel_height + 20
        else:
            # Draw stats panel to the right
            stats_width = min(300, self.width - (bot_panel_x + self.bot_panel_width) - 40)
            stats_x = bot_panel_x + self.bot_panel_width + 20
            stats_y = panel_y
        
        # Draw the stats panel
        self.draw_vs_stats(stats_x, stats_y, stats_width, stats_height)
        
        # Draw winner announcement if game is over
        if hasattr(self, 'game_over') and hasattr(self, 'current_winner') and self.game_over and self.current_winner:
            self.draw_winner_announcement()
    
    def draw_vs_stats(self, x, y, width, height):
        """Draw the enhanced stats panel for player vs bot mode with improved styling."""
        # Create stats panel with semi-transparency
        stats_panel = pygame.Surface((width, height), pygame.SRCALPHA)
        stats_panel.fill((20, 20, 30, 230))  # Dark blue with transparency
        
        # Draw panel border with multiple layers
        pygame.draw.rect(stats_panel, NEON_BLUE, (0, 0, width, height), 2)  # Outer border
        pygame.draw.rect(stats_panel, (40, 40, 60), (2, 2, width-4, height-4), 1)  # Inner border
        
        # Add header with more defined border
        header_height = 40
        pygame.draw.rect(stats_panel, (40, 40, 60), (2, 2, width-4, header_height))
        pygame.draw.line(stats_panel, NEON_BLUE, (2, header_height+2), (width-2, header_height+2), 2)
        header_text = self.theme.medium_font.render("RACE STATISTICS", True, NEON_YELLOW)
        stats_panel.blit(header_text, 
                       (width//2 - header_text.get_width()//2, 
                        header_height//2 - header_text.get_height()//2))
        
        # Add horizontal separator with glow effect
        pygame.draw.line(stats_panel, NEON_BLUE, (15, header_height + 10), 
                       (width - 15, header_height + 10), 1)
        pygame.draw.line(stats_panel, (100, 150, 255, 100), (15, header_height + 11), 
                       (width - 15, header_height + 11), 1)
        
        # Side-by-side comparison
        player_color = NEON_GREEN
        bot_color = NEON_PURPLE
        
        # Calculate columns for comparison
        left_col = width // 4
        right_col = width * 3 // 4
        
        # Position for first category
        category_y = header_height + 25
        
        # Categories for comparison - fixed reference to player_game instead of game
        categories = [
            {
                "name": "PLAYER VS AI",
                "color": NEON_CYAN,
                "stats": [
                    ("Moves", str(self.player_tracker.total_moves), str(self.bot_moves)),
                    ("Backtracks", str(self.player_tracker.backtracks), str(self.bot_backtracks))
                ]
            },
            {
                "name": "LEVEL",
                "color": NEON_BLUE,
                "stats": [
                    ("Current", str(self.player_game.current_level)),
                    ("Difficulty", str(self.player_game.difficulty))
                ]
            },
            {
                "name": "TIME",
                "color": NEON_PURPLE,
                "stats": [
                    ("Elapsed", f"{time.time() - self.start_time:.1f}s")
                ]
            }
        ]
        
        # Draw each category
        for category in categories:
            # Category header with subtle border
            cat_header = self.theme.small_font.render(category["name"], True, category["color"])
            stats_panel.blit(cat_header, (20, category_y))
            
            # Draw stats in this category
            stat_y = category_y + 25
            
            if "PLAYER VS AI" in category["name"]:
                # Special formatting for comparison stats
                for label, player_val, bot_val in category["stats"]:
                    # Label on left (dimmed color)
                    label_text = self.theme.small_font.render(label + ":", True, LIGHT_GRAY)
                    stats_panel.blit(label_text, (30, stat_y))
                    
                    # Draw player value (left side)
                    p_val_text = self.theme.medium_font.render(player_val, True, player_color)
                    stats_panel.blit(p_val_text, (left_col - p_val_text.get_width()//2, stat_y))
                    
                    # Draw bot value (right side)
                    b_val_text = self.theme.medium_font.render(bot_val, True, bot_color)
                    stats_panel.blit(b_val_text, (right_col - b_val_text.get_width()//2, stat_y))
                    
                    stat_y += 30
            else:
                # Standard formatting for other categories
                for label, value in category["stats"]:
                    # Label on left (dimmed color)
                    label_text = self.theme.small_font.render(label + ":", True, LIGHT_GRAY)
                    stats_panel.blit(label_text, (30, stat_y))
                    
                    # Value on right (bright color)
                    value_text = self.theme.medium_font.render(value, True, category["color"])
                    stats_panel.blit(value_text, 
                                   (width - 30 - value_text.get_width(), stat_y))
                    
                    stat_y += 30
            
            # Add space between categories
            category_y = stat_y + 20
        
        # Race status box with enhanced border and layering
        status_y = height - 80
        # Background layer
        pygame.draw.rect(stats_panel, (30, 30, 50, 200), (2, status_y, width-4, 60))
        # Main box
        pygame.draw.rect(stats_panel, (40, 40, 60), (2, status_y, width-4, 60))
        # Border layers
        pygame.draw.rect(stats_panel, NEON_BLUE, (0, status_y-2, width, 64), 2)
        pygame.draw.line(stats_panel, (100, 150, 255, 100), (2, status_y), (width-2, status_y), 1)
        
        status_label = self.theme.medium_font.render("RACE STATUS", True, NEON_YELLOW)
        stats_panel.blit(status_label, 
                       (width//2 - status_label.get_width()//2, status_y + 5))
        
        # Calculate race status
        player_distance = self._distance_to_goal(self.player_pos)
        bot_distance = self._distance_to_goal(self.bot_pos)
        
        if player_distance < bot_distance:
            status_text = "PLAYER LEADING"
            status_color = player_color
        elif bot_distance < player_distance:
            status_text = "AI LEADING"
            status_color = bot_color
        else:
            status_text = "NECK AND NECK"
            status_color = NEON_YELLOW
        
        status_text_surf = self.theme.large_font.render(status_text, True, status_color)
        stats_panel.blit(status_text_surf, 
                       (width//2 - status_text_surf.get_width()//2, status_y + 30))
        
        # Blit the entire stats panel to the screen
        self.screen.blit(stats_panel, (x, y))
    
    def _distance_to_goal(self, position):
        """Calculate Manhattan distance from position to the goal."""
        goal_pos = np.argwhere(self.maze == 3)[0]
        return abs(position[0] - goal_pos[0]) + abs(position[1] - goal_pos[1])
    
    def draw_winner_announcement(self):
        """Draw an announcement when the race has a winner."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Dark overlay with transparency
        self.screen.blit(overlay, (0, 0))
        
        # Create winner announcement
        winner_color = NEON_GREEN if self.current_winner == "PLAYER" else NEON_PURPLE
        winner_text = f"{self.current_winner} WINS!"
        
        # Use larger font with glow effect for winner text
        announcement = self.theme.get_glowing_text(winner_text, 48, winner_color)
        
        # Create instruction text with smaller font
        instruction = self.theme.get_glowing_text("Press SPACE to continue", 24, NEON_CYAN)
        
        # Draw texts centered on screen
        self.screen.blit(announcement, 
                      ((self.width - announcement.get_width()) // 2, 
                       (self.height - announcement.get_height()) // 2 - 40))
        
        self.screen.blit(instruction, 
                      ((self.width - instruction.get_width()) // 2, 
                       (self.height - instruction.get_height()) // 2 + 40))
    
    def show_game_completion(self):
        """Show game completion screen with appropriate winning/losing video."""
        # Stop background music
        pygame.mixer.music.stop()
        
        # Determine the overall winner based on total wins
        if self.player_wins > self.ai_wins:
            final_winner = "PLAYER"
        else:
            final_winner = "AI"
        
        # Play appropriate ending video based on who won overall
        self.show_end_game_video(final_winner)

    def show_end_game_video(self, winner):
        """Show the winning or losing video based on who won the game."""
        # Determine which video and audio to play based on winner
        if winner == "PLAYER":
            video_path = os.path.join('assets', 'video', 'Winning Screen.mp4')  # Updated filename
            audio_path = os.path.join('assets', 'sound', 'Winning Screen.mp3')  # Updated filename
        else:
            video_path = os.path.join('assets', 'video', 'Losing Screen.mp4')
            audio_path = os.path.join('assets', 'sound', 'Losing Screen.mp3')
        
        # Check if files exist
        video_exists = os.path.exists(video_path)
        audio_exists = os.path.exists(audio_path)
        
        print(f"Video path: {video_path}, exists: {video_exists}")
        print(f"Audio path: {audio_path}, exists: {audio_exists}")
        
        if not video_exists:
            print("Warning: Video file not found. Returning to main menu.")
            self.return_to_main_menu()
            return
        
        try:
            # Initialize pygame mixer
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            # Import MoviePy here to avoid circular imports
            from moviepy import VideoFileClip
            
            # Load the video without audio (we'll handle audio separately)
            end_video = VideoFileClip(video_path, audio=False)
            
            # Store the video duration
            video_duration = end_video.duration
            
            # Play the audio if it exists
            if audio_exists:
                try:
                    pygame.mixer.music.load(audio_path)
                    pygame.mixer.music.set_volume(1.0)
                    pygame.mixer.music.play(0)  # Play once, not looping
                    print("Audio playback started")
                except Exception as e:
                    print(f"Error playing audio: {e}")
            
            # Record when we started playing
            start_time = pygame.time.get_ticks()
            playing = True
            
            # Play the video
            while playing and self.running:
                # Calculate elapsed time
                elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
                
                # Check if video is complete
                if elapsed >= video_duration:
                    playing = False
                    break
                    
                # Get the current frame
                try:
                    frame = end_video.get_frame(elapsed)
                    frame_surface = pygame.image.frombuffer(
                        frame.tobytes(), frame.shape[1::-1], "RGB")
                    
                    # Scale video to fit screen if needed
                    if frame_surface.get_size() != (self.width, self.height):
                        frame_surface = pygame.transform.scale(frame_surface, (self.width, self.height))
                    
                    # Draw the video frame
                    self.screen.fill((0, 0, 0))  # Clear screen
                    self.screen.blit(frame_surface, (0, 0))
                    pygame.display.flip()
                except Exception as e:
                    print(f"Error rendering frame: {e}")
                    playing = False
                    break
                
                # Handle events during playback
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        playing = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                            playing = False
                            break
                
                # Maintain framerate
                self.clock.tick(FPS)
            
            # Clean up video resources
            end_video.close()
            
        except Exception as e:
            print(f"Error playing ending video: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Stop any playing audio
            pygame.mixer.music.stop()
            
            # Return to main menu
            self.return_to_main_menu()
