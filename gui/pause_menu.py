import pygame
import sys
import os
import math
import random
from utils.config import *
from utils.helpers import create_neon_button
from gui.retro_theme import RetroTheme

class PauseMenu:
    """Pause menu screen."""
    
    def __init__(self, screen, resume_callback, quit_callback):
        """Initialize the pause menu."""
        self.screen = screen
        self.resume_callback = resume_callback
        self.quit_callback = quit_callback
        self.width, self.height = screen.get_size()
        
        # Load theme
        self.theme = RetroTheme()
        
        # Load button assets
        self.load_button_assets()
        
        # Load sound assets
        self.load_sound_assets()
        
        # Create buttons
        self.create_buttons()
    
    def load_button_assets(self):
        """Load button background images."""
        try:
            # Create fallback button image - don't try to load from path
            self.button_normal = self._create_fallback_button((20, 20, 30, 220))
        except Exception as e:
            print(f"Error creating button assets: {e}")
            # Create a simple fallback button as last resort
            self.button_normal = self._create_fallback_button((20, 20, 30, 220))
    
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
            print(f"Error loading sound assets: {e}")
            self.button_sound = None
    
    def _create_fallback_button(self, color):
        """Create a fallback button image if asset loading fails."""
        button_w, button_h = 250, 50
        button_surf = pygame.Surface((button_w, button_h), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, color, (0, 0, button_w, button_h), border_radius=10)
        pygame.draw.rect(button_surf, NEON_GREEN, (0, 0, button_w, button_h), width=2, border_radius=10)
        return button_surf
    
    def create_buttons(self):
        """Create menu buttons."""
        button_width = 250
        button_height = 50
        button_spacing = 20
        
        # Calculate position for centering buttons
        start_y = self.height // 2 - 30
        
        # Resume button
        self.resume_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2,
                               start_y,
                               button_width,
                               button_height),
            'text': 'Resume',
            'action': self.resume_callback
        }
        
        # Quit button
        self.quit_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2,
                               start_y + button_height + button_spacing,
                               button_width,
                               button_height),
            'text': 'Quit to Menu',
            'action': self.quit_callback
        }
        
        self.buttons = [self.resume_btn, self.quit_btn]
    
    def draw(self):
        """Draw the pause menu overlay with stars background effect."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Draw retro grid pattern
        grid_size = 40
        grid_color = (0, 20, 40, 30)  # Dark blue, very subtle
        
        # Draw horizontal grid lines
        for y in range(0, self.height, grid_size):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y))
        
        # Draw vertical grid lines
        for x in range(0, self.width, grid_size):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height))
        
        # Add dynamic star field effect
        current_time = pygame.time.get_ticks() / 1000.0
        for i in range(150):  # More stars for a richer effect
            # Use deterministic positions but with good distribution
            x = (self.width * ((i * 13) % 100)) / 100
            y = (self.height * ((i * 17) % 100)) / 100
            
            # Add some drift based on time
            x += math.sin(current_time * 0.5 + i * 0.1) * 5
            y += math.cos(current_time * 0.3 + i * 0.2) * 5
            
            # Ensure stars stay on screen
            x = x % self.width
            y = y % self.height
            
            # Vary size based on position
            base_size = 1 + (i % 3)
            
            # Pulse effect - vary brightness over time
            pulse = 0.5 + 0.5 * math.sin(current_time * 2 + i * 0.3)
            
            # Different star colors for visual interest
            if i % 5 == 0:  # Blue-white stars
                color = (180 + 75 * pulse, 180 + 75 * pulse, 255)
                size = base_size * 1.2
            elif i % 7 == 0:  # Yellow stars
                color = (255, 255, 180 + 75 * pulse)
                size = base_size * 0.9
            elif i % 11 == 0:  # Pink-purple stars
                color = (255, 140 + 60 * pulse, 220 + 35 * pulse)
                size = base_size * 1.1
            else:  # White stars
                brightness = 150 + int(105 * pulse)
                color = (brightness, brightness, brightness)
                size = base_size
                
            # Draw the star with glow effect
            if size > 1.5:
                # Add soft glow for larger stars
                glow_size = size * 3
                glow_surf = pygame.Surface((int(glow_size*2), int(glow_size*2)), pygame.SRCALPHA)
                glow_color = (*color, 50)  # Semi-transparent color
                pygame.draw.circle(glow_surf, glow_color, (int(glow_size), int(glow_size)), int(glow_size))
                self.screen.blit(glow_surf, (int(x - glow_size), int(y - glow_size)))
            
            # Draw the star itself
            pygame.draw.circle(self.screen, color, (int(x), int(y)), size)
        
        # Draw enhanced paused text with stronger glow
        paused_text = self.theme.get_glowing_text("PAUSED", 64, NEON_PURPLE, glow_radius=3, font_type="title")
        text_x = (self.width - paused_text.get_width()) // 2
        
        # Add subtle text floating effect
        text_y = 150 + math.sin(current_time * 1.5) * 5
        
        # Draw extra glow behind text
        glow_surf = pygame.Surface((paused_text.get_width() + 20, paused_text.get_height() + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*NEON_PURPLE[:3], 30), 
                          (0, 0, paused_text.get_width() + 20, paused_text.get_height() + 20))
        self.screen.blit(glow_surf, (text_x - 10, text_y - 10))
        
        # Draw the text
        self.screen.blit(paused_text, (text_x, text_y))
        
        # Draw a subtle subtitle
        subtitle = self.theme.medium_font.render("Game is paused", True, (180, 180, 255))
        subtitle_x = (self.width - subtitle.get_width()) // 2
        self.screen.blit(subtitle, (subtitle_x, text_y + paused_text.get_height() + 10))
        
        # Draw buttons with enhanced pop-out effect
        for button in self.buttons:
            # Check if the mouse is hovering over the button
            hover = button['rect'].collidepoint(pygame.mouse.get_pos())
            
            # Choose the button background and scaling factor
            button_bg = self.button_normal
            scale = 1.15 if hover else 1.0  # More dramatic scaling when hovered
            
            # Scale the button background
            scaled_width = int(button['rect'].width * scale)
            scaled_height = int(button['rect'].height * scale)
            scaled_bg = pygame.transform.scale(button_bg, (scaled_width, scaled_height))
            
            # Render button text with glow effect for hover state
            if hover:
                text_color = NEON_YELLOW
                text_surf = self.theme.get_glowing_text(button['text'], 24, text_color, glow_radius=1)
            else:
                text_color = NEON_GREEN
                text_surf = self.theme.medium_font.render(button['text'], True, text_color)
            
            # Center text on the button
            text_x = (scaled_width - text_surf.get_width()) // 2
            text_y = (scaled_height - text_surf.get_height()) // 2
            
            # Create the final button by combining background and text
            button_surf = scaled_bg.copy()
            button_surf.blit(text_surf, (text_x, text_y))
            
            # Calculate position to keep the button centered after scaling
            pos_x = button['rect'].x - (scaled_width - button['rect'].width) // 2
            pos_y = button['rect'].y - (scaled_height - button['rect'].height) // 2
            
            # Draw soft glow behind button when hovered
            if hover:
                glow = pygame.Surface((scaled_width + 20, scaled_height + 20), pygame.SRCALPHA)
                glow_color = (*NEON_YELLOW[:3], 40)
                pygame.draw.rect(glow, glow_color, (0, 0, scaled_width + 20, scaled_height + 20), 
                               border_radius=15)
                self.screen.blit(glow, (pos_x - 10, pos_y - 10))
            
            # Draw the button
            self.screen.blit(button_surf, (pos_x, pos_y))
    
    def handle_events(self):
        """Handle pause menu input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.resume_callback()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Check button clicks
                    for button in self.buttons:
                        if button['rect'].collidepoint(event.pos):
                            # Play button click sound
                            if hasattr(self, 'button_sound') and self.button_sound:
                                self.button_sound.play()
                            button['action']()