import pygame
import sys
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
        
        # Create buttons
        self.create_buttons()
    
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
        """Draw the pause menu overlay."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        
        # Draw paused text
        paused_text = self.theme.get_glowing_text("PAUSED", 64, NEON_PURPLE)
        text_x = (self.width - paused_text.get_width()) // 2
        self.screen.blit(paused_text, (text_x, 150))
        
        # Draw buttons
        for button in self.buttons:
            # Check for hover state
            hover = button['rect'].collidepoint(pygame.mouse.get_pos())
            
            # Different colors based on hover state
            if hover:
                text_color = NEON_YELLOW
                glow_color = NEON_YELLOW
                bg_color = (40, 40, 50)
            else:
                text_color = NEON_GREEN
                glow_color = NEON_GREEN
                bg_color = (20, 20, 30)
            
            # Create button surface
            button_surf = create_neon_button(
                button['text'],
                self.theme.medium_font,
                button['rect'].width,
                button['rect'].height,
                text_color,
                glow_color,
                bg_color
            )
            
            # Draw button
            self.screen.blit(button_surf, button['rect'])
    
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
                            button['action']()