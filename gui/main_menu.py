import pygame
import sys
import os
from utils.config import *
from utils.helpers import create_neon_button, center_rect
from gui.retro_theme import RetroTheme
from logic.singleplayer import PlayerTracker
from logic.player_vs_bot import PlayerVsBotGame
from moviepy import VideoFileClip
import math
import random

class MainMenu:
    """Main menu screen for the retro-futuristic maze game."""
    
    def __init__(self, screen):
        """Initialize the main menu."""
        self.screen = screen
        self.running = True
        self.clock = pygame.time.Clock()
        
        # Get screen dimensions
        self.width, self.height = self.screen.get_size()
        
        # Load retro theme
        self.theme = RetroTheme()
        
        # Load button assets
        self.load_button_assets()
        
        # Load sound assets
        self.load_sound_assets()
        
        # Load background video
        self.load_background_video()
        
        # Create buttons
        self.create_buttons()
    
    def load_button_assets(self):
        """Load button background images."""
        try:
            # Define paths for button images
            button_path = None
            button_hover_path = None
            
            if os.path.exists(button_path) and os.path.exists(button_hover_path):
                self.button_normal = pygame.image.load(button_path).convert_alpha()
                self.button_hover = pygame.image.load(button_hover_path).convert_alpha()
            else:
                print(f"Button images not found at {button_path} or {button_hover_path}")
                # Create fallback button images
                self.button_normal = self._create_fallback_button((20, 20, 30, 220))
                self.button_hover = self._create_fallback_button((40, 40, 50, 240))
        except Exception as e:
            print(f"Error loading button assets: {e}")
            # Create fallback button images
            self.button_normal = self._create_fallback_button((20, 20, 30, 220))
            self.button_hover = self._create_fallback_button((40, 40, 50, 240))

    def load_sound_assets(self):
        """Load sound effect assets."""
        try:
            sound_path = os.path.join('assets', 'sound', 'button.mp3')
            if os.path.exists(sound_path):
                self.button_sound = pygame.mixer.Sound(sound_path)
                self.button_sound.set_volume(0.5)  # Set to 50% volume
            else:
                print(f"Button sound not found at {sound_path}")
                self.button_sound = None
        except Exception as e:
            print(f"Error loading button sound: {e}")
            self.button_sound = None

    def _create_fallback_button(self, color):
        """Create a fallback button image if asset loading fails."""
        button_w, button_h = 300, 60
        button_surf = pygame.Surface((button_w, button_h), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, color, (0, 0, button_w, button_h), border_radius=10)
        pygame.draw.rect(button_surf, NEON_GREEN, (0, 0, button_w, button_h), width=2, border_radius=10)
        return button_surf

    def load_background_video(self):
        """Load the background video with audio."""
        video_path = 'assets/video/Entry Scene Main Menu.mp4'
        audio_path = 'assets/sound/Entry Scene Main Menu.mp3'  # Extract audio if needed
        
        # First check if the file exists
        if not os.path.exists(video_path):
            print(f"Video file not found at: {video_path}")
            print(f"Current working directory: {os.getcwd()}")
            self.video = None
            return
        
        try:
            # Initialize pygame mixer first with settings that work well with video
            pygame.mixer.quit()  # Reset mixer if it was initialized before
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            # Load the video without audio (we'll handle audio separately)
            self.video = VideoFileClip(video_path, audio=False)
            
            # Store the video duration for proper looping
            self.video_duration = self.video.duration
            
            # Extract audio if needed and play with pygame mixer
            if not os.path.exists(audio_path) and hasattr(self.video, 'audio') and self.video.audio:
                print("Extracting audio from video...")
                self.video.audio.write_audiofile(audio_path)
                print(f"Audio extracted to {audio_path}")
            
            # Now play the audio file if it exists
            if os.path.exists(audio_path):
                print(f"Loading audio from {audio_path}")
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.set_volume(1.0)  # Full volume
                pygame.mixer.music.play(-1)  # Loop indefinitely
                print("Audio playback started")
            else:
                print(f"No audio file found at {audio_path}")
            
            # Start the video playback
            self.video_started_at = pygame.time.get_ticks()
            
            # Create a surface for the video
            self.video_surface = pygame.Surface((self.width, self.height))
            
            print("Video loaded successfully!")
        except Exception as e:
            print(f"Error loading video: {e}")
            import traceback
            traceback.print_exc()  # Print full error details
            self.video = None
    
    def create_buttons(self):
        """Create main menu buttons."""
        button_width = 300
        button_height = 60
        button_spacing = 20
        
        # Calculate position for centering buttons
        start_y = self.height // 2 - 50
        
        # Start Game button
        self.start_game_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               start_y, 
                               button_width, 
                               button_height),
            'text': 'Start the Game',
            'action': self.show_game_modes
        }
        
        # Credits button
        self.credits_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               start_y + button_height + button_spacing, 
                               button_width, 
                               button_height),
            'text': 'Credits',
            'action': self.show_credits
        }
        
        # Quit button
        self.quit_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               start_y + 2 * (button_height + button_spacing), 
                               button_width, 
                               button_height),
            'text': 'Quit',
            'action': self.quit_game
        }
        
        self.buttons = [self.start_game_btn, self.credits_btn, self.quit_btn]
        # Set menu state to main
        self.current_menu = "main"

    def show_game_modes(self):
        """Show the game mode selection screen with Started.mp4 as background."""
        # First load the game modes menu
        self.load_game_modes_menu()
        
        # Then load Started.mp4 as the background with its audio
        self.load_game_modes_background()

    def load_game_modes_background(self):
        """Load the Started.mp4 video as background for game modes screen."""
        video_path = 'assets/video/Started.mp4'
        audio_path = 'assets/sound/Started.mp3'
        
        # First check if the file exists
        if not os.path.exists(video_path):
            print(f"Game modes video file not found at: {video_path}")
            return
        
        try:
            # Initialize pygame mixer
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            # Load the video without audio (we'll handle audio separately)
            self.modes_video = VideoFileClip(video_path, audio=False)
            
            # Store the video duration for proper looping
            self.modes_video_duration = self.modes_video.duration
            
            # Extract audio if needed
            if not os.path.exists(audio_path) and hasattr(self.modes_video, 'audio') and self.modes_video.audio:
                print("Extracting audio from game modes video...")
                self.modes_video.audio.write_audiofile(audio_path)
                print(f"Audio extracted to {audio_path}")
            
            # Play the audio if it exists
            if os.path.exists(audio_path):
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play(-1)  # Loop indefinitely
            
            # Start the video playback
            self.modes_video_started_at = pygame.time.get_ticks()
            
            print("Game modes video loaded successfully!")
        except Exception as e:
            print(f"Error loading game modes video: {e}")
            import traceback
            traceback.print_exc()
            self.modes_video = None

    def load_game_modes_menu(self):
        """Show the game modes selection menu."""
        # Create game mode selection buttons
        button_width = 300
        button_height = 60
        button_spacing = 20
        
        # Calculate position for centering buttons
        start_y = self.height // 2 - 50
        
        # Single Player button
        self.single_player_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               start_y, 
                               button_width, 
                               button_height),
            'text': 'Single Player Mode',
            'action': self.start_single_player
        }
        
        # Player vs Bot button
        self.player_vs_bot_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               start_y + button_height + button_spacing, 
                               button_width, 
                               button_height),
            'text': 'Race Against AI',
            'action': self.start_player_vs_bot
        }
        
        # Back button to return to main menu
        self.back_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               start_y + 2 * (button_height + button_spacing), 
                               button_width, 
                               button_height),
            'text': 'Back',
            'action': self.return_to_main_menu
        }
        
        # Update buttons and set menu state
        self.buttons = [self.single_player_btn, self.player_vs_bot_btn, self.back_btn]
        self.current_menu = "game_modes"

    def show_credits(self):
        """Show the credits screen."""
        self.current_menu = "credits"
        # Create back button for credits screen
        button_width = 200
        button_height = 50
        
        self.back_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               self.height - 100, 
                               button_width, 
                               button_height),
            'text': 'Back',
            'action': self.return_to_main_menu
        }
        
        self.buttons = [self.back_btn]

    def return_to_main_menu(self):
        """Return to the main menu from other screens."""
        self.create_buttons()  # Reset to main menu buttons
        self.reload_background_audio()  # Switch back to main menu audio

    def draw(self):
        """Draw the current menu screen with enhanced retro styling."""
        # Fill screen with black first (as fallback)
        self.screen.fill(BLACK)
        
        # Draw appropriate video background based on current menu
        if self.current_menu == "game_modes" and hasattr(self, 'modes_video') and self.modes_video:
            try:
                # Get elapsed time in seconds for game modes video
                elapsed = (pygame.time.get_ticks() - self.modes_video_started_at) / 1000.0
                
                # Calculate the current time position in the video (for manual looping)
                current_time = elapsed % self.modes_video_duration
                
                # Get the current frame and convert to a pygame surface
                frame = self.modes_video.get_frame(current_time)
                frame_surface = pygame.image.frombuffer(
                    frame.tobytes(), frame.shape[1::-1], "RGB")
                
                # Scale video to fit screen if needed
                if frame_surface.get_size() != (self.width, self.height):
                    frame_surface = pygame.transform.scale(frame_surface, (self.width, self.height))
                
                # Draw the video frame
                self.screen.blit(frame_surface, (0, 0))
            except Exception as e:
                # Fallback to grid background pattern
                self._draw_grid_background()
        elif hasattr(self, 'video') and self.video:
            try:
                # Main menu video logic (existing code)
                elapsed = (pygame.time.get_ticks() - self.video_started_at) / 1000.0
                current_time = elapsed % self.video_duration
                frame = self.video.get_frame(current_time)
                frame_surface = pygame.image.frombuffer(
                    frame.tobytes(), frame.shape[1::-1], "RGB")
                if frame_surface.get_size() != (self.width, self.height):
                    frame_surface = pygame.transform.scale(frame_surface, (self.width, self.height))
                self.screen.blit(frame_surface, (0, 0))
            except Exception as e:
                self._draw_grid_background()
        else:
            # Fallback if no video
            self._draw_grid_background()
        
        # Draw menu-specific content
        if self.current_menu == "main":
            # Draw title text
            title_text = self.theme.get_glowing_text("RETRO MAZE", 72, NEON_CYAN, font_type="title")
            subtitle_text = self.theme.get_glowing_text("A FUTURISTIC ADVENTURE", 32, NEON_PINK, font_type="ui")
            
            # Position and draw title
            title_x = (self.width - title_text.get_width()) // 2
            self.screen.blit(title_text, (title_x, 100))
            
            # Position and draw subtitle
            subtitle_x = (self.width - subtitle_text.get_width()) // 2
            self.screen.blit(subtitle_text, (subtitle_x, 180))
        
        elif self.current_menu == "game_modes":
            # Draw title for game modes
            title_text = self.theme.get_glowing_text("SELECT GAME MODE", 64, NEON_CYAN, font_type="title")
            title_x = (self.width - title_text.get_width()) // 2
            self.screen.blit(title_text, (title_x, 100))
        
        elif self.current_menu == "credits":
            # Draw credits content
            self._draw_credits()
        
        # Draw buttons last to ensure they appear on top
        self._draw_enhanced_buttons()

    def _draw_grid_background(self):
        """Draw a retro grid background."""
        # Create grid pattern
        grid_size = 40
        grid_color = (0, 20, 40, 50)  # Dark blue, semi-transparent
        
        # Draw horizontal grid lines
        for y in range(0, self.height, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y))
        
        # Draw vertical grid lines
        for x in range(0, self.width, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height))
        
        # Add some random "stars"
        for _ in range(100):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            alpha = random.randint(50, 200)
            color = (255, 255, 255, alpha)
            pygame.draw.circle(self.screen, color, (x, y), size)

    def _apply_scan_lines(self):
        """Apply a scan lines effect."""
        scan_line_height = 4
        scan_line_color = (0, 0, 0, 30)  # Black with 30% opacity
        
        for y in range(0, self.height, scan_line_height):
            # Create a transparent surface for the scan line
            scan_surface = pygame.Surface((self.width, scan_line_height//2), pygame.SRCALPHA)
            scan_surface.fill(scan_line_color)
            self.screen.blit(scan_surface, (0, y))

    def _apply_crt_flicker(self):
        """Apply a subtle CRT flicker effect."""
        # Add subtle screen flicker
        if random.random() < 0.03:  # 3% chance of flicker per frame
            flicker_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flicker_surface.fill((0, 0, 0, random.randint(5, 15)))  # Slightly dark with randomized alpha
            self.screen.blit(flicker_surface, (0, 0))

    def _draw_enhanced_buttons(self):
        """Draw buttons with a pop-out hover effect using the same button image."""
        for button in self.buttons:
            # Check if the mouse is hovering over the button
            hover = button['rect'].collidepoint(pygame.mouse.get_pos())
            
            # Choose the button background and scaling factor
            button_bg = self.button_normal
            scale = 1.1 if hover else 1.0  # Slightly larger when hovered
            
            # Scale the button background to match the button rect
            scaled_width = int(button['rect'].width * scale)
            scaled_height = int(button['rect'].height * scale)
            scaled_bg = pygame.transform.scale(button_bg, (scaled_width, scaled_height))
            
            # Render button text
            text_color = NEON_YELLOW if hover else NEON_GREEN
            text_surf = self.theme.large_font.render(button['text'], True, text_color)
            
            # Center text on the button
            text_x = (scaled_width - text_surf.get_width()) // 2
            text_y = (scaled_height - text_surf.get_height()) // 2
            
            # Create the final button by combining background and text
            button_surf = scaled_bg.copy()
            button_surf.blit(text_surf, (text_x, text_y))
            
            # Calculate position to keep the button centered after scaling
            pos_x = button['rect'].x - (scaled_width - button['rect'].width) // 2
            pos_y = button['rect'].y - (scaled_height - button['rect'].height) // 2
            
            # Draw the button
            self.screen.blit(button_surf, (pos_x, pos_y))

    def _draw_credits(self):
        """Draw the credits screen content."""
        credits_title = self.theme.get_glowing_text("CREDITS", 64, NEON_PURPLE, font_type="title")
        
        # Credits content
        credits = [
            ("Game Design & Development", NEON_CYAN),
            ("Your Name", WHITE),
            ("", WHITE),
            ("Artwork & Audio", NEON_CYAN),
            ("Your Artist", WHITE),
            ("", WHITE),
            ("Special Thanks", NEON_CYAN),
            ("GitHub Copilot", WHITE)
        ]
        
        # Draw title
        title_x = (self.width - credits_title.get_width()) // 2
        self.screen.blit(credits_title, (title_x, 100))
        
        # Draw credits content
        y_pos = 200
        for text, color in credits:
            if text:
                credit_text = self.theme.medium_font.render(text, True, color)
                text_x = (self.width - credit_text.get_width()) // 2
                self.screen.blit(credit_text, (text_x, y_pos))
            y_pos += 40

    def handle_events(self):
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_game()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check button clicks
                    for button in self.buttons:
                        if button['rect'].collidepoint(event.pos):
                            # Play button click sound
                            if hasattr(self, 'button_sound') and self.button_sound:
                                self.button_sound.play()
                            button['action']()

    def start_single_player(self):
        """Launch the single player game mode directly without transition video."""
        # Stop any currently playing music before launching the game
        pygame.mixer.music.stop()
        
        # Launch the game directly without transition video
        from gui.game_ui import SinglePlayerGame
        game = SinglePlayerGame(self.screen)
        game.run()
        
        # Reload main menu audio when returning from game
        self.reload_background_audio()

    def start_player_vs_bot(self):
        """Launch the player vs bot game mode after transition video."""
        def launch_game():
            # Stop any currently playing music before launching the game
            pygame.mixer.music.stop()
            
            game = PlayerVsBotGame(self.screen)
            game.run()
            
            # Reload main menu audio when returning from game
            self.reload_background_audio()
        
        self.play_transition_video(launch_game)
    
    def quit_game(self):
        """Exit the game."""
        self.running = False
        
        # Clean up video resources
        if hasattr(self, 'video') and self.video:
            self.video.close()
            
        pygame.quit()
        sys.exit()
    
    def run(self):
        """Main menu loop."""
        last_loop_point = 0
        
        # Reload background audio when returning to main menu
        self.reload_background_audio()
        
        while self.running:
            self.handle_events()
            
            # Check for video loop point to restart audio
            if hasattr(self, 'video') and self.video and hasattr(self, 'video_duration'):
                elapsed = (pygame.time.get_ticks() - self.video_started_at) / 1000.0
                current_loop = int(elapsed / self.video_duration)
                
                # If we've crossed a loop boundary, restart audio to keep in sync with video
                if current_loop > last_loop_point:
                    last_loop_point = current_loop
                    # Restart audio to maintain sync
                    pygame.mixer.music.stop()
                    pygame.mixer.music.play(-1)
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
    
    def reload_background_audio(self):
        """Reload the main menu background audio."""
        audio_path = 'assets/sound/Entry Scene Main Menu.mp3'
        
        if os.path.exists(audio_path):
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.set_volume(1.0)  # Full volume
                pygame.mixer.music.play(-1)  # Loop indefinitely
                print("Main menu audio reloaded and restarted")
            except Exception as e:
                print(f"Error reloading background audio: {e}")

    def play_transition_video(self, next_action):
        """Play a transition video and then execute the provided action."""
        video_path = 'assets/video/Press Start 2P.mp4'
        audio_path = 'assets/sound/Press Start 2P.mp3'
        
        # First check if the file exists
        if not os.path.exists(video_path):
            print(f"Transition video file not found at: {video_path}")
            next_action()
            return
        
        try:
            # Initialize pygame mixer
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            # Load the video without audio (we'll handle audio separately)
            transition_video = VideoFileClip(video_path, audio=False)
            
            # Store the video duration
            video_duration = transition_video.duration
            
            # Extract audio if needed
            if not os.path.exists(audio_path) and hasattr(transition_video, 'audio') and transition_video.audio:
                print("Extracting audio from transition video...")
                transition_video.audio.write_audiofile(audio_path)
                print(f"Audio extracted to {audio_path}")
            
            # Play the audio if it exists
            if os.path.exists(audio_path):
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play(0)  # Play once, not looping
            
            # Record when we started playing
            start_time = pygame.time.get_ticks()
            playing = True
            
            # Play the transition video
            while playing:
                # Calculate elapsed time
                elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
                
                # Check if video is complete
                if elapsed >= video_duration:
                    playing = False
                    break
                    
                # Get the current frame
                frame = transition_video.get_frame(elapsed)
                frame_surface = pygame.image.frombuffer(
                    frame.tobytes(), frame.shape[1::-1], "RGB")
                
                # Scale video to fit screen if needed
                if frame_surface.get_size() != (self.width, self.height):
                    frame_surface = pygame.transform.scale(frame_surface, (self.width, self.height))
                
                # Draw the video frame
                self.screen.fill(BLACK)  # Clear screen
                self.screen.blit(frame_surface, (0, 0))
                pygame.display.flip()
                
                # Handle quit events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.quit_game()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            playing = False
                
                self.clock.tick(FPS)
            
            # Clean up video resources
            transition_video.close()
            
            # Start the game after video completes
            next_action()
            
        except Exception as e:
            print(f"Error playing transition video: {e}")
            import traceback
            traceback.print_exc()
            # Start the game anyway if video fails
            next_action()