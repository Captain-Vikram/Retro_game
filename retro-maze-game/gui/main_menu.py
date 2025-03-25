import pygame
import sys
from utils.config import *
from utils.helpers import create_neon_button, center_rect
from gui.retro_theme import RetroTheme
from logic.singleplayer import PlayerTracker
from logic.player_vs_bot import PlayerVsBotGame

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
        
        # Create buttons
        self.create_buttons()
        
    def create_buttons(self):
        """Create menu buttons."""
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
            'text': 'Single Player',
            'action': self.start_single_player
        }
        
        # Player vs Bot button
        self.player_vs_bot_btn = {
            'rect': pygame.Rect((self.width - button_width) // 2, 
                               start_y + button_height + button_spacing, 
                               button_width, 
                               button_height),
            'text': 'Player vs Bot',
            'action': self.start_player_vs_bot
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
        
        self.buttons = [self.single_player_btn, self.player_vs_bot_btn, self.quit_btn]
    
    def draw(self):
        """Draw the main menu."""
        # Fill screen with black
        self.screen.fill(BLACK)
        
        # Tile background pattern
        for x in range(0, self.width, 800):
            for y in range(0, self.height, 800):
                self.screen.blit(self.theme.background, (x, y))
        
        # Draw title
        title_text = self.theme.get_glowing_text("RETRO MAZE", 72, NEON_CYAN)
        subtitle_text = self.theme.get_glowing_text("A FUTURISTIC ADVENTURE", 32, NEON_PINK)
        
        # Center and draw title
        title_x = (self.width - title_text.get_width()) // 2
        self.screen.blit(title_text, (title_x, 100))
        
        # Center and draw subtitle
        subtitle_x = (self.width - subtitle_text.get_width()) // 2
        self.screen.blit(subtitle_text, (subtitle_x, 180))
        
        # Draw buttons
        for button in self.buttons:
            # Create button surface with glow
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
                self.theme.large_font, 
                button['rect'].width, 
                button['rect'].height,
                text_color, 
                glow_color,
                bg_color
            )
            
            # Draw button
            self.screen.blit(button_surf, button['rect'])
    
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
                            button['action']()
    
    def start_single_player(self):
        """Launch the single player game mode."""
        from gui.game_ui import SinglePlayerGame
        game = SinglePlayerGame(self.screen)
        game.run()
    
    def start_player_vs_bot(self):
        """Launch the player vs bot game mode."""
        game = PlayerVsBotGame(self.screen)
        game.run()
    
    def quit_game(self):
        """Exit the game."""
        self.running = False
        pygame.quit()
        sys.exit()
    
    def run(self):
        """Main menu loop."""
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)