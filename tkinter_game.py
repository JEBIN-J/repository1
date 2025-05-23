import tkinter as tk
import random

# --- Game Constants ---
# These values define the basic parameters of the game.
CANVAS_WIDTH = 800    # Width of the game canvas in pixels
CANVAS_HEIGHT = 600   # Height of the game canvas in pixels
PLAYER_WIDTH = 100    # Width of the player's catcher
PLAYER_HEIGHT = 20    # Height of the player's catcher
PLAYER_COLOR = "blue" # Color of the player's catcher
PLAYER_SPEED = 30     # Number of pixels the player moves per key press

OBJECT_SIZE = 25      # Diameter of the falling objects (circles)
OBJECT_COLOR = "red"  # Color of the falling objects
OBJECT_SPEED = 5      # Pixels an object falls per game loop iteration
SPAWN_INTERVAL = 1500 # Time in milliseconds between new object spawns (e.g., 1.5 seconds)

# --- Game State Variables ---
# These variables track the current status of the game.
score = 0
misses = 0
miss_limit = 5          # Max number of misses before game over

falling_objects = []    # List to store active falling objects. Each object is: [x_pos, y_pos, canvas_id]
player_x = (CANVAS_WIDTH - PLAYER_WIDTH) / 2 # Player's initial horizontal position (centered)

score_text_id = None    # Canvas item ID for the score display text
misses_text_id = None   # Canvas item ID for the misses display text
player_rect_id = None   # Canvas item ID for the player's rectangle

game_state = 'playing'  # Current game state: 'playing' or 'game_over'
last_spawn_time = 0     # Time when the last object was spawned

# --- Window and Canvas Setup ---
# Initialize the main Tkinter window
window = tk.Tk()
window.title("Catch the Falling Objects Game")
window.geometry(f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}") # Set window dimensions
window.resizable(False, False) # Prevent window resizing

# Create the game canvas
canvas = tk.Canvas(window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="lightgrey") # Changed bg for better contrast
canvas.pack() # Add canvas to the window
canvas.focus_set() # Set focus to the canvas to receive keyboard events

# --- Player Character Logic ---
def move_player_left(event=None):
    """Moves the player character to the left, constrained by the canvas edge."""
    global player_x
    if game_state == 'playing': # Player can only move if the game is active
        player_x = max(0, player_x - PLAYER_SPEED)

def move_player_right(event=None):
    """Moves the player character to the right, constrained by the canvas edge."""
    global player_x
    if game_state == 'playing': # Player can only move if the game is active
        player_x = min(CANVAS_WIDTH - PLAYER_WIDTH, player_x + PLAYER_SPEED)

# --- Falling Objects Logic ---
def create_falling_object():
    """Creates a new falling object at a random horizontal position at the top of the canvas."""
    x_position = random.randint(0, CANVAS_WIDTH - OBJECT_SIZE)
    # Each object: [x_coordinate, y_coordinate, canvas_item_id (initially None)]
    obj = [x_position, 0 - OBJECT_SIZE, None] # Start just above the canvas
    falling_objects.append(obj)

def update_object_positions():
    """
    Moves all active falling objects downwards.
    If an object moves off the bottom of the screen, it's a miss and is removed.
    """
    global misses
    objects_to_remove = [] # Objects to delete after iterating

    for obj in falling_objects:
        obj[1] += OBJECT_SPEED  # Move object down
        if obj[1] > CANVAS_HEIGHT: # Object is below the canvas
            misses += 1
            objects_to_remove.append(obj)
            if obj[2]: # If drawn
                canvas.delete(obj[2])

    # Remove objects from the main list
    for obj in objects_to_remove:
        if obj in falling_objects:
            falling_objects.remove(obj)

# --- Collision Detection Logic ---
def check_collisions():
    """
    Checks for collisions between the player and falling objects.
    Updates score and removes caught objects.
    """
    global score
    objects_to_remove = []
    player_bbox = (player_x, CANVAS_HEIGHT - PLAYER_HEIGHT,
                   player_x + PLAYER_WIDTH, CANVAS_HEIGHT)

    for obj in falling_objects:
        # Object's bounding box (oval is approximated by its bounding rectangle)
        obj_bbox = (obj[0], obj[1], obj[0] + OBJECT_SIZE, obj[1] + OBJECT_SIZE)

        # AABB collision check
        if (player_bbox[0] < obj_bbox[2] and player_bbox[2] > obj_bbox[0] and
                player_bbox[1] < obj_bbox[3] and player_bbox[3] > obj_bbox[1]):
            score += 1
            objects_to_remove.append(obj)
            if obj[2]: # If drawn
                canvas.delete(obj[2])

    for obj in objects_to_remove:
        if obj in falling_objects:
            falling_objects.remove(obj)

# --- Object Spawning Logic ---
def spawn_object_periodically():
    """Creates a new falling object if SPAWN_INTERVAL has passed."""
    global last_spawn_time
    current_time = window.tk.call('clock', 'milliseconds')
    if current_time - last_spawn_time > SPAWN_INTERVAL:
        create_falling_object()
        last_spawn_time = current_time

# --- Drawing Functions ---
def draw_player():
    """Draws the player's rectangle on the canvas."""
    global player_rect_id
    if player_rect_id and canvas.type(player_rect_id): # Check if ID is valid
        canvas.delete(player_rect_id)
    player_rect_id = canvas.create_rectangle(player_x, CANVAS_HEIGHT - PLAYER_HEIGHT,
                                           player_x + PLAYER_WIDTH, CANVAS_HEIGHT,
                                           fill=PLAYER_COLOR, outline=PLAYER_COLOR) # Added outline

def draw_objects():
    """Draws all falling objects or updates their positions on the canvas."""
    for obj in falling_objects:
        if obj[2] is None or not canvas.type(obj[2]): # If new or ID invalid
            obj[2] = canvas.create_oval(obj[0], obj[1],
                                         obj[0] + OBJECT_SIZE, obj[1] + OBJECT_SIZE,
                                         fill=OBJECT_COLOR, outline=OBJECT_COLOR) # Added outline
        else: # Update existing object's coordinates
            canvas.coords(obj[2], obj[0], obj[1],
                          obj[0] + OBJECT_SIZE, obj[1] + OBJECT_SIZE)

def draw_score():
    """Draws or updates the score display."""
    global score_text_id
    text_to_display = f"Score: {score}"
    if score_text_id and canvas.type(score_text_id): # Check if ID is valid
        canvas.itemconfig(score_text_id, text=text_to_display)
    else:
        score_text_id = canvas.create_text(10, 10, text=text_to_display,
                                           font=("Arial", 16, "bold"), fill="black", anchor="nw")

def draw_misses():
    """Draws or updates the misses display."""
    global misses_text_id
    text_to_display = f"Misses: {misses}/{miss_limit}"
    if misses_text_id and canvas.type(misses_text_id): # Check if ID is valid
        canvas.itemconfig(misses_text_id, text=text_to_display)
    else:
        misses_text_id = canvas.create_text(CANVAS_WIDTH - 10, 10, text=text_to_display,
                                            font=("Arial", 16, "bold"), fill="black", anchor="ne")

# --- Main Game Loop ---
def game_loop():
    """The core game loop, updating state and redrawing each frame."""
    global game_state, score, misses, last_spawn_time # Modifiable globals

    if game_state == 'playing':
        # --- Update Game Logic ---
        update_object_positions()
        check_collisions()
        spawn_object_periodically()

        # --- Drawing ---
        canvas.delete("all") # Clear canvas for fresh redraw
        draw_player()
        draw_objects()
        draw_score()
        draw_misses()

        # --- Check Game Over Condition ---
        if misses >= miss_limit:
            game_state = 'game_over'
            last_spawn_time = 0 # Reset spawn timer for next game
            # Display Game Over message
            canvas.create_text(CANVAS_WIDTH/2, CANVAS_HEIGHT/2 - 40,
                               text="GAME OVER!",
                               font=("Arial", 48, "bold"), fill="darkred", tags="game_over_text")
            canvas.create_text(CANVAS_WIDTH/2, CANVAS_HEIGHT/2 + 10,
                               text=f"Final Score: {score}",
                               font=("Arial", 24), fill="black", tags="game_over_text")
            canvas.create_text(CANVAS_WIDTH/2, CANVAS_HEIGHT/2 + 50,
                               text="Press 'R' to Restart",
                               font=("Arial", 18), fill="black", tags="game_over_text")
            # Ensure player and objects are not drawn on top of game over message
            if player_rect_id and canvas.type(player_rect_id): canvas.delete(player_rect_id)
            for obj_data in falling_objects:
                if obj_data[2] and canvas.type(obj_data[2]): canvas.delete(obj_data[2])


    elif game_state == 'game_over':
        # Game is paused. Message is on canvas. Awaiting restart.
        pass

    window.after(50, game_loop) # Schedule next loop iteration (approx 20 FPS)

# --- Game Restart Function ---
def restart_game(event=None):
    """Resets the game state to allow playing again."""
    global score, misses, player_x, falling_objects, game_state
    global score_text_id, misses_text_id, last_spawn_time, player_rect_id

    if game_state == 'game_over': # Only restart if game is actually over
        # Reset game variables
        score = 0
        misses = 0
        player_x = (CANVAS_WIDTH - PLAYER_WIDTH) / 2 # Center player
        falling_objects.clear() # Clear object list (canvas items cleared by game_loop's delete("all"))

        # Remove "Game Over" message
        canvas.delete("game_over_text")

        # Reset canvas item IDs for UI text (they will be recreated)
        score_text_id = None
        misses_text_id = None
        player_rect_id = None # Player will be redrawn

        # Reset spawn timer
        last_spawn_time = window.tk.call('clock', 'milliseconds')

        game_state = 'playing'
        # The game_loop, when 'playing', will call canvas.delete("all")
        # and then redraw everything fresh.

# --- Keyboard Bindings ---
window.bind("<Left>", move_player_left)
window.bind("<Right>", move_player_right)
window.bind("r", restart_game) # For lowercase 'r'
window.bind("R", restart_game) # For uppercase 'R'

# --- Start the Game ---
last_spawn_time = window.tk.call('clock', 'milliseconds') # Initialize spawn timer before first loop
game_loop()          # Start the game's update cycle
window.mainloop()    # Start Tkinter's event processing loop
