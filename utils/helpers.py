import os
import pygame
from utils.config import *

def load_font(font_name, size):
    """Load a font, first trying the custom fonts, then falling back to system fonts."""
    # Try loading from assets/fonts
    font_path = os.path.join(FONT_DIR, font_name)
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except pygame.error:
            pass
    
    # Fall back to system font
    try:
        return pygame.font.SysFont(font_name.split('.')[0], size)
    except:
        return pygame.font.SysFont(None, size)  # Default system font

def create_glowing_text(text, font, text_color, glow_color, glow_radius=2):
    """Create text with a neon glowing effect."""
    # Create the base text surface
    text_surface = font.render(text, True, text_color)
    
    # Create a larger surface for the glow effect
    padding = glow_radius * 2
    glow_surface = pygame.Surface((text_surface.get_width() + padding, 
                                  text_surface.get_height() + padding), 
                                  pygame.SRCALPHA)
    
    # Draw the text multiple times with slight offsets for the glow
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            # Skip the center (that's where the final text will go)
            if dx == 0 and dy == 0:
                continue
                
            # Calculate alpha based on distance from center
            distance = (dx**2 + dy**2) ** 0.5
            alpha = int(max(0, 255 * (1 - distance / glow_radius)))
            
            # Create a custom color with alpha
            color_with_alpha = (*glow_color, alpha)
            
            # Create the glow layer and blit it
            glow_layer = font.render(text, True, color_with_alpha)
            glow_surface.blit(glow_layer, (dx + glow_radius, dy + glow_radius))
    
    # Add the original text on top
    glow_surface.blit(text_surface, (glow_radius, glow_radius))
    
    return glow_surface

def create_neon_button(text, font, width, height, text_color, glow_color, bg_color=None):
    """Create a neon-styled button with glowing text."""
    # Create glowing text
    text_surf = create_glowing_text(text, font, text_color, glow_color)
    
    # Create button surface
    button_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Optional background
    if bg_color:
        pygame.draw.rect(button_surf, bg_color, (0, 0, width, height), border_radius=10)
        
    # Draw glowing border
    pygame.draw.rect(button_surf, glow_color, (0, 0, width, height), width=2, border_radius=10)
    
    # Center text on button
    text_x = (width - text_surf.get_width()) // 2
    text_y = (height - text_surf.get_height()) // 2
    button_surf.blit(text_surf, (text_x, text_y))
    
    return button_surf

def center_rect(surface_width, surface_height, rect_width, rect_height):
    """Calculate the centered rectangle coordinates."""
    x = (surface_width - rect_width) // 2
    y = (surface_height - rect_height) // 2
    return pygame.Rect(x, y, rect_width, rect_height)