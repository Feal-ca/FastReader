import json
import os

filename = 'book_progress.json'

def load_progress():
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}

def save_progress(progress):
    with open(filename, 'w') as file:
        json.dump(progress, file, indent=4)

def update_progress(book_title, progress):
    all_progress = load_progress()
    all_progress[book_title] = progress
    save_progress(all_progress)
    print(f"Updated progress for '{book_title}' to {progress}.")

def get_progress(book_title):
    all_progress = load_progress()
    return all_progress.get(book_title, None)

