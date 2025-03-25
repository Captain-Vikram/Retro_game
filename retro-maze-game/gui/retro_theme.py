import pygame
import os
from utils.config import *
from utils.helpers import load_font, create_glowing_text

class RetroTheme:
    """Defines the retro-futuristic visual style for the game."""
    
    def __init__(self):
        """Initialize the retro theme with fonts and visual elements."""
        pygame.init()
        
        # Initialize fonts
        self.init_fonts()
        
        # Load or create visual elements
        self.init_visual_elements()
    
    def init_fonts(self):
        """Load custom fonts or fall back to system fonts."""
        # Try to load custom fonts from assets folder
        try:
            # Look for .ttf files in the fonts directory
            font_files = [f for f in os.listdir(FONT_DIR) if f.endswith('.ttf')]
            
            if font_files:
                self.title_font_path = os.path.join(FONT_DIR, font_files[0])
                self.text_font_path = os.path.join(FONT_DIR, font_files[-1] if len(font_files) > 1 else font_files[0])
            else:
                # Fallback to system fonts
                self.title_font_path = None
                self.text_font_path = None
        except (FileNotFoundError, OSError):
            # Fallback to system fonts if directory doesn't exist
            self.title_font_path = None
            self.text_font_path = None
        
        # Create font objects in various sizes
        self.title_font = self._create_font(self.title_font_path, 64)
        self.subtitle_font = self._create_font(self.title_font_path, 48)
        self.large_font = self._create_font(self.text_font_path, 36)
        self.medium_font = self._create_font(self.text_font_path, 28)
        self.small_font = self._create_font(self.text_font_path, 18)
    
    def _create_font(self, font_path, size):
        """Create a font object from the given path and size."""
        if font_path and os.path.exists(font_path):
            try:
                return pygame.font.Font(font_path, size)
            except pygame.error:
                pass
        
        # Fallback options
        try:
            return pygame.font.SysFont("Arial", size)
        except:
            return pygame.font.Font(None, size)
    
    def init_visual_elements(self):
        """Initialize visual elements like backgrounds, tiles, etc."""
        # Create a grid pattern background
        self.background = self._create_grid_background(32, DARK_GRAY, BLACK)
        
        # Create tile surfaces
        self.wall_tile = self._create_wall_tile()
        self.path_tile = self._create_path_tile()
        self.start_tile = self._create_start_tile()
        self.goal_tile = self._create_goal_tile()
        self.player_sprite = self._create_player_sprite()
        self.bot_sprite = self._create_bot_sprite()
    
    def _create_grid_background(self, grid_size, line_color, bg_color):
        """Create a grid pattern background."""
        # Create a surface with the grid pattern
        bg = pygame.Surface((800, 800))
        bg.fill(bg_color)
        
        # Draw vertical and horizontal grid lines
        for i in range(0, 800, grid_size):
            pygame.draw.line(bg, line_color, (i, 0), (i, 800), 1)
            pygame.draw.line(bg, line_color, (0, i), (800, i), 1)
        
        return bg
    
    def _create_wall_tile(self):
        """Create a neon wall tile."""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile.fill(BLACK)
        
        # Draw neon edges
        thickness = 3
        pygame.draw.rect(tile, WALL_COLOR, (0, 0, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(tile, BLACK, (thickness, thickness, 
                                     TILE_SIZE - 2*thickness, 
                                     TILE_SIZE - 2*thickness))
        
        # Add a subtle glow
        glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*WALL_COLOR, 100), (0, 0, TILE_SIZE, TILE_SIZE), border_radius=5)
        tile.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        return tile
    
    def _create_path_tile(self):
        """Create a path tile."""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile.fill(PATH_COLOR)
        return tile
    
    def _create_start_tile(self):
        """Create a start position tile."""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile.fill(BLACK)
        
        # Draw "S" in the center
        text = self.medium_font.render("S", True, START_COLOR)
        x = (TILE_SIZE - text.get_width()) // 2
        y = (TILE_SIZE - text.get_height()) // 2
        tile.blit(text, (x, y))
        
        # Add glow effect
        glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*START_COLOR, 100), (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2)
        tile.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        return tile
    
    def _create_goal_tile(self):
        """Create a goal position tile."""
        tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        tile.fill(BLACK)
        
        # Draw "G" in the center
        text = self.medium_font.render("G", True, GOAL_COLOR)
        x = (TILE_SIZE - text.get_width()) // 2
        y = (TILE_SIZE - text.get_height()) // 2
        tile.blit(text, (x, y))
        
        # Add glow effect
        glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*GOAL_COLOR, 100), (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2)
        tile.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        return tile
    
    def _create_player_sprite(self):
        """Create player sprite."""
        sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Draw a glowing circle
        radius = TILE_SIZE // 2 - 4
        pygame.draw.circle(sprite, PLAYER_COLOR, (TILE_SIZE//2, TILE_SIZE//2), radius)
        
        # Add inner highlight
        pygame.draw.circle(sprite, WHITE, (TILE_SIZE//2 - 2, TILE_SIZE//2 - 2), radius//3)
        
        return sprite
    
    def _create_bot_sprite(self):
        """Create bot sprite."""
        sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Draw a glowing diamond shape
        points = [
            (TILE_SIZE//2, 4),                    # Top
            (TILE_SIZE - 4, TILE_SIZE//2),        # Right
            (TILE_SIZE//2, TILE_SIZE - 4),        # Bottom
            (4, TILE_SIZE//2)                     # Left
        ]
        pygame.draw.polygon(sprite, BOT_COLOR, points)
        
        # Add inner highlight
        inner_points = [
            (TILE_SIZE//2, 12),
            (TILE_SIZE - 12, TILE_SIZE//2),
            (TILE_SIZE//2, TILE_SIZE - 12),
            (12, TILE_SIZE//2)
        ]
        pygame.draw.polygon(sprite, (*BOT_COLOR, 200), inner_points)
        
        return sprite
    
    def get_glowing_text(self, text, size, color=NEON_GREEN, glow_color=None):
        """Get text with a neon glow effect."""
        if glow_color is None:
            glow_color = color
        
        # Choose appropriate font based on size
        if size >= 48:
            font = self.title_font
        elif size >= 36:
            font = self.subtitle_font
        elif size >= 24:
            font = self.large_font
        elif size >= 16:
            font = self.medium_font
        else:
            font = self.small_font
        
        # Create text with glow
        text_surface = create_glowing_text(text, font, color, glow_color)
        
        return text_surface