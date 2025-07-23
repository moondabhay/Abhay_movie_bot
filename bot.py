import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from typing import List
import urllib.parse
import requests

TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TMDB_API_KEY = 'YOUR_TMDB_API_KEY'  # Get from https://www.themoviedb.org
REDIRECT_BOT_URL = 'https://t.me/YOUR_REDIRECT_BOT?start='

# Mock search results — In production, fetch/download link data dynamically
def fetch_movie_links(movie_title: str) -> List[dict]:
    # Example static results format (replace logic with real scraping or DB/logic as needed)
    results = [
        {"size": "1.23 GB", "quality": "720p", "title": f"{movie_title} (2001)", "url": f"{REDIRECT_BOT_URL}{urllib.parse.quote_plus(movie_title + '_720p')}"},
        {"size": "2.80 GB", "quality": "1080p", "title": f"{movie_title} (2001)", "url": f"{REDIRECT_BOT_URL}{urllib.parse.quote_plus(movie_title + '_1080p')}"},
        {"size": "700 MB", "quality": "480p", "title": f"{movie_title} (2001)", "url": f"{REDIRECT_BOT_URL}{urllib.parse.quote_plus(movie_title + '_480p')}"}
    ]
    return results

def get_movie_info_tmdb(movie_title: str):
    url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={urllib.parse.quote_plus(movie_title)}'
    r = requests.get(url)
    data = r.json()
    result = {}
    if data.get("results"):
        movie = data["results"][0]
        genres = []
        # Genre fetch
        if movie.get('genre_ids'):
            # TMDB Genre mapping example, real code should cache this dict.
            genre_map = {
                12: "Adventure", 14: "Fantasy", 10751: "Family", 28: "Action",
                16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary",
                18: "Drama", 10752: "War", 36: "History"
                # Add all codes as needed...
            }
            genres = [genre_map.get(gid, str(gid)) for gid in movie["genre_ids"]]
        result['title'] = movie.get('title', 'N/A')
        result['year'] = movie.get('release_date', 'N/A')[:4]
        result['genres'] = ", ".join(genres) if genres else 'N/A'
        result['overview'] = movie.get('overview', '')
        result['rating'] = movie.get('vote_average', 'N/A')
        result['language'] = movie.get('original_language', 'N/A').upper()
        result['duration'] = 'N/A'  # Duration needs another API call (details endpoint), left blank to keep it snappy
    else:
        # fallback format
        result['title'] = movie_title
        result['year'] = 'N/A'
        result['genres'] = 'N/A'
        result['overview'] = ''
        result['rating'] = 'N/A'
        result['language'] = 'N/A'
        result['duration'] = 'N/A'
    return result

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🔎 Send any movie name to get links and info!"
    )

def make_links_message(links: List[dict]) -> (str, InlineKeyboardMarkup):
    msg = "Your Requested Files ⬇️\n"
    buttons = []
    for idx, item in enumerate(links, 1):
        label = f"[{item['size']}] {item['title']} {item['quality']}"
        msg += f"{idx}. {label}\n"
        buttons.append([InlineKeyboardButton(f"Download {item['quality']} ({item['size']})", url=item['url'])])
    return msg, InlineKeyboardMarkup(buttons)

def movie_search(update: Update, context: CallbackContext):
    query = update.message.text.strip()
    info = get_movie_info_tmdb(query)
    links = fetch_movie_links(info['title'])

    info_msg = (
        f"*{info['title']}* ({info['year']})\n"
        f"Genres: {info['genres']}\n"
        f"Rating: {info['rating']} ⭐\n"
        f"Language: {info['language']}\n"
        # f"Duration: {info['duration']}\n"
        f"\n{info['overview']}\n"
        f"\n*Result Shown In:* {round(update.message.date.timestamp())} seconds\n"
        f"Requested by: {update.effective_use