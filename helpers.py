import requests
from functools import wraps
from flask import redirect, session

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def is_username_taken(username, db):
    username = username
    rows = db.execute("SELECT username FROM users WHERE LOWER(username) = LOWER(?)", username)

    return len(rows) > 0

def generate_keyword():
    import random
    adjectives = ["Happy", "Sad", "Quick", "Lazy", "Bright", "Dark", "Clever", "Brave", "Calm", "Eager"]
    nouns = ["Dog", "Cat", "Car", "Tree", "House", "River", "Mountain", "Sky", "Ocean", "Star"]
    return f"{random.choice(adjectives)} {random.choice(nouns)}"

def get_random_noun():
    api_key = "qyg7y39wqnycxi69xliniu2v6hbzgpm9xhpsizosx71gpbp4a"
    url = f"https://api.wordnik.com/v4/words.json/randomWord"
    params = {
        'hasDictionaryDef': 'true',
        'includePartOfSpeech': 'noun',
        'excludePartOfSpeech': 'proper-noun',
        'minCorpusCount': 7000,      # not too rare
        'maxCorpusCount': 120000000,      # not too common
        'minLength': 4,
        'maxLength': 14,        
        'api_key': api_key
    }
    
    # Retry up to 3 times
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=15)  # Increased timeout
            response.raise_for_status()
            data = response.json()
            word = data.get("word", None)
            if word:
                return word
        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Error fetching word (attempt {attempt + 1}): {e}")
            # Don't retry on 404 errors - try different params instead
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                break
    
    return None  # All retries failed


def validate_word(words_list):
    return all(len(word) >= 3 and word.isalpha() for word in words_list)


def check_forbidden_words(description, forbidden_words):
    description_no_spaces = description.replace(" ", "").lower()

    for word in forbidden_words:
        if word.lower() in description_no_spaces:
            return True
        
    return False

def has_keyword(description, keyword):
    description_no_spaces = description.replace(" ", "").lower()
    keyword_no_spaces = keyword.replace(" ", "").lower()
    return keyword_no_spaces in description_no_spaces

