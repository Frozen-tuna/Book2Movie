from typing import List, Optional
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from config import Config
from db_utils import upsert_json
from prompts import Prompts
from typing import List
import json
import os


token = "your_bearer_token_here"
# langchain.debug = True
image_chain = None
voice_type_chain = None
characters_chain = None
dedupe_characters_chain = None
speaker_chain = None
speaker_follow_up_chain = None

class ImagePrompt(BaseModel):
    prompt: str = Field(description="Combine 1-4 into a single vivid image prompt")

class Voice_type(BaseModel):
    voice_type: Prompts.Voice_type = Field(description="A guess for the voice_type of the file name. It is okay to not know. Must be one of: masculine, feminine, machine, unknown.")

class Character(BaseModel):
    name: str = Field(description="A name for the speaking character, if it exists. If no name can be determined, use 'unknown'. Only add characters that speak.")
    aliases: Optional[str] = Field(default="", description="Other names or titles the character might go by, if any. Otherwise, empty string. Should be empty if name is unknown.")
    type: Prompts.Voice_type = Field(description="The type of character this is. It is okay to not know. Must be one of: masculine, feminine, machine, unknown.")

class Speaker(BaseModel):
    name: str = Field(description="The name of the character that the quote can be attributed to. If no name can be determined, use 'unknown'.")
    type: Optional[Prompts.Voice_type] = Field(description="For unknown speakers, a guess at their voice type. Can be one of: masculine, feminine, machine, unknown.")
    

class CharacterList(BaseModel):
    characters: List[Character] = Field(description="A list of characters, each containing their name and a guess at what kind of character they are.")

class CharacterDedupe(BaseModel):
    characters: List[str] = Field(description="A list of character names, deduplicated. If two characters have the same name, keep the one that appears most in the list. If two characters have the same name, only keep one of them. Combine characters that are effectively the same character, but have different names. For example, if a character is referred to as 'John' and 'Johnny', combine them into one character with the name 'John'. If a character is referred to as 'John' and 'John Smith', combine them into one character with the name 'John Smith'.")

image_prompt_parser = PydanticOutputParser(pydantic_object=ImagePrompt)
voice_type_parser = PydanticOutputParser(pydantic_object=Voice_type)
character_parser = PydanticOutputParser(pydantic_object=CharacterList)
dedupe_parser = PydanticOutputParser(pydantic_object=CharacterDedupe)
speaker_parser = PydanticOutputParser(pydantic_object=Speaker)


def __init__():
    global image_chain
    global voice_type_chain
    global characters_chain
    global dedupe_characters_chain
    global speaker_chain
    global speaker_follow_up_chain

    image_chain_prompt = PromptTemplate(template=Prompts.image_template, input_variables=["large_book_description", "excerpt"], partial_variables={"format_instructions": image_prompt_parser.get_format_instructions()})
    voice_type_chain_prompt = PromptTemplate(template=Prompts.voice_type_template, input_variables=["file_name"],  partial_variables={"format_instructions": voice_type_parser.get_format_instructions()})
    characters_chain_prompt = PromptTemplate(template=Prompts.characters_template, input_variables=["excerpt"],  partial_variables={"format_instructions": character_parser.get_format_instructions()})
    dedupe_characters_chain_prompt = PromptTemplate(template=Prompts.dedupe_characters_template, input_variables=["characters"],  partial_variables={"format_instructions": dedupe_parser.get_format_instructions()})
    speaker_chain_prompt = PromptTemplate(template=Prompts.speaker_template, input_variables=["quote", "excerpt"])
    speaker_follow_up_chain_prompt = PromptTemplate(template=Prompts.speaker_follow_up_template, input_variables=["analysis", "formatted_characters"],  partial_variables={"format_instructions": speaker_parser.get_format_instructions()})
    
    nemotron = ChatOllama(
        model="nemotron-3-nano:30b",
        temperature=0.8,
        repeat_penalty=1.1,
        top_p=0.9,
        top_k=40,
        num_ctx=4096,        # critical
        num_predict=1000,    # cap generation
        num_thread=8,
        microstat=0
    )

    structured_output_model = ChatOllama(
        model=Config.LLM_STRUCTURED_OUTPUT_MODEL,
        temperature=0.4,
        repeat_penalty=1.1,
        top_p=0.7,
        top_k=40,
    )

    quote_mapping = ChatOllama(
        model=Config.LLM_QUOTE_MAPPING_MODEL,
        temperature=0.6,
        repeat_penalty=1.1,
        top_p=0.9,
        top_k=40,
        num_ctx=4096,
        num_predict=1000,
        num_thread=8,
        microstat=0
    )

    chutes = ChatOpenAI(
        openai_api_base="https://llm.chutes.ai/v1",
        openai_api_key=Config.CHUTES_API_KEY,
        model="Qwen/Qwen3-235B-A22B-Instruct-2507-TEE"
    )

    image_chain = image_chain_prompt | structured_output_model | image_prompt_parser
    voice_type_chain = voice_type_chain_prompt | structured_output_model | voice_type_parser
    characters_chain = characters_chain_prompt | structured_output_model | character_parser
    dedupe_characters_chain = dedupe_characters_chain_prompt | structured_output_model | dedupe_parser
    speaker_chain = speaker_chain_prompt | quote_mapping
    speaker_follow_up_chain = speaker_follow_up_chain_prompt | quote_mapping | speaker_parser



def generate_image_prompt(context, passage):
    global image_chain
    result = image_chain.invoke({"large_book_description" : context, "excerpt": passage})
    return result
    
    
def get_voice_type(file_name):
    global voice_type_chain
    result = voice_type_chain.invoke(file_name)
    return result
    
def get_characters(passage):
    global characters_chain
    result = characters_chain.invoke({"excerpt": passage})
    return result.characters


def get_speaker(quote, passage, characters):
    global speaker_chain
    global speaker_follow_up_chain
    analysis = speaker_chain.invoke({"quote": quote, "excerpt": passage}).content
    speaker = speaker_follow_up_chain.invoke({"analysis": analysis, "formatted_characters": characters})
    return speaker


def populate_voice_types(voices):
    mapped_voices = []
    for voice in voices:
        voice_type = get_voice_type(voice).voice_type
        mapped_voices.append({"voice": voice, "voice_type": voice_type})
    return mapped_voices



