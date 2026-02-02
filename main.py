import argparse
from db_utils import fetch_json, fetch_status, upsert_json, upsert_status
import preprocess
import audio
import speech
import image
import movie
import llm
import true_characters
from tinydb import TinyDB

def main(book_name, start_page, end_page):
    voices_db = TinyDB("data/voices.json")

    raw_voices = fetch_json("raw_voices",  voices_db)

    if not raw_voices:
        input("Press enter when tts server is running to fetch possible voices")
        raw_voices = {}
        raw_voices["list"] = audio.get_voices()["voices"]
        upsert_json("raw_voices", raw_voices, voices_db)

    llm.__init__()

    if not raw_voices.get("mapped_voices"):
        input("Press enter when llm server is running to map voices to gender")
        raw_voices["mapped_voices"] = llm.populate_voice_types(raw_voices["list"])
        upsert_json("raw_voices", raw_voices, voices_db)

    book_db = TinyDB(book_name + ".json")
    status = fetch_status(start_page, end_page, book_db)

    if not status.get("text"):
        text = preprocess.read(book_name, start_page, end_page)
        upsert_json("text", text, book_db)
        upsert_status(status, "text", start_page, end_page, book_db)

    # won't work right if book is generated out of order. IE Chapter 1, Chapter 3, then chapter 2. can go backwards though.
    if not status.get("characters"):
        input("Press enter when llm server is running to collect characters")
        text = fetch_json("text", book_db)
        character_data = fetch_json("characters", book_db)
        characters = [true_characters.TrueCharacter.from_dict(char) for char in character_data] if character_data else []
        characters = true_characters.populate_characters(text, characters)
        upsert_json("characters", [c.to_dict() for c in characters], book_db)
        upsert_status(status, "characters", start_page, end_page, book_db)


    # figure out who said what. Takes the most time
    if not status.get("quotes"):
        input("Press enter when llm server is running to map quotes to characters")
        text = fetch_json("text", book_db)
        characters = [true_characters.TrueCharacter.from_dict(char) for char in fetch_json("characters", book_db)]
        quotes = true_characters.map_quotes_to_characters(text, characters, book_db)
        upsert_json("quotes", quotes, book_db)
        upsert_status(status, "quotes", start_page, end_page, book_db)

    # assigning voices to characters. Saved between sessions
    if not status.get("character_voices"):
        characters = [true_characters.TrueCharacter.from_dict(char) for char in fetch_json("characters", book_db)]
        quotes = fetch_json("quotes",  book_db)
        characters, raw_voices["mapped_voices"] = speech.map_character_voices(raw_voices["mapped_voices"], quotes, characters)
        upsert_json("characters", [c.to_dict() for c in characters], book_db)
        upsert_json("raw_voices", raw_voices, voices_db)
        upsert_status(status, "character_voices", start_page, end_page, book_db)

    # put the voices of the characters onto the quotes
    if not status.get("voiced_quotes"):
        quotes = fetch_json("quotes", book_db)
        characters = [true_characters.TrueCharacter.from_dict(char) for char in fetch_json("characters", book_db)]
        raw_voices = fetch_json("raw_voices", voices_db)
        voiced_quotes = speech.assign_voices_to_quotes(quotes, characters, raw_voices["mapped_voices"])

        upsert_json("voiced_quotes", voiced_quotes, book_db)
        upsert_json("raw_voices", raw_voices, voices_db)
        upsert_status(status, "voiced_quotes", start_page, end_page, book_db)

    av_db = TinyDB(book_name + ".av.json")

    # generate chunks of audio with voice mapped quotes. "Tomes" are X seconds of audio, effectively one slide in the final product.
    if not status.get("sound"):
        input("Press enter when tts server is running")
        voiced_quotes = fetch_json("voiced_quotes", book_db)
        tomes = audio.generate_audio(voiced_quotes, av_db)
        upsert_json("tomes", tomes, av_db)
        upsert_status(status, "sound", start_page, end_page, book_db)

    if not status.get("image_prompts"):
        input("Press enter when llm server is running")
        tomes = fetch_json("tomes", av_db)
        tomes = image.populate_tome_image_prompts(tomes, av_db)
        upsert_json("tomes", tomes, av_db)
        upsert_status(status, "image_prompts", start_page, end_page, book_db)

    if not status.get("images"):
        input("Press enter when image server is running")
        tomes = fetch_json("tomes", av_db)
        images = image.build_images(tomes, av_db)
        upsert_json("images", images, av_db)
        upsert_status(status, "images", start_page, end_page, book_db)

    tomes = fetch_json("tomes", av_db)
    images = fetch_json("images", av_db)
    movie.build_movie(tomes, images, book_name, start_page, end_page)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process an ebook to generate a movie."
    )
    parser.add_argument(
        "book_name",
        type=str,
        help="The name of the book to process. Should match a file in the data directory",
    )
    parser.add_argument("start_page", type=int, help="page to start processing from")
    parser.add_argument("end_page", type=int, help="page to end processing to")
    args = parser.parse_args()
    main(args.book_name, args.start_page, args.end_page)
