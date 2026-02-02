

from dataclasses import asdict, dataclass, field
import re
from typing import List
from config import Config
import llm
from db_utils import fetch_json, upsert_json
from prompts import Prompts
from rapidfuzz import fuzz


@dataclass
class TrueCharacter():
    name: str
    aliases: List[str]
    type: Prompts.Voice_type = None
    sections: List[int] = field(default_factory=list)
    voice: str = None
    count: int = 0
    lead: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value if self.type else None
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TrueCharacter":
        return cls(
            name=d["name"],
            aliases=d["aliases"],
            type=Prompts.Voice_type(d["type"]),
            sections=d.get("sections", []),
            voice=d.get("voice", None),
            count=d.get("count", 0),
            lead=d.get("lead", False),
        )
    
# Generalized character deduplication/merging function
def merge_characters(characters, strategies):
    """
    Merge characters using a list of strategies. Each strategy is a function that takes (char, other) and returns True if they should be merged.
    """
    combined = []
    used = set()
    for i, char in enumerate(characters):
        if i in used:
            continue
        merged_char = char
        for j, other in enumerate(characters):
            if i == j or j in used:
                continue
            for strategy in strategies:
                if strategy(merged_char, other):
                    # Merge aliases
                    aliases1 = set([a.strip().lower() for a in (merged_char.aliases if merged_char.aliases else [])] if isinstance(merged_char.aliases, list) else [a.strip().lower() for a in (merged_char.aliases.split(",") if merged_char.aliases else [])])
                    aliases2 = set([a.strip().lower() for a in (other.aliases if other.aliases else [])] if isinstance(other.aliases, list) else [a.strip().lower() for a in (other.aliases.split(",") if other.aliases else [])])
                    merged_aliases = aliases1.union(aliases2)
                    merged_aliases.discard(merged_char.name.lower())
                    merged_aliases.discard(other.name.lower())
                    merged_char.aliases = list(merged_aliases)
                    # Merge sections
                    if hasattr(merged_char, 'sections') and hasattr(other, 'sections'):
                        merged_sections = set(getattr(merged_char, 'sections', []))
                        merged_sections.update(getattr(other, 'sections', []))
                        merged_char.sections = list(merged_sections)
                    used.add(j)
                    break
        combined.append(merged_char)
    print(f"characters after merging ({len(strategies)} strategies):", len(combined))
    return combined


def remove_unknown_characters(characters):
    filtered = [char for char in characters if normalize(char.name) != "unknown"]
    return filtered

def unknown_characters():
    unknowns = []
    for Voice_type in Prompts.Voice_type:
        unknown_char = TrueCharacter(
            name = "unknown",
            aliases = [],
            type = Voice_type,
        )
        unknowns.append(unknown_char)
    return unknowns

def narrator():
    narrator = TrueCharacter(
        name = "narrator",
        aliases = ['Used when the speaker is the narrator of the story or for non-dialogue quotes like names of places or objects.'],
        type = Prompts.Voice_type.unknown,
    )
    return narrator

def normalize(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def dedupe_characters(characters):
    global dedupe_characters_chain
    print("Dedupe characters:", characters)
    result = dedupe_characters_chain.invoke({"characters": (",\n ").join(characters)})
    print("raw characters", (" ").join(characters))
    print("Dedupe characters result:", result.characters)
    return result.characters

def populate_characters(book_text, characters=[]):
    if (characters):
        for character in characters:
            character.sections = []
    sections = split_book(" ".join(book_text), Config.SECTION_SIZE)
    for index, section in enumerate(sections):
        print("Collecting characters from section "+str(index+1)+" of "+str(len(sections)), end='\r')
        current_chars = llm.get_characters(section)
        true_chars = []

        for char in current_chars:
            if char.name.lower() == "unknown" and char.aliases.strip() != "":
                true_char = TrueCharacter(
                    name = char.aliases.split(",")[0].strip(),
                    aliases = [],
                    type = char.type,
                    sections=[index]
                )
            else:
                true_char = TrueCharacter(
                    name = char.name,
                    aliases = [alias.strip() for alias in char.aliases.split(",")] if char.aliases else [],
                    type = char.type,
                    sections=[index]
                )
            true_chars.append(true_char)
        characters.extend(true_chars)
    print()
    # Define merge strategies
    def fuzzy_name_and_type(char, other):
        if char.type != other.type:
            return False
        score = fuzz.token_sort_ratio(char.name, other.name)
        return score >= 85

    def name_in_aliases(char, other):
        if char.type != other.type:
            return False
        other_aliases = [a.strip() for a in (other.aliases if other.aliases else [])] if isinstance(other.aliases, list) else [a.strip() for a in (other.aliases.split(",") if other.aliases else [])]
        return char.name in other_aliases

    def prefix_or_substring(char, other):
        if char.type != other.type:
            return False
        name1 = char.name.strip().lower()
        name2 = other.name.strip().lower()
        name1_first = name1.split(" ")[0]
        name2_first = name2.split(" ")[0]
        return name1 != name2 and (name1 == name2_first or name2 == name1_first or name1 in name2 or name2 in name1)

    def same_name_aliases_diff_types(char, other):
        if char.name.strip().lower() == "unknown" or other.name.strip().lower() == "unknown":
            return False
        name1 = char.name.strip().lower()
        name2 = other.name.strip().lower()
        aliases1 = set([a.strip().lower() for a in (char.aliases if char.aliases else [])] if isinstance(char.aliases, list) else [a.strip().lower() for a in (char.aliases.split(",") if char.aliases else [])])
        aliases2 = set([a.strip().lower() for a in (other.aliases if other.aliases else [])] if isinstance(other.aliases, list) else [a.strip().lower() for a in (other.aliases.split(",") if other.aliases else [])])
        return name1 == name2 and aliases1 == aliases2 and char.type != other.type

    def cross_name_alias(char, other):
        # Merge if one's name is in the other's aliases and vice versa, regardless of order, and types match
        if char.type != other.type:
            return False
        name1 = char.name.strip().lower()
        name2 = other.name.strip().lower()
        aliases1 = set([a.strip().lower() for a in (char.aliases if char.aliases else [])] if isinstance(char.aliases, list) else [a.strip().lower() for a in (char.aliases.split(",") if char.aliases else [])])
        aliases2 = set([a.strip().lower() for a in (other.aliases if other.aliases else [])] if isinstance(other.aliases, list) else [a.strip().lower() for a in (other.aliases.split(",") if other.aliases else [])])
        # Check if name1 in aliases2 and name2 in aliases1
        return (name1 in aliases2 or any(name1 in alias for alias in aliases2)) and (name2 in aliases1 or any(name2 in alias for alias in aliases1))

    strategies = [
        fuzzy_name_and_type,
        name_in_aliases,
        prefix_or_substring,
        same_name_aliases_diff_types,
        cross_name_alias
    ]
    unique_characters = merge_characters(characters, strategies)
    unique_characters = remove_unknown_characters(unique_characters)
    return unique_characters


def split_book(book_text, size):
    parts = []
    length = len(book_text)
    index = 0

    while (index + size <= len(book_text)):
        parts.append(book_text[index:index + size])
        # divide by 5 for 20% overlap
        index = index + size - size//5

    parts.append(book_text[index:len(book_text)])
    return parts


def characters_by_section(characters):
    section_map = {}
    for char in characters:
        for section in char.sections:
            if section not in section_map:
                section_map[section] = []
            section_map[section].append(char)

    for section in section_map:
        section_map[section].extend(unknown_characters())
        section_map[section].append(narrator())
    return section_map

def build_surrounding_text(book_text, quote_index, radius):
    start_index = max(0, quote_index - radius)
    end_index = min(len(book_text), quote_index + radius + 1)
    def prepend_newline_if_needed(text):
        if not text:
            return "\n\n"
        elif text.startswith(" "):
            return "\n" + text
        return text
    surrounding_text = " ".join(prepend_newline_if_needed(text) for text in book_text[start_index:end_index])
    return surrounding_text

def find_best_character_match(best_match, characters):
    if best_match.name.lower() == "unknown":
        return best_match
    best_score = 0
    best_character = None
    for char in characters:
        score = fuzz.token_sort_ratio(best_match.name, char.name)
        if score > best_score:
            best_score = score
            best_character = char
        for alias in (char.aliases if isinstance(char.aliases, list) else (char.aliases.split(",") if char.aliases else [])):
            alias_score = fuzz.token_sort_ratio(best_match.name, alias.strip())-15
            if alias_score > best_score:
                best_score = alias_score
                best_character = char
    return best_character

def map_quotes_to_characters(book_text, characters, db):
    mapped_quotes = fetch_json("quotes",  db) or []
    section_characters =  characters_by_section(characters)
    sections = split_book(" ".join(book_text), Config.SECTION_SIZE)
    starting_index = 0

    if len(mapped_quotes) > 0:
        starting_index = len(mapped_quotes)
        print(f"Resuming quote mapping from index {starting_index}")

    for k, quote in enumerate(book_text[starting_index:], start=starting_index):
        print("mapping quote "+str(k)+" of "+str(len(book_text)-1), end='\r')
        new_quote = {}
        if (quote.strip() and (quote.strip()[0] == '"' or quote.strip()[-1] == '"')):
            best_match = None
            for (i, section) in enumerate(sections):
                if quote in section:
                    characters = section_characters.get(i)
                    formatted_characters = "\n".join([f"Name: {char.name}" + (f", Type: {char.type.value}" if char.type else "") + (f", Aliases: {char.aliases}" if char.aliases else "") for char in characters])
                    current_match = llm.get_speaker(quote, build_surrounding_text(book_text, k, 20), formatted_characters)
                    if best_match is None or (best_match.name.lower() == "unknown" and current_match.name != "unknown"):
                        best_match = current_match
            character = find_best_character_match(best_match, characters)
            if len(mapped_quotes) > 0:
                last_mapped_quote = mapped_quotes[-1]
                if last_mapped_quote["character"]["name"] == character.name:
                    last_mapped_quote["quote"] += " " + quote
                else:
                    mapped_quotes.append({"quote": quote, "character": {"name": character.name, "type": character.type, "aliases": (character.aliases if hasattr(character, "aliases") and character.aliases is not None else [])}})
            else:
                mapped_quotes.append({"quote": quote, "character": {"name": character.name, "type": character.type, "aliases": (character.aliases if hasattr(character, "aliases") and character.aliases is not None else [])}})
        else:
            #adding for empty noise. Makes final product a bit nicer.
            mapped_quotes.append({"quote": quote, "character": {"name": "narrator", "type": Prompts.Voice_type.unknown, "aliases": []}})
        if k % 10 == 0:
            upsert_json("quotes", mapped_quotes, db)
    print()
    return mapped_quotes