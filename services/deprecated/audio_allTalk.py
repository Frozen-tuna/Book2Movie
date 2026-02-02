import re
from pydub import AudioSegment
from config import Config
import requests
import json
import base64
from io import BytesIO

from db_utils import fetch_json, upsert_json

voices = [];

def audio_to_string(audio):
    temp_audio  = BytesIO()
    audio.export(temp_audio, format="wav")
    return base64.b64encode(temp_audio.getvalue()).decode("utf-8")

def string_to_audio(audio):
    raw_bytes = base64.b64decode(audio)
    temp_audio = BytesIO(raw_bytes)
    return AudioSegment.from_file(temp_audio, format="wav")

def check_status():
    url = Config.TTS_API_URL + "/api/ready"
    response = requests.get(url)
    if response.status_code == 200:
        return "API is ready"
    else:
        return False



def get_voices():
    url = Config.TTS_API_URL + "/api/voices"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return False
    
def generate_clip(text, voice):
    url = Config.TTS_API_URL + "/api/tts-generate"
    data = {
        "text_input": text,
        "character_voice_gen": voice,
        "response_format": "wav",
        "speed": 1.0,
        "text_filtering": "standard",
        "narrator_enabled": False,
        "narrator_voice_gen": voice,
        "text_not_inside": "character",
        "language": "en",
        "output_file_name": "output",
        "output_file_timestamp": False,
        "autoplay": False,
        "autoplay_volume": 0.9
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, json=data, data=data, headers=headers)
    if response.status_code == 200:
        audio = AudioSegment.from_file(json.loads(response.content.decode("utf-8"))["output_file_path"], format="wav") + AudioSegment.silent(duration=500)
        return audio_to_string(audio)
    else:
        print("Error generating audio:", response.text)
        return False

def split_text_by_sentences(text):

    if len(text) <= Config.MAX_TTS_LENGTH:
        return [text]
    
    chunks = []
    # Split by sentences while respecting the character limit
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s', text)
    
    current_chunk = ""
    for sentence in sentences:
        # If adding this sentence exceeds the limit, start a new chunk
        if len(current_chunk) + len(sentence) + 1 > Config.MAX_TTS_LENGTH and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
        else:
            current_chunk += sentence + " "
    
    # Add the last chunk if it exists
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # If we still have chunks that are too long, split them further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= Config.MAX_TTS_LENGTH:
            final_chunks.append(chunk)
        else:
            # Split long chunks into smaller pieces
            while len(chunk) > Config.MAX_TTS_LENGTH:
                # Find a good split point
                split_point = Config.MAX_TTS_LENGTH
                # Try to find a space or punctuation to avoid splitting words
                if chunk[Config.MAX_TTS_LENGTH-50:Config.MAX_TTS_LENGTH+50].find(' ') != -1:
                    # Find the nearest space
                    space_pos = chunk.rfind(' ', 0, Config.MAX_TTS_LENGTH)
                    if space_pos > Config.MAX_TTS_LENGTH - 100:
                        split_point = space_pos
                final_chunks.append(chunk[:split_point].strip())
                chunk = chunk[split_point:].strip()
            if chunk:
                final_chunks.append(chunk)
    
    return final_chunks

def generate_audio(quotes, av_db):
    clips = fetch_json("clips",  av_db) or []
    starting_index = 0

    if len(clips) > 0:
        starting_index = len(clips)
        print(f"Resuming generating audio from index {starting_index}")


    if check_status():
        for k,sentence in enumerate(quotes[starting_index:], start=starting_index):
            print("Generating audio for sentence:", k, "of", len(quotes)-1, end='\r')
            if not sentence.get("text").strip():
                clips.append({"sentence": sentence.get("text"), "audio": audio_to_string(AudioSegment.silent(duration=1000))})
            else:
                for chunk in split_text_by_sentences(sentence.get("text").strip()):
                    audio = generate_clip(chunk, sentence.get("voice"))
                    clips.append({"sentence": chunk, "audio": audio})
            if k % 20 == 0:
                upsert_json("clips", clips, av_db)
    print()
    print("Finished generating audio.")
    return build_tomes(clips)

def build_tomes(clips):
    duration_limit = 60
    groupings = []
    current_grouping = []
    current_length = 0
    tomes = []

    for clip in clips:
        clip_duration = string_to_audio(clip["audio"]).duration_seconds
        if current_length + clip_duration <= duration_limit:
            current_grouping.append(clip)
            current_length += clip_duration
        else:
            groupings.append(current_grouping)
            current_grouping = [clip]
            current_length = clip_duration
    if current_grouping:
        groupings.append(current_grouping)

    for group in groupings:
        sum_audio = AudioSegment.silent(duration=0)
        text = ""
        sentences = []
        for clip in group:
            sum_audio += string_to_audio(clip["audio"])
            text += clip["sentence"] + " "
            sentences.append(clip["sentence"])
        tomes.append({"audio": audio_to_string(sum_audio), "text": text, "sentences": sentences})

    return tomes