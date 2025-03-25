### Project Overview
You are tasked with creating a retro-futuristic maze game with the following features:

- **Main Menu**: Options to select between "Single Player" or "Player vs Bot" modes with a visually appealing retro-futuristic design.
- **Game Modes**:
  - **Single Player**: The player navigates the maze to reach the goal.
  - **Player vs Bot**: The player competes against an AI bot to reach the goal first.
- **Pause Menu**: Allows the player to pause the game and resume or quit.
- **UI Design**: Full-screen main window with an inner game panel (max size 800x800 pixels) centered on the screen, featuring retro-futuristic visual elements.

### Step-by-Step Generation Process

#### Step 1: File Structure
1. **Create the folder structure**:
   ```
   Maze/
   ├── gui/
   ├── logic/
   ├── utils/
   ├── assets/
   ├── main.py
   └── prompt.txt
   ```

2. **Create empty files for each component in the structure**:
   - `main.py`
   - `gui/main_menu.py`
   - `gui/game_ui.py`
   - `gui/pause_menu.py`
   - `gui/retro_theme.py`
   - `utils/config.py`
   - `utils/helpers.py`
   - `logic/adaptive_logic.py`
   - `logic/ai_logic.py`
   - `logic/maze_logic.py`
   - `logic/player_vs_bot.py`
   - `logic/singleplayer.py`

#### Step 2: Core Logic Integration
Attach the following files from your existing workspace to the `logic/` folder:
- `adaptivemaze.py` → `logic/adaptive_logic.py`
- `ai_bot_trainer_multicore.py` → `logic/ai_logic.py`
- `ai_gpu.py` → `logic/ai_logic.py`
- `mazegenerator.py` → `logic/maze_logic.py`
- `player_vs__bot.py` → `logic/player_vs_bot.py`
- `playertracker.py` → `logic/singleplayer.py`

These files will contain the core logic for maze generation, AI bot behavior, and adaptive difficulty.

#### Step 3: Main File (main.py)
The `main.py` file will:
- Initialize the game window in full-screen mode.
- Load the main menu.
- Handle transitions between the main menu, game modes, and pause menu.

#### Step 4: Main Menu (gui/main_menu.py)
The `main_menu.py` file will:
- Display options for "Single Player" and "Player vs Bot."
- Use retro-futuristic fonts and glowing buttons.
- Transition to the selected game mode when a button is clicked.

#### Step 5: Game UI (gui/game_ui.py)
The `game_ui.py` file will:
- Render the maze and player/bot positions.
- Display the inner game panel (800x800 pixels) centered on the screen.
- Use assets from the `assets` folder for retro-futuristic visuals.

#### Step 6: Pause Menu (gui/pause_menu.py)
The `pause_menu.py` file will:
- Allow the player to pause the game.
- Provide options to resume or quit.
- Use the retro-futuristic theme for consistency.

#### Step 7: Retro Theme (gui/retro_theme.py)
The `retro_theme.py` file will:
- Define colors, fonts, and styles for the retro-futuristic theme.
- Load assets (e.g., neon walls, glowing effects) from the `assets` folder.

#### Step 8: Utility Functions (utils/)
The `utils/` folder will contain:
- `config.py`: Define constants like screen size, colors, and font paths.
- `helpers.py`: Provide utility functions for loading assets and handling events.

#### Step 9: Assets
The `assets` folder will include:
- **Fonts**: Retro-futuristic fonts for UI text.
- **Images**: Neon walls, glowing player/bot sprites, and other visual elements.
- **Sounds**: Background music and sound effects for interactions.

#### Step 10: Testing and Polishing
- Test each game mode (Single Player and Player vs Bot) to ensure functionality.
- Adjust the retro-futuristic theme for visual appeal.
- Optimize performance for smooth animations and transitions.

### Conclusion
This structured approach will help you create a modular and maintainable retro-futuristic maze game. Each step focuses on a specific aspect of the game, ensuring clarity and organization throughout the development process.
