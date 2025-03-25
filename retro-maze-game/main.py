import pygame
from gui.main_menu import MainMenu

def main():
    pygame.init()
    # Set up full-screen game window
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Retro-Futuristic Maze Game")
    
    # Load and run the main menu
    main_menu = MainMenu(screen)
    main_menu.run()
    
    pygame.quit()

if __name__ == "__main__":
    main()