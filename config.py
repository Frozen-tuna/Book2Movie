class Config:
    LLM_URL = "http://localhost:5000"
    LLM_CHARACTER_EXTRA_INSTRUCTIONS = """This story is told in first person. The narrator is one of the characters in the story and refers to themselves as "I" and "me". The narrator is the same character as Dr. Watson."""
    LLM_STRUCTURED_OUTPUT_MODEL = "gemma3:27b-it-qat"
    LLM_QUOTE_MAPPING_MODEL = "mistral-small3.2:24b"
    CHUTES_API_KEY = "your_chutes_api_key_here"
    TTS_API_URL = "http://localhost:8880"
    MAX_TTS_LENGTH = 600
    TTS_SPEED = 0.9
    IMAGE_API_URL = "http://localhost:8188"
    NARRATOR_VOICE = "male_onyx"
    IMAGE_MODEL = "realDream_zitV3.safetensors"
    IMAGE_PREPROMPT = "highly detailed, masterpiece, futurisitc, high resolution, industrial era, english, movie still, dramatic lighting, cinematic, 8k, "
    IMAGE_NEGATIVE_PROMPT = "lowres, bad anatomy, error body parts, error face parts, deformed, blurry, disfigured, poorly drawn, mutation, mutated, ugly, disgusting, blurry, fuzzy"
    BOOK_TITLE = "Sherlock Holmes: Study in Scarlet"
    BOOK_DESCRIPTION = """A Study in Scarlet is Arthur Conan Doyle's first Sherlock Holmes novel, introducing the brilliant but eccentric detective and his chronicler, Dr. Watson, as they investigate a baffling murder in London, uncovering a tale of deadly revenge rooted in a tragic past in America involving Mormon persecution and forbidden love, with the killer leaving cryptic clues, like the word "RACHE" (German for revenge) written in blood, for Holmes to unravel using his unique powers of deduction."""
    IMAGE_PROMPT_ASSIST = """The visuals have a strong film noir aesthetic, inspired by a blend of early industrial era and English themes.
    Outdoor settings should feature foggy, dimly lit environments with cobblestone streets, wrought iron fences, and gas lamps casting long shadows. The architecture should reflect Victorian and Edwardian styles, with intricate brickwork, steep gables, and ornate details. The exception is the garden itself.
    Indoor scenes should be characterized by dark wood paneling, heavy draperies, and antique furnishings, creating a sense of mystery and intrigue. Use a muted color palette with deep blues, grays, and sepia tones to enhance the moody atmosphere.
    Kids should be described as teenagers or young adults. Adults should be described as middle aged or older."""
    #Summary width is the number of surrounding tomes to include when generating a summary for a given tome. Radius.
    SUMMARY_RADIUS = 2
    #Splits the book into sections of approximately this many characters when analyzing for characters. Larger will be more accurate with more important characters. 
    #Smaller will catch more minor characters with less accuracy. Larger will also risk response parsing errors.
    SECTION_SIZE = 8000