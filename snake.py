import sys
from tkinter import *
import random
import json
import os
import time
import pygame

# Game Configuration
GAME_WIDTH = 700
GAME_HEIGHT = 700
SPEED = 50
SPACE_SIZE = 50
BODY_PARTS = 3
SNAKE_COLOR = "#00FF00"
FOOD_COLOR = "#FF0000"
BACKGROUND_COLOR = "#000000"
HIGHSCORE_FILE = "highscore.json"
STATISTICS_FILE = "statistics.json"

menu_buttons = [] # Global list to keep track of menu buttons
start_time = None  # For tracking playtime
is_playing = False  # Flag to determine if the player is actively playing
direction_queue = []  # Queue to handle direction changes
last_song = None # Global variable to track the last song played
pygame.mixer.init() # Initialize Pygame mixer for music playback
sound_on = True


class Snake:
    """Snake class."""

    def __init__(self):
        self.body_size = BODY_PARTS
        self.coordinates = []
        self.squares = []

        for i in range(self.body_size):
            self.coordinates.append([0, 0])

        for x, y in self.coordinates:
            square = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR, tag="snakes")
            self.squares.append(square)


class Food:
    """Food class."""

    def __init__(self, snake_coordinates):
        while True:
            x = random.randint(0, (GAME_WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
            y = random.randint(0, (GAME_HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
            if (x, y) not in snake_coordinates:  # Check if the coordinates are not occupied
                break
        self.coordinates = [x, y]

        canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=FOOD_COLOR, tag="food")


def load_highscore():
    """Highscore handling."""

    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, 'r') as file:
            return json.load(file).get('highscore', 0)
    return 0


def save_highscore(highscore):
    with open(HIGHSCORE_FILE, 'w') as file:
        json.dump({'highscore': highscore}, file)


def load_statistics():
    """Statistics handling."""

    if os.path.exists(STATISTICS_FILE):
        with open(STATISTICS_FILE, 'r') as file:
            return json.load(file)
    # If the file doesn't exist, initialize with default values
    return {
        "games_played": 0,
        "total_score": 0,
        "highest_score": 0,
        "average_score": 0,
        "total_playtime": 0  # In seconds
    }


def save_statistics(statistics):
    with open(STATISTICS_FILE, 'w') as file:
        json.dump(statistics, file)


def update_statistics(current_score, playtime):
    statistics = load_statistics()
    statistics["games_played"] += 1
    statistics["total_score"] += current_score
    statistics["highest_score"] = max(statistics["highest_score"], current_score)
    statistics["average_score"] = statistics["total_score"] / statistics["games_played"]
    statistics["total_playtime"] += playtime  # Add the current game session's playtime

    save_statistics(statistics)


def remove_menu_buttons():
    """Clear previous menu buttons if any."""

    for button in menu_buttons:
        button.destroy()
    menu_buttons.clear()


def next_turn(snake, food):
    """Game Logic."""

    global score, highscore, is_playing, direction  # Declare as global

    # Check if there are any directions in the queue
    if direction_queue:
        new_direction = direction_queue.pop(0)  # Get the oldest direction in the queue
        if new_direction != direction:  # Update direction if it's different
            direction = new_direction

    x, y = snake.coordinates[0]

    if direction == "up":
        y -= SPACE_SIZE
    elif direction == "down":
        y += SPACE_SIZE
    elif direction == "left":
        x -= SPACE_SIZE
    elif direction == "right":
        x += SPACE_SIZE

    snake.coordinates.insert(0, (x, y))
    square = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR)
    snake.squares.insert(0, square)

    if (x, y) == (food.coordinates[0], food.coordinates[1]):
        score += 1
        label.config(text=f"Score: {score}")

        if score > highscore:
            highscore = score
            save_highscore(highscore)
            highscore_label.config(text=f"Best: {highscore}")

        canvas.delete("food")
        food = Food(snake.coordinates)  # Pass snake coordinates here
    else:
        del snake.coordinates[-1]
        canvas.delete(snake.squares[-1])
        del snake.squares[-1]

    if check_collisions(snake):
        game_over()
    else:
        window.after(SPEED, next_turn, snake, food)


def change_direction(new_direction):
    global direction
    opposites = {"left": "right", "right": "left", "up": "down", "down": "up"}

    # Prevent the snake from reversing direction
    if new_direction != opposites.get(direction, ""):
        direction_queue.append(new_direction)  # Add new direction to the queue


def check_collisions(snake):
    x, y = snake.coordinates[0]
    if x < 0 or x >= GAME_WIDTH or y < 0 or y >= GAME_HEIGHT:
        return True

    for body_part in snake.coordinates[1:]:
        if (x, y) == (body_part[0], body_part[1]):
            return True

    return False


def game_over():
    global is_playing, start_time
    canvas.delete(ALL)
    canvas.create_text(canvas.winfo_width() / 2, canvas.winfo_height() / 2 - 90,
                       font=("Malgun Gothic", 70), text="GAME OVER",
                       fill="red", tag="gameover")
    canvas.create_text(canvas.winfo_width() / 2, canvas.winfo_height() / 2 + 50,
                       font=("Malgun Gothic", 30), text="Press Space to start",
                       fill="white", tag="restart")
    is_playing = False
    playtime = time.time() - start_time
    update_statistics(score, playtime)  # Update stats with current score and playtime

    # Show the cursor
    window.config(cursor="arrow")  # Show the cursor


def start_game():
    global snake, food, score, direction, start_time, is_playing

    canvas.delete(ALL)  # Clear the canvas for a new game
    snake = Snake()  # Initialize the snake
    food = Food(snake.coordinates)  # Initialize the food
    score = 0
    direction = "down"  # Reset the direction
    label.config(text=f"Score: {score}")  # Reset the score label
    start_time = time.time()  # Reset the start time
    is_playing = True  # Set the game state to playing

    # Hide the cursor
    window.config(cursor="")  # Hide the cursor

    next_turn(snake, food)  # Start the game loop


def restart_game():
    global snake, food, score, direction, start_time, is_playing

    # Clear the canvas and set the state to not playing
    canvas.delete(ALL)
    is_playing = False  # Set is_playing to False

    remove_menu_buttons()

    # Display the message "Press Space to Start"
    canvas.create_rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, fill=BACKGROUND_COLOR)
    canvas.create_text(canvas.winfo_width() / 2, canvas.winfo_height() / 2,
                       font=("Malgun Gothic", 30), text="Press Space to Start",
                       fill="white", tag="start_message")


def show_menu():
    """Menu and Placeholder Functions."""

    global is_playing
    is_playing = False
    canvas.delete(ALL)
    canvas.create_rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, fill="black")

    remove_menu_buttons()

    # Create new menu buttons
    achievements_button = create_menu_button("Achievements", 100, show_achievements)
    sound_settings_button = create_menu_button("Sound Settings", 200, show_sound_settings)
    statistics_button = create_menu_button("Statistics", 300, show_statistics)

    # Store the buttons in the menu_buttons list
    menu_buttons.extend([achievements_button, sound_settings_button, statistics_button])


def create_menu_button(text, y_offset, command):
    button = Button(window, text=text, font=("Malgun Gothic", 15), command=command)
    button.place(x=GAME_WIDTH / 2 - 75, y=y_offset, width=150, height=50)
    return button


def show_achievements():
    canvas.delete(ALL)
    remove_menu_buttons()
    canvas.create_text(GAME_WIDTH / 2, 65, font=("Malgun Gothic", 40), text="Achievements", fill="white")

    # Load statistics to check completed achievements
    statistics = load_statistics()

    # Create variables for positioning
    x_offset1 = GAME_WIDTH / 8  # First column position
    x_offset2 = 3 * GAME_WIDTH / 7  # Second column position
    x_offset3 = 5 * GAME_WIDTH / 7  # Third column position
    y_offset = 150  # Initial y position
    spacing = 30  # Space between achievements

    # Loop through achievements
    for index, achievement in enumerate(achievements):
        threshold = achievement["threshold"]
        achieved = False

        # Check if the achievement has been met
        if achievement["type"] == "games_played" and statistics["games_played"] >= threshold:
            achieved = True
        elif achievement["type"] == "total_score" and statistics["total_score"] >= threshold:
            achieved = True
        elif achievement["type"] == "highest_score" and statistics["highest_score"] >= threshold:
            achieved = True
        elif achievement["type"] == "total_playtime" and statistics["total_playtime"] >= threshold:
            achieved = True

        # Set the color based on achievement status
        color = "green" if achieved else "grey"
        # Determine column and position
        if index < len(achievements) / 3:
            # First column
            canvas.create_text(x_offset1, y_offset + index * spacing, anchor='w', font=("Malgun Gothic", 12),
                               text=achievement["name"], fill=color)
        elif index < 2 * len(achievements) / 3:
            # Second column
            canvas.create_text(x_offset2, y_offset + (index - len(achievements) / 3) * spacing, anchor='w',
                               font=("Malgun Gothic", 12), text=achievement["name"], fill=color)
        else:
            # Third column
            canvas.create_text(x_offset3, y_offset + (index - 2 * len(achievements) / 3) * spacing, anchor='w',
                               font=("Malgun Gothic", 12), text=achievement["name"], fill=color)


def show_sound_settings():
    canvas.delete(ALL)
    remove_menu_buttons()
    canvas.create_text(GAME_WIDTH / 2, 65, font=("Malgun Gothic", 40), text="Sound Settings", fill="white")


def show_statistics():
    canvas.delete(ALL)
    remove_menu_buttons()
    statistics = load_statistics()

    # Convert total playtime (in seconds) to hours, minutes, and seconds
    total_seconds = statistics['total_playtime']
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format the playtime as 2h 50min 30s
    formatted_playtime = f"{int(hours)}h {int(minutes)}min {int(seconds)}s"

    # Display statistics on the canvas
    stats_text = (
        f"Games Played: {statistics['games_played']}\n"
        f"Total Score: {statistics['total_score']}\n"
        f"Highest Score: {statistics['highest_score']}\n"
        f"Average Score: {statistics['average_score']:.2f}\n"
        f"Playtime: {formatted_playtime}"
    )

    canvas.create_text(GAME_WIDTH / 2, 65, font=("Malgun Gothic", 40),
                       text="Statistics", fill="white")
    canvas.create_text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 50, font=("Malgun Gothic", 20),
                       text=stats_text, fill="white")


# List of achievements
achievements = [
    {"name": "Play 5 games", "type": "games_played", "threshold": 5},
    {"name": "Play 10 games", "type": "games_played", "threshold": 10},
    {"name": "Play 25 games", "type": "games_played", "threshold": 25},
    {"name": "Play 50 games", "type": "games_played", "threshold": 50},
    {"name": "Play 100 games", "type": "games_played", "threshold": 100},
    {"name": "Play 250 games", "type": "games_played", "threshold": 250},
    {"name": "Play 500 games", "type": "games_played", "threshold": 500},
    {"name": "Play 1000 games", "type": "games_played", "threshold": 1000},

    {"name": "Total score 100", "type": "total_score", "threshold": 100},
    {"name": "Total score 250", "type": "total_score", "threshold": 250},
    {"name": "Total score 500", "type": "total_score", "threshold": 500},
    {"name": "Total score 1000", "type": "total_score", "threshold": 1000},
    {"name": "Total score 2500", "type": "total_score", "threshold": 2500},
    {"name": "Total score 5000", "type": "total_score", "threshold": 5000},
    {"name": "Total score 10'000", "type": "total_score", "threshold": 10000},

    {"name": "Highest score 5", "type": "highest_score", "threshold": 5},
    {"name": "Highest score 10", "type": "highest_score", "threshold": 10},
    {"name": "Highest score 15", "type": "highest_score", "threshold": 15},
    {"name": "Highest score 20", "type": "highest_score", "threshold": 20},
    {"name": "Highest score 25", "type": "highest_score", "threshold": 25},
    {"name": "Highest score 30", "type": "highest_score", "threshold": 30},
    {"name": "Highest score 35", "type": "highest_score", "threshold": 35},
    {"name": "Highest score 40", "type": "highest_score", "threshold": 40},
    {"name": "Highest score 45", "type": "highest_score", "threshold": 45},
    {"name": "Highest score 50", "type": "highest_score", "threshold": 50},
    {"name": "Highest score 55", "type": "highest_score", "threshold": 55},
    {"name": "Highest score 60", "type": "highest_score", "threshold": 60},
    {"name": "Highest score 65", "type": "highest_score", "threshold": 65},
    {"name": "Highest score 70", "type": "highest_score", "threshold": 70},
    {"name": "Highest score 75", "type": "highest_score", "threshold": 75},
    {"name": "Highest score 80", "type": "highest_score", "threshold": 80},
    {"name": "Highest score 85", "type": "highest_score", "threshold": 85},
    {"name": "Highest score 90", "type": "highest_score", "threshold": 90},
    {"name": "Highest score 95", "type": "highest_score", "threshold": 95},
    {"name": "Highest score 100", "type": "highest_score", "threshold": 100},

    # Playtime achievements
    {"name": "Playtime 5 min", "type": "total_playtime", "threshold": 5 * 60},
    {"name": "Playtime 15 min", "type": "total_playtime", "threshold": 15 * 60},
    {"name": "Playtime 30 min", "type": "total_playtime", "threshold": 30 * 60},
    {"name": "Playtime 1h", "type": "total_playtime", "threshold": 60 * 60},
    {"name": "Playtime 2h", "type": "total_playtime", "threshold": 2 * 60 * 60},
]


def play_random_song():
    global last_song
    songs_folder = 'Songs'
    songs = [f for f in os.listdir(songs_folder) if f.endswith('.mp3')]  # List all MP3 files

    if len(songs) <= 1:
        return  # If there's only one song or none, just return

    next_song = random.choice(songs)

    # Ensure the next song isn't the same as the last one
    while next_song == last_song:
        next_song = random.choice(songs)

    last_song = next_song

    song_path = os.path.join(songs_folder, next_song)
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()


def check_music():
    """Function to continuously check if music has stopped and play a new song."""

    if not pygame.mixer.music.get_busy():  # If no music is playing
        play_random_song()  # Play the next random song
    window.after(1000, check_music)  # Check every second


def toggle_sound():
    global sound_on
    if sound_on:
        # Mute the sound
        pygame.mixer.music.set_volume(0)
        sound_button.config(text="Sound is: OFF")
    else:
        # Unmute the sound
        pygame.mixer.music.set_volume(1)  # Change to your desired volume level
        sound_button.config(text="Sound is: ON")
    sound_on = not sound_on


# Tkinter Window Setup
window = Tk()
window.title("Snake")
window.resizable(False, False)

# Score and Highscore
score = 0
direction = "down"
highscore = load_highscore()

# Labels for score and highscore
label = Label(window, text=f"Score: {score}", font=("Malgun Gothic", 35))
label.pack()

highscore_label = Label(window, text=f"Best: {highscore}", font=("Malgun Gothic", 20))
highscore_label.place(x=GAME_WIDTH - 160, y=10, width=160, height=50)

# Canvas
canvas = Canvas(window, bg=BACKGROUND_COLOR, height=GAME_HEIGHT, width=GAME_WIDTH)
canvas.pack()


def centering_window():
    """Centering window"""

    window.update()

    window_width = window.winfo_width()
    window_height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    y_offset = window.winfo_rooty() - window.winfo_y()
    fine_tune_offset = 10  # Adjust this value to fine-tune vertical positioning

    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2)) - y_offset - fine_tune_offset

    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
centering_window()

def binding_keys():
    """Binding keys"""

    window.bind("<Left>", lambda event: change_direction("left"))
    window.bind("<Right>", lambda event: change_direction("right"))
    window.bind("<Up>", lambda event: change_direction("up"))
    window.bind("<Down>", lambda event: change_direction("down"))
    window.bind("<space>", lambda event: start_game())  # Call a new function to start the game
    window.bind("<Escape>", lambda event: sys.exit())

    # Buttons for restart and menu
    Button(window, text="Restart", command=restart_game, font=("Malgun Gothic", 15)).place(x=10, y=10, width=100, height=50)
    Button(window, text="Menu", command=show_menu, font=("Malgun Gothic", 15)).place(x=120, y=10, width=100, height=50)


def initialization_process():
    """Initialize the game."""

    centering_window()
    binding_keys()
    restart_game()
    play_random_song()  # Start playing the first random song
    check_music()  # Continuously check if music has stopped and play the next

    window.mainloop()
initialization_process()
