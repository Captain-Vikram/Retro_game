import pygame
import os
import random
from utils.config import *
from utils.helpers import load_font, create_glowing_text

class RetroTheme:
    """Defines the retro-futuristic visual style for the game."""
    
    def __init__(self):
        """Initialize the retro theme with fonts and visual elements."""
        pygame.init()
        
        # Initialize fonts
        self.init_fonts()
        
        # Initialize default images path
        self.image_dir = os.path.join(IMAGE_DIR, "game")
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
        
        # Load or create visual elements
        self.init_visual_elements()
        
        # Load background image for maze (but don't resize yet - will be done when maze dimensions are known)
        self.original_background = self.load_image("bg.png", fallback="bg.webp")
        self.background_image = self.original_background  # Will be scaled properly when prepare_background is called
        
        # Load player and bot sprites
        self.player_image = self.load_image("player_icon.png", fallback="player.png")
        self.player_sprite = self._prepare_player_sprite(self.player_image)
        
        self.bot_image = self.load_image("bot_icon.png", fallback="bot.png")
        self.bot_sprite = self._prepare_bot_sprite(self.bot_image)
        
        # Load tile images
        self.wall_image = self.load_image("wall.png", fallback="wall.webp")
        self.wall_tile = self._prepare_wall_tile(self.wall_image)
        
        self.path_tile = self.load_image("path.png", create_fallback=self._create_path_tile)
        self.start_tile = self.load_image("start.png", create_fallback=self._create_start_tile)
        self.goal_tile = self.load_image("finish.png", create_fallback=self._create_goal_tile)
        
        # Create enhanced wall with glow effect
        self.enhanced_wall_tile = self.create_enhanced_wall_tile()
    
    def prepare_background(self, width, height):
        """Scale the background image to match the exact size of the maze.
        
        Args:
            width (int): The width of the maze in pixels
            height (int): The height of the maze in pixels
        """
        if self.original_background:
            # Scale the background to fit the maze exactly
            self.background_image = pygame.transform.scale(self.original_background, (width, height))
            return self.background_image
        return None
    
    def load_image(self, filename, fallback=None, create_fallback=None):
        """Load an image with fallback options."""
        try:
            # Try primary filename
            path = os.path.join(self.image_dir, filename)
            if os.path.exists(path):
                return pygame.image.load(path).convert_alpha()
            
            # Try fallback filename if provided
            if fallback:
                fallback_path = os.path.join(self.image_dir, fallback)
                if os.path.exists(fallback_path):
                    return pygame.image.load(fallback_path).convert_alpha()
            
            # If no image found, use the fallback creation function
            if create_fallback:
                print(f"Image {filename} not found, using generated fallback")
                return create_fallback()
            
            print(f"Warning: Image {filename} not found and no fallback provided")
            return pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
        except Exception as e:
            print(f"Error loading image {filename}: {e}")
            if create_fallback:
                return create_fallback()
            return pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    
    def load_ui_image(self, filename, desired_size=None, fallback=None, create_fallback=None):
        """Load a UI image with proper sizing and fallback options.
        
        Args:
            filename (str): The name of the image file to load
            desired_size (tuple): Optional (width, height) to scale the image to
            fallback (str): Optional fallback filename to try if the primary isn't found
            create_fallback (callable): Function to create a fallback surface if image loading fails
            
        Returns:
            pygame.Surface: The loaded and potentially scaled image
        """
        # UI images should be in the UI subdirectory
        ui_dir = os.path.join(IMAGE_DIR, "ui")
        
        try:
            # Try primary filename
            path = os.path.join(ui_dir, filename)
            if os.path.exists(path):
                image = pygame.image.load(path).convert_alpha()
            # Try fallback filename if provided
            elif fallback:
                fallback_path = os.path.join(ui_dir, fallback)
                if os.path.exists(fallback_path):
                    image = pygame.image.load(fallback_path).convert_alpha()
            # If no image found, use the fallback creation function
            elif create_fallback:
                print(f"UI image {filename} not found, using generated fallback")
                image = create_fallback()
            else:
                print(f"Warning: UI image {filename} not found and no fallback provided")
                # For UI elements, use a larger default size than tiles
                image = pygame.Surface((300, 60), pygame.SRCALPHA)
                
            # Scale the image if a size is specified
            if desired_size and (image.get_width() != desired_size[0] or 
                                 image.get_height() != desired_size[1]):
                image = pygame.transform.scale(image, desired_size)
                
            return image
            
        except Exception as e:
            print(f"Error loading UI image {filename}: {e}")
            if create_fallback:
                image = create_fallback()
                if desired_size:
                    image = pygame.transform.scale(image, desired_size)
                return image
            
            # Return a default surface with the desired size or a reasonable default
            size = desired_size if desired_size else (300, 60)
            return pygame.Surface(size, pygame.SRCALPHA)
    
    def scale_image(self, image, size):
        """Scale an image to the specified size while preserving aspect ratio.
        
        Args:
            image (pygame.Surface): The image to scale
            size (tuple): The (width, height) to scale to. If either is None,
                         it will be calculated to preserve aspect ratio.
        
        Returns:
            pygame.Surface: The scaled image
        """
        if not image:
            return None
            
        orig_width, orig_height = image.get_size()
        target_width, target_height = size
        
        # If either dimension is None, calculate it to preserve aspect ratio
        if target_width is None and target_height is not None:
            scale_factor = target_height / orig_height
            target_width = int(orig_width * scale_factor)
        elif target_height is None and target_width is not None:
            scale_factor = target_width / orig_width
            target_height = int(orig_height * scale_factor)
        
        # Scale the image
        return pygame.transform.scale(image, (target_width, target_height))
    
    def init_fonts(self):
        """Load custom fonts for different UI elements with appropriate fallbacks."""
        # Font preferences with fallbacks
        title_fonts = ["PressStart2P-Regular.ttf"]
        ui_fonts = ["VT323-Regular.ttf"]
        dialog_fonts = ["Audiowide-Regular.ttf"]
        
        # Initialize font paths
        self.title_font_path = None
        self.ui_font_path = None
        self.dialog_font_path = None
        
        try:
            # Get available font files in the fonts directory
            available_fonts = [f.lower() for f in os.listdir(FONT_DIR) if f.endswith('.ttf')]
            
            # Find the best matching fonts from preferences
            for font in title_fonts:
                if font.lower() in available_fonts:
                    self.title_font_path = os.path.join(FONT_DIR, font)
                    break
                    
            for font in ui_fonts:
                if font.lower() in available_fonts:
                    self.ui_font_path = os.path.join(FONT_DIR, font)
                    break
                    
            for font in dialog_fonts:
                if font.lower() in available_fonts:
                    self.dialog_font_path = os.path.join(FONT_DIR, font)
                    break
            
            # Fall back to any available font if specific ones weren't found
            if not self.title_font_path and available_fonts:
                self.title_font_path = os.path.join(FONT_DIR, available_fonts[0])
                
            # Use title font as fallback for UI if needed
            if not self.ui_font_path:
                self.ui_font_path = self.title_font_path
                
            # Use UI font as fallback for dialog if needed
            if not self.dialog_font_path:
                self.dialog_font_path = self.ui_font_path
                
        except (FileNotFoundError, OSError):
            # Fallback to system fonts if directory doesn't exist
            print("Font directory not found, using system fonts")
        
        # Create font objects in various sizes
        # Title fonts (bold, eye-catching for main menu and titles)
        self.title_font = self._create_font(self.title_font_path, 64)
        self.subtitle_font = self._create_font(self.title_font_path, 48)
        
        # UI fonts (clear and readable for HUD and in-game elements)
        self.large_font = self._create_font(self.ui_font_path, 36)
        self.medium_font = self._create_font(self.ui_font_path, 28)
        self.small_font = self._create_font(self.ui_font_path, 18)
        
        # Dialog fonts (smooth and futuristic for pause menu and dialogs)
        self.dialog_large_font = self._create_font(self.dialog_font_path, 42)
        self.dialog_medium_font = self._create_font(self.dialog_font_path, 32)
        self.dialog_small_font = self._create_font(self.dialog_font_path, 24)
    
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
        
        # Use a darker interior color for better contrast
        tile.fill((15, 25, 35))  # Darkened for better visibility
        
        # Draw borders with increased thickness
        thickness = 3  # Increased from 2
        pygame.draw.rect(tile, WALL_COLOR, (0, 0, TILE_SIZE, TILE_SIZE), thickness)
        
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
    
    def _prepare_player_sprite(self, image=None):
        """Prepare player sprite using image if available, otherwise create a default."""
        # Check if we have a valid image
        if image and isinstance(image, pygame.Surface) and image.get_width() > 1:
            # Create a new surface with alpha channel
            sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Scale image to fit within the tile with some padding
            padding = TILE_SIZE // 6  # Use 1/6 of tile size as padding
            img_size = TILE_SIZE - (padding * 2)
            
            # Scale the image to fit
            scaled_img = pygame.transform.scale(image, (img_size, img_size))
            
            # Center the image on the tile
            sprite.blit(scaled_img, (padding, padding))
            
            # Add a subtle glow effect around the player
            glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            glow_color = (*PLAYER_COLOR, 60)  # Semi-transparent player color
            pygame.draw.circle(glow, glow_color, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2 - 2)
            
            # Apply the glow underneath the player image
            temp = sprite.copy()
            sprite.blit(glow, (0, 0))
            sprite.blit(temp, (0, 0))
            
            return sprite
        else:
            # Fall back to the default sprite
            return self._create_player_sprite()
    
    def _prepare_bot_sprite(self, image=None):
        """Prepare bot sprite using image if available, otherwise create a default."""
        # Check if we have a valid image
        if image and isinstance(image, pygame.Surface) and image.get_width() > 1:
            # Create a new surface with alpha channel
            sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Scale image to fit within the tile with some padding
            padding = TILE_SIZE // 6  # Use 1/6 of tile size as padding
            img_size = TILE_SIZE - (padding * 2)
            
            # Scale the image to fit
            scaled_img = pygame.transform.scale(image, (img_size, img_size))
            
            # Center the image on the tile
            sprite.blit(scaled_img, (padding, padding))
            
            # Add a subtle glow effect around the bot
            glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            glow_color = (*BOT_COLOR, 60)  # Semi-transparent bot color
            pygame.draw.circle(glow, glow_color, (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2 - 2)
            
            # Apply the glow underneath the bot image
            temp = sprite.copy()
            sprite.blit(glow, (0, 0))
            sprite.blit(temp, (0, 0))
            
            return sprite
        else:
            # Fall back to the default sprite
            return self._create_bot_sprite()
    
    def _prepare_wall_tile(self, image=None):
        """Prepare wall tile using image if available, otherwise create a default."""
        # Check if we have a valid image
        if image and isinstance(image, pygame.Surface) and image.get_width() > 1:
            # Create a new surface with alpha channel
            tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Scale image to exactly fit the tile size
            scaled_img = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            
            # Apply the image without any glow effects
            tile.blit(scaled_img, (0, 0))
            
            # Add a stronger border to ensure the wall is visible
            pygame.draw.rect(tile, WALL_COLOR, (0, 0, TILE_SIZE, TILE_SIZE), 2)
            
            return tile
        else:
            # Create a more visible default wall
            return self._create_wall_tile()
    
    def _prepare_start_tile(self, image=None):
        """Prepare start tile using image if available, otherwise create a default."""
        if image and isinstance(image, pygame.Surface) and image.get_width() > 1:
            tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            scaled_img = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            tile.blit(scaled_img, (0, 0))
            return tile
        else:
            return self._create_start_tile()
    
    def _prepare_goal_tile(self, image=None):
        """Prepare goal tile using image if available, otherwise create a default."""
        if image and isinstance(image, pygame.Surface) and image.get_width() > 1:
            tile = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            scaled_img = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            tile.blit(scaled_img, (0, 0))
            return tile
        else:
            return self._create_goal_tile()
    
    def get_glowing_text(self, text, size, color, glow_radius=0, font_type="ui"):
        """Create text with optional outline for better visibility."""
        # Select appropriate font path based on type
        if font_type == "title":
            font_path = self.title_font_path
        elif font_type == "dialog":
            font_path = self.dialog_font_path
        else:  # "ui" is default
            font_path = self.ui_font_path
            
        font = pygame.font.Font(font_path, size)
        
        # Simple direct rendering without glow
        text_surface = font.render(text, True, color)
        
        # If an outline is requested (using glow_radius as outline thickness)
        if glow_radius > 0:
            # Create a slightly larger surface for the outline
            outline_surface = pygame.Surface(
                (text_surface.get_width() + glow_radius * 2, 
                 text_surface.get_height() + glow_radius * 2),
                pygame.SRCALPHA
            )
            
            # Choose a dark outline color for visibility
            outline_color = (0, 0, 0)
            
            # Render outline text (just once in each direction)
            outline = font.render(text, True, outline_color)
            
            # Draw the outline positions
            for x_offset in [-1, 0, 1]:
                for y_offset in [-1, 0, 1]:
                    if x_offset != 0 or y_offset != 0:  # Skip the center position
                        outline_surface.blit(
                            outline, 
                            (glow_radius + x_offset, glow_radius + y_offset)
                        )
            
            # Draw the main text on top
            outline_surface.blit(text_surface, (glow_radius, glow_radius))
            return outline_surface
        
        # If no outline is needed, just return the text surface
        return text_surface
    
    def create_default_wall_tile(self):
        """Create a default wall tile if image file is missing"""
        texture = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Draw cyberpunk-style neon border
        inner_color = (20, 30, 40)  # Dark blue interior
        border_color = NEON_BLUE
        
        # Fill with inner color
        texture.fill(inner_color)
        
        # Draw glowing neon border
        border_width = 2
        pygame.draw.rect(texture, border_color, (0, 0, TILE_SIZE, TILE_SIZE), border_width)
        
        # Add circuit pattern
        line_color = (border_color[0], border_color[1], border_color[2], 100)
        
        # Horizontal lines
        for y in range(5, TILE_SIZE, 10):
            start_x = random.randint(5, 15)
            end_x = random.randint(25, 35)
            pygame.draw.line(texture, line_color, (start_x, y), (end_x, y), 1)
        
        # Vertical lines
        for x in range(5, TILE_SIZE, 10):
            start_y = random.randint(5, 15)
            end_y = random.randint(25, 35)
            pygame.draw.line(texture, line_color, (x, start_y), (x, end_y), 1)
        
        return texture
    
    def create_enhanced_wall_tile(self):
        """Create a slightly enhanced wall tile for special cases."""
        if hasattr(self, 'wall_tile') and self.wall_tile:  # Fixed: changed 'wall' to 'wall_tile'
            # Just return the regular wall tile without extra glow
            return self.wall_tile.copy()
        else:
            return self.create_default_wall_tile()