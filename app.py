from datetime import date
import random

MOVIES = ["Scream", "Halloween", "The Conjuring", "The Shining", "A Nightmare on Elm Street"]
TV_EPISODES = [
    {"show": "The Simpsons", "episode": "Treehouse of Horror"},
    {"show": "Bob's Burgers", "episode": "Full Bars"},
    {"show": "Family Guy", "episode": "Halloween on Spooner Street"},
    {"show": "Community", "episode": "Epidemiology"},
]
GAMES = [
    "Phasmophobia",
    "Resident Evil 4",
    "Dead by Daylight",
    "Outlast",
    "Until Dawn",
    "Halloween: The Game",
]

def roll_movie():
    movie = random.choice(MOVIES)
    print(f"🎬 Tonight's movie is: {movie}")

def roll_episode():
    episode = random.choice(TV_EPISODES)
    print("📺 Tonight's Halloween episode:")
    print(f"{episode['show']} - {episode['episode']}")

def roll_game():
    game = random.choice(GAMES)
    print(f"🎮 Tonight's Spooky Video Game: {game}")


def days_until_halloween():
    today = date.today()
    halloween = date(today.year, 10, 31)
    return (halloween - today).days


def main():
    print("🎃 Welcome to 31 Nights 🎃")

    while True:
        print(f"{days_until_halloween()} days until Halloween! 🎃")
        print()
        print("What do you want to roll?")
        print("1. A Movie 🎬")
        print("2. A Halloween TV episode 📺")
        print("3. A Spooky Video Game 🎮")
        print("4. Exit 👻")

        choice = input("Choose 1, 2, 3, or 4: ")

        if choice == "1":
            roll_movie()
            print("\nPress Enter to choose again.")
        elif choice == "2":
            roll_episode()
            print("\nPress Enter to choose again.")
        elif choice == "3":
            roll_game()
            print("\nPress Enter to choose again.")
        elif choice == "4":
            print("Happy Halloween! 🎃")
            break
        else:
            print("This is not a valid choice.")
if __name__ == "__main__":
    main()