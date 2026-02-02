import math
import random
import itertools
from prompts import Prompts
from config import Config
import true_characters

def map_character_voices(voices, quotes, characters):        
    all_voices = voices.copy()

    for quote in quotes:
        for character in characters:
            character.count = 0
            if quote.get("character").get("name") == character.name:
                character.count += 1
                break

    # remove narrator voice from available voices
    narrator_char = true_characters.narrator()
    narrator_char.voice = Config.NARRATOR_VOICE
    if not any(c.name == narrator_char.name for c in characters):
        characters.append(narrator_char)


    voices = [voice for voice in voices if voice.get("voice") != Config.NARRATOR_VOICE]

    voices = assign_character_voices_by_type(voices, characters, Prompts.Voice_type.masculine)
    voices = assign_character_voices_by_type(voices, characters, Prompts.Voice_type.feminine)
    voices = assign_character_voices_by_type(voices, characters, Prompts.Voice_type.machine)
    assign_character_voices_with_unknown_type(voices, characters)

    for voice in all_voices:
        if voice not in voices:
            voice["lead"] = True

    return characters, all_voices

def assign_character_voices_by_type(voices, characters, voice_type):

    leads_assigned = False
    lead_voices = []

    for v in voices:
        if v.get("lead"):
            leads_assigned = True

    filtered_voices = [voice for voice in voices if (voice.get("voice_type") == voice_type and voice.get("lead") != True)]
    filtered_characters = [char for char in characters if char.type == voice_type]

    if not leads_assigned:
        print(f"Assigning lead voices for {voice_type} characters")
        lead_number = math.floor(len(filtered_voices) / 3)
        lead_voices = random.sample(filtered_voices, min(lead_number, len(filtered_voices)))
        lead_characters = sorted(filtered_characters, key=lambda char: char.count, reverse=True)[:lead_number]
        remaining_voices = [voice for voice in filtered_voices if voice not in lead_voices]

        if len(lead_voices) == len(lead_characters):
            for i, lead in enumerate(lead_characters):
                lead.voice = lead_voices[i].get("voice")
                lead.lead = True
    else:
        remaining_voices = filtered_voices

    if len(remaining_voices) == 0:
        voice_cycle = itertools.cycle([voice for voice in voices if (voice.get("voice_type") == Prompts.Voice_type.masculine and voice.get("lead") != True)])
    else:
        voice_cycle = itertools.cycle(remaining_voices)
        
    for character in filtered_characters:
        if character.voice is None:
            character.voice = next(voice_cycle).get("voice")

    return [voice for voice in voices if voice not in lead_voices]

def assign_character_voices_with_unknown_type(voices, characters):
    filtered_voices = [voice for voice in voices if voice.get("voice_type") == Prompts.Voice_type.masculine or voice.get("voice_type") == Prompts.Voice_type.feminine]
    filtered_characters = [char for char in characters if char.type == Prompts.Voice_type.unknown or char.type is None]

    voice_cycle = itertools.cycle(filtered_voices)
    for character in filtered_characters:
        if character.voice is None:
            character.voice = next(voice_cycle).get("voice")
    
def get_character_voice(character_name, complete_characters):
    for character in complete_characters:
        if character.name == character_name:
            return character.voice
    return None

def get_random_voice_by_type(voices, voice_type=None):
    if voice_type is not None and voice_type != Prompts.Voice_type.unknown:
        filtered_voices = [voice for voice in voices if voice.get("voice_type") == voice_type]
    else:
        masculine_voices = [voice for voice in voices if voice.get("voice_type") == Prompts.Voice_type.masculine]
        femenine_voices = [voice for voice in voices if voice.get("voice_type") == Prompts.Voice_type.feminine]
        

        #masculine bias. Feel free to adjust. Some check here must be done even for 50/50 as the quantity of available voices may be uneven.
        if masculine_voices and random.random() < 0.8:
            filtered_voices = masculine_voices
        else:
            filtered_voices = femenine_voices
    return random.choice(filtered_voices).get("voice")


def assign_voices_to_quotes(quotes, characters, voices):
    assigned_quotes = []
    unknown_counter = 0
    unknown_one = {}
    unknown_two = {}
    for quote in quotes:
        if quote.get("character").get("name") != "unknown" and quote.get("character").get("name") != "narrator":
            unknown_counter = 0
            assigned_quotes.append({"text": quote.get("quote"), "voice": get_character_voice(quote.get("character").get("name"), characters)})
        elif quote.get("character").get("name") == "narrator":
            if quote.get("quote").strip() != "":
                unknown_counter = 0
            assigned_quotes.append({"text": quote.get("quote"), "voice": Config.NARRATOR_VOICE})
        else:
            if unknown_counter == 0:
                unknown_one = {}
                unknown_two = {}
            unknown_counter += 1
            if unknown_counter == 1:
                #first unknown voice
                unknown_one = get_random_voice_by_type(voices, quote.get("character").get("type"))
                assigned_quotes.append({"text": quote.get("quote"), "voice": unknown_one})
            elif unknown_counter == 2:
                #second unknown voice
                unknown_two = get_random_voice_by_type(voices, quote.get("character").get("type"))
                #ensure different from first
                while unknown_two == unknown_one:
                    unknown_two = get_random_voice_by_type(voices, quote.get("character").get("type"))
                assigned_quotes.append({"text": quote.get("quote"), "voice": unknown_two})
            elif unknown_counter >= 3:
                #alternate between the two voices
                if unknown_counter % 2 == 1:
                    assigned_quotes.append({"text": quote.get("quote"), "voice": unknown_one})
                else:
                    assigned_quotes.append({"text": quote.get("quote"), "voice": unknown_two})

    return assigned_quotes

