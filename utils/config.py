import os
import pygame

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 0, 0  # Will be set to fullscreen dimensions
GAME_PANEL_SIZE = (800, 800)  # Max size of inner game panel

# Colors - Retro-futuristic neon palette
NEON_PINK = (255, 20, 147)
NEON_BLUE = (10, 230, 250)
NEON_GREEN = (57, 255, 20)
NEON_PURPLE = (180, 40, 240)
NEON_YELLOW = (255, 252, 64)
NEON_CYAN = (0, 255, 255)

BLACK = (0, 0, 0)
DARK_GRAY = (20, 20, 30)
LIGHT_GRAY = (150, 150, 150)
WHITE = (255, 255, 255)

# Game element colors
WALL_COLOR = NEON_BLUE
PATH_COLOR = DARK_GRAY
START_COLOR = NEON_GREEN
GOAL_COLOR = NEON_PINK
PLAYER_COLOR = NEON_YELLOW
BOT_COLOR = NEON_PURPLE

# Game constants
TILE_SIZE = 40
FPS = 120
AI_UPDATE_INTERVAL = 200  # milliseconds between AI moves
AI_UPDATE_EVENT = pygame.USEREVENT + 1
MAX_LEVELS = 5
AI_BACKTRACK_LIMIT = 10

# Asset paths
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
FONT_DIR = os.path.join(ASSET_DIR, "fonts")
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
SOUND_DIR = os.path.join(ASSET_DIR, "sounds")

# Default font paths (will use system fonts if custom ones aren't available)
MAIN_FONT = None
TITLE_FONT = None

# Game states
STATE_MAIN_MENU = "main_menu"
STATE_SINGLE_PLAYER = "single_player"
STATE_PLAYER_VS_BOT = "player_vs_bot"
STATE_PAUSE = "pause"
STATE_GAME_OVER = "game_over"