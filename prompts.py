from enum import Enum
from config import Config

class Prompts:
    image_template = """You are a professional prompt engineer working with image generation tools such as Stable Diffusion, Midjourney, Flux, etc. Use your powers of analysis and knowledge of successful prompt design to create an image description that would perfectly display the most interesting, vivid action from book exerpts.

Given: """ +  Config.BOOK_TITLE + " - " + Config.BOOK_DESCRIPTION + """

CONTEXT BLOCK (BROAD SETTING ONLY):
{large_book_description}

TARGET PASSAGE (THE ONLY SOURCE OF VISUAL CONTENT):
{excerpt}

Rules:
- CONTEXT provides general world information only (tone, genre, tech level).
- TARGET PASSAGE provides all visual details.
- Do NOT add story details not visible in the excerpt.
- Do NOT use CONTEXT to add characters, objects, locations, or events.
- Always follow the required output format.

""" + Config.IMAGE_PROMPT_ASSIST + """ 

Focus and add details on the most visually interesting elements of the TARGET PASSAGE. Add additional visual details for the main characters. Do not use proper nouns but use phrases like "man", " teenage boy", "teenage girl", or "woman" instead. Your goal is to describe an image with key visual details, not make a comma delimited list.

    {format_instructions}
    
"""

    voice_type_template = """You are a digital sorting system. Take the following file name of a voice sample and guess it's gender. The 2nd character usually indicates m for  masculine or f for feminine. For exampled, pf_dora would be feminine. If you cannot tell, say unknown.
    
    {file_name}

    {format_instructions}
    
"""

    characters_template = """You are a Literature professor at a prestigious university. You must track all the speaking characters from the passage that you can. You do not need to add characters who never speak. There will be a quiz after.

    PASSAGE:
    {excerpt}

    Rules:
        Try to name each character that speaks in the passage. You may guess what kind of speaker they are. Only add new characters that speak. Add their full name if it is given, otherwise you can use nicknames.
    """ + Config.LLM_CHARACTER_EXTRA_INSTRUCTIONS + """
    
    {format_instructions}

"""

    dedupe_characters_template = """You are a digital sorting system. Take the following list of characters and deduplicate them. If two characters have the same name, keep the one that appears last in the list. If two characters have the same name, only keep one of them.
Combine characters that are effectively the same character, but have different names. For example, if a character is referred to as "John" and "Johnny", combine them into one character with the name "John". If a character is referred to as "John" and "John Smith", combine them into one character with the name "John Smith".
If given two similar names, use the longer name.
    CHARACTERS:
    {characters}

    """ + Config.LLM_CHARACTER_EXTRA_INSTRUCTIONS + """

    {format_instructions}

"""


    speaker_template = """You are a helpful assistant.
Create a thorough analysis about the quote in the context of the passage it was taken from. Based on the passage, determine who is most likely to have spoken the quote. Use only the information provided in the passage. Do not use any external information. Be thorough when explaining your reasoning. If there is no clear speaker, say "unknown".
human

    PASSAGE:
    ---
    {excerpt}
    ---


    QUOTE:
    ---
    {quote}
    ---
    
    Please provide a detailed analysis of who is most likely to have spoken the quote based on the passage. Answer at the end of your analysis.
    Never respond with an empty message or silence.
    If unsure, summarize the input neutrally.
"""

    speaker_follow_up_template = """You are a digital sorting system. Given the following analysis of a quote and passage, and a list of characters, determine which character is most likely to have spoken the quote. Do not use external information. Your answer must be part of the list.
    
    ANALYSIS:
    {analysis}

    CHARACTERS:
    {formatted_characters}
    
    {format_instructions}
    

    Only choose a speaker from the provided character list. Do not invent new names. If unsure, use 'unknown'. If the analysis does not explicitly name a character from the list, choose 'unknown'.
"""

    class Voice_type(str, Enum):
        masculine = "masculine"
        feminine = "feminine"
        machine = "machine"
        unknown = "unknown"