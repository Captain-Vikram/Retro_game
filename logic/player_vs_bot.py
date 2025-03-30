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
import math

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
        
        self.load_background_music()

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
        
        # Check if this was the final level
        if self.player_game.current_level > MAX_LEVELS:
            self.show_end_game_video(winner)
            return
        
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
    
    def show_end_game_video(self, winner):
        """Show the winning or losing video based on who won the game."""
        # Stop background music
        pygame.mixer.music.stop()
        
        # Determine which video and audio to play based on winner
        if winner == "PLAYER":
            video_path = os.path.join('assets', 'video', 'Winning Screen.mp4')
            audio_path = os.path.join('assets', 'sound', 'Winning Screen.mp3')
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
                    self.screen.fill(BLACK)  # Clear screen
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
            
            # Wait a moment for everything to finish
            pygame.time.delay(500)
            
            # Return to main menu
            self.return_to_main_menu()
    
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
        
        # Calculate panel positions (center horizontally with spacing between)
        panel_spacing = 20
        total_width = (self.panel_width * 2) + panel_spacing
        start_x = (self.width - total_width) // 2
        panel_y = (self.height - self.panel_height) // 2
        
        player_panel_x = start_x
        ai_panel_x = start_x + self.panel_width + panel_spacing
        
        # Set panel dimensions for reference in other methods
        self.player_panel_width = self.panel_width
        self.player_panel_height = self.panel_height
        self.bot_panel_width = self.panel_width
        self.bot_panel_height = self.panel_height
        
        # Create maze panels for both player and bot
        self._create_maze_panel(self.player_panel_width, self.player_panel_height, 
                               *self.calculate_player_camera(), is_player=True, x_pos=player_panel_x, y_pos=panel_y)
        
        self._create_maze_panel(self.bot_panel_width, self.bot_panel_height, 
                               *self.calculate_ai_camera(), is_player=False, x_pos=ai_panel_x, y_pos=panel_y)
        
        # Add glow effect to the finishing point in both panels
        for row in range(self.maze_height):
            for col in range(self.maze_width):
                if self.player_maze[row, col] == 3:  # 3 represents the finishing point
                    # Player panel glow
                    player_cam_x, player_cam_y = self.calculate_player_camera()
                    glow_radius = TILE_SIZE * 1.5
                    glow_surface = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
                    glow_color = (255, 255, 0, 100)  # Yellow glow with transparency
                    pygame.draw.circle(glow_surface, glow_color, (int(glow_radius), int(glow_radius)), int(glow_radius))
                    
                    # Calculate the position of the glow
                    glow_x = player_panel_x + col * TILE_SIZE - player_cam_x - glow_radius + TILE_SIZE // 2
                    glow_y = panel_y + row * TILE_SIZE - player_cam_y - glow_radius + TILE_SIZE // 2
                    
                    # Blit the glow effect onto the screen
                    self.screen.blit(glow_surface, (glow_x, glow_y))
                    
                    # AI panel glow
                    ai_cam_x, ai_cam_y = self.calculate_ai_camera()
                    glow_x = ai_panel_x + col * TILE_SIZE - ai_cam_x - glow_radius + TILE_SIZE // 2
                    glow_y = panel_y + row * TILE_SIZE - ai_cam_y - glow_radius + TILE_SIZE // 2
                    
                    # Blit the glow effect onto the screen
                    self.screen.blit(glow_surface, (glow_x, glow_y))
                    
        # Draw stats at new positions
        self.draw_stats(10, 10, width=230, height=400)  # Left side stats
        self.draw_stats(self.width - 240, 10, width=230, height=400)  # Right side stats
        
        # Draw winner announcement if game is over
        if self.game_over and self.current_winner:
            self.draw_winner_announcement()
    
    def _create_maze_panel(self, width, height, cam_x, cam_y, is_player, x_pos, y_pos):
        """Create and draw a maze panel (either player or AI)."""
        panel = pygame.Surface((width, height))
        panel.fill(BLACK)
        
        maze = self.player_maze if is_player else self.ai_maze
        path = self.player_path if is_player else self.ai_path
        
        # Draw maze tiles
        for row in range(self.maze_height):
            for col in range(self.maze_width):
                # Calculate tile position within panel
                x = col * TILE_SIZE - cam_x
                y = row * TILE_SIZE - cam_y
                
                # Skip tiles outside the panel
                if (x + TILE_SIZE <= 0 or x >= width or
                    y + TILE_SIZE <= 0 or y >= height):
                    continue
                
                # Draw appropriate tile
                if maze[row, col] == 1:  # Wall
                    panel.blit(self.theme.wall_tile, (x, y))
                elif maze[row, col] == 0:  # Path
                    panel.blit(self.theme.path_tile, (x, y))
                elif maze[row, col] == 2:  # Start
                    panel.blit(self.theme.start_tile, (x, y))
                elif maze[row, col] == 3:  # Goal
                    panel.blit(self.theme.goal_tile, (x, y))
        
        # Draw path
        if len(path) > 1:
            for i in range(1, len(path)):
                prev = (path[i-1][1]*TILE_SIZE - cam_x + TILE_SIZE//2, 
                       path[i-1][0]*TILE_SIZE - cam_y + TILE_SIZE//2)
                curr = (path[i][1]*TILE_SIZE - cam_x + TILE_SIZE//2, 
                       path[i][0]*TILE_SIZE - cam_y + TILE_SIZE//2)
                pygame.draw.line(panel, NEON_BLUE if is_player else NEON_PURPLE, prev, curr, 3)
        
        # Draw player/AI sprite
        if is_player:
            sprite_x = self.player_pos[1] * TILE_SIZE - cam_x
            sprite_y = self.player_pos[0] * TILE_SIZE - cam_y
            panel.blit(self.theme.player_sprite, (sprite_x, sprite_y))
        elif self.ai_bot and not self.ai_reached_goal:
            sprite_x = self.ai_bot.state[1] * TILE_SIZE - cam_x
            sprite_y = self.ai_bot.state[0] * TILE_SIZE - cam_y
            panel.blit(self.theme.bot_sprite, (sprite_x, sprite_y))
        
        # Draw panel label
        label_text = "PLAYER" if is_player else "AI"
        label_color = NEON_BLUE if is_player else NEON_PURPLE
        label = self.theme.get_glowing_text(label_text, 24, label_color)
        panel.blit(label, ((width - label.get_width()) // 2, 10))
        
        # Blit panel to screen and draw border
        self.screen.blit(panel, (x_pos, y_pos))
        pygame.draw.rect(self.screen, label_color, 
                        (x_pos-2, y_pos-2, width+4, height+4), 2)
    
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

    def draw_stats(self, x, y, width=230, height=400):
        """Draw enhanced game statistics with styled panel."""
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
        header_text = self.theme.medium_font.render("GAME STATISTICS", True, NEON_YELLOW)
        stats_panel.blit(header_text, 
                    (width//2 - header_text.get_width()//2, 
                        header_height//2 - header_text.get_height()//2))
        
        # Add horizontal separator with glow effect
        pygame.draw.line(stats_panel, NEON_BLUE, (15, header_height + 10), 
                    (width - 15, header_height + 10), 1)
        pygame.draw.line(stats_panel, (100, 150, 255, 100), (15, header_height + 11), 
                    (width - 15, header_height + 11), 1)
        
        # Prepare stats
        stats = [
            {"label": "LEVEL", "value": str(self.player_game.current_level), "color": NEON_CYAN},
            {"label": "TIME", "value": f"{time.time() - self.start_time:.1f}s", "color": NEON_PURPLE},
            {"label": "PLAYER MOVES", "value": str(self.player_tracker.total_moves), "color": NEON_GREEN},
            {"label": "AI MOVES", "value": str(self.ai_moves), "color": NEON_PURPLE},
            {"label": "PLAYER BACKTRACKS", "value": str(self.player_tracker.backtracks), "color": NEON_GREEN},
            {"label": "AI BACKTRACKS", "value": f"{self.ai_backtracks}/10", "color": NEON_PURPLE},
            {"label": "SCORE", "value": f"{self.player_wins} - {self.ai_wins}", "color": NEON_BLUE}
        ]
        
        # Draw stats
        category_y = header_height + 25
        for stat in stats:
            # Label on left (dimmed color)
            label_text = self.theme.small_font.render(stat["label"] + ":", True, LIGHT_GRAY)
            stats_panel.blit(label_text, (30, category_y))
            
            # Value on right (bright color)
            value_text = self.theme.medium_font.render(stat["value"], True, stat["color"])
            stats_panel.blit(value_text, 
                        (width - 30 - value_text.get_width(), category_y))
            
            category_y += 30
        
        # Conditional status messages
        status_y = height - 120
        
        # Player first move prompt
        if not self.player_made_first_move:
            pygame.draw.rect(stats_panel, (30, 30, 50, 200), (2, status_y, width-4, 60))
            pygame.draw.rect(stats_panel, (40, 40, 60), (2, status_y, width-4, 60))
            pygame.draw.rect(stats_panel, NEON_BLUE, (0, status_y-2, width, 64), 2)
            
            prompt_text = self.theme.medium_font.render("MOVE TO START RACE!", True, NEON_YELLOW)
            stats_panel.blit(prompt_text, 
                        (width//2 - prompt_text.get_width()//2, status_y + 20))
        
        # AI reset warning
        if self.ai_resetting:
            reset_y = status_y + 70 if not self.player_made_first_move else status_y
            pygame.draw.rect(stats_panel, (30, 30, 50, 200), (2, reset_y, width-4, 60))
            pygame.draw.rect(stats_panel, (40, 40, 60), (2, reset_y, width-4, 60))
            pygame.draw.rect(stats_panel, NEON_BLUE, (0, reset_y-2, width, 64), 2)
            
            reset_text = self.theme.medium_font.render("AI RESETTING...", True, NEON_PINK)
            stats_panel.blit(reset_text, 
                        (width//2 - reset_text.get_width()//2, reset_y + 20))
        
        # Blit the entire stats panel to the screen
        self.screen.blit(stats_panel, (x, y))
    
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
                    
                    # Check if this was the final level
                    if self.player_game.current_level >= MAX_LEVELS:
                        # Immediately play end game video without waiting for input
                        self.show_end_game_video(self.current_winner)
                        return
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
                    
                    # Check if this was the final level
                    if self.player_game.current_level >= MAX_LEVELS:
                        # Immediately play end game video without waiting for input
                        self.show_end_game_video(self.current_winner)
                        return
    
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