import re
import PyPDF2
import nltk
import ebooklib
from ebooklib import epub
from ebooklib.utils import debug
nltk.download('punkt')
nltk.download('punkt_tab')



def read_pdf(file_path, start_page, end_page):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        pdf_text = ""
        num_pages = min(end_page, len(reader.pages))
        start = max(0, start_page)
        for page_num in range(start, num_pages):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            page_text = re.sub(r'\n', r' ', page_text)
            page_text = page_text.replace('“', '"').replace('”', '"')
            if pdf_text and not pdf_text.endswith(' '):
                pdf_text += ' '
            pdf_text += page_text
        return pdf_text

def read_epub(file_path, start_page, end_page):
    book = epub.read_epub(file_path)
    epub_text = ""
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    for index in range(start_page-1, min(end_page, len(items))):
        item = items[index]
        content = item.get_content().decode('utf-8')
        content = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE).group(1)
        text = re.sub(r'</?(span|div|em|a)[^>]*>', '', content)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = re.sub(r'\s+', ' ', text)

        UNICODE_REPLACEMENTS = {
            ord('“'): '"',
            ord('”'): '"',
            ord('‘'): "'",
            ord('’'): "'",
            ord('—'): '-',
            ord('–'): '-',
            ord('…'): '...',
            ord('•'): '*',
            ord('\u00e6'): 'ae',
            ord('\u00a0'): ' ',
        }
        text = text.translate(UNICODE_REPLACEMENTS)
        if epub_text and not epub_text.endswith(' '):
            epub_text += ' '
        epub_text += text
    return epub_text


def text_to_sentences(text):
    sentences = nltk.sent_tokenize(text)
    return sentences

def build_quotes(sentences):
    quotes = []
    current_group = []
    in_quote = False

    for dirty_sentence in sentences:
        sentence = dirty_sentence.lstrip(r"^!@#$%^&*()_+-=[]{}|;:',.<>/?`~ ")
        if '"' in sentence:
            sentence = sentence.strip()
            #print(f"Processing sentence: {sentence}")
            ## Start and end quote in same sentence
            if sentence[0] == '"' and sentence[len(sentence) - 1] == '"' and sentence.count('"') == 2:
                quotes.append(' '.join(current_group))
                current_group = []
                quotes.append(sentence);
            ## Start quote
            elif (sentence[0] == '"' and sentence.count('"') == 1):
                quotes.append(' '.join(current_group))
                current_group = []
                current_group.append(sentence)
                in_quote = True
            ## End quote
            elif (sentence[len(sentence) - 1] == '"' and sentence.count('"') == 1):
                current_group.append(sentence)
                quotes.append(' '.join(current_group))
                current_group = []
                in_quote = False
            ## One quote somewhere in the sentence
            elif sentence.count('"') == 1:
                if in_quote:
                    left_half = sentence.split('"')[0]
                    right_half = sentence.split('"')[1]
                else:
                    left_half, sep, right_half = sentence.partition('"')
                    right_half = sep + right_half
                
                current_group.append(left_half)
                quotes.append(' '.join(current_group))
                current_group = []
                current_group.append(right_half)
                in_quote = not in_quote
            elif sentence[0] == '"' and sentence.count('"') == 2:
                parts = sentence.split('"')
                quotes.append(' '.join(current_group))
                current_group = []
                quotes.append('"' + parts[1] + '"')
                current_group = [parts[2]]
            elif sentence[0] != '"' and sentence[len(sentence) - 1] != '"':
                if '" "' in sentence:
                    parts = sentence.split('"')
                    current_group.append(parts[0])
                    quotes.append(' '.join(current_group))
                    current_group = [parts[2]]
                else:
                    parts = sentence.split('"')
                    current_group.append(parts[0])
                    quotes.append(' '.join(current_group))
                    quotes.append('"' + parts[1] + '"')
                    current_group = [parts[2]]
            elif sentence.count('"') == 4:
                parts = sentence.split('"')
                for part in parts:
                    if part.strip() == '':
                        continue
                    else:
                        if current_group != []:
                            quotes.append(' '.join(current_group))
                            current_group = []
                        if (quotes[0] == ' '):
                            quotes.append(part.strip())
                        else:
                            quotes.append('"' + part.strip() + '"')
            elif sentence[0] != '"' and sentence[len(sentence) - 1] == '"' and sentence.count('"') == 2:
                parts = sentence.split('"')
                current_group.append(parts[0])
                quotes.append(' '.join(current_group))
                quotes.append('"' + parts[1] + '"')
                current_group = []
            elif sentence[0] == '"' and sentence[len(sentence) - 1] != '"' and (sentence.count('"') == 3 or sentence.count('"') == 5):
                parts = sentence.split('"')
                if current_group != []:
                    quotes.append(' '.join(current_group))
                    current_group = []
                quotes.append('"' + parts[1] + '"')
                if parts[2].strip() != '':
                    quotes.append(parts[2])
                if (len(parts) == 4):
                    current_group = [parts[3]]
                elif (len(parts) == 6):
                    quotes.append('"' + parts[3] + '"')
                    if parts[4].strip() != '':
                        quotes.append(parts[4])
                    current_group = [parts[5]]
                in_quote = True
            elif sentence[0] != '"' and sentence[len(sentence) - 1] == '"' and (sentence.count('"') == 3 or sentence.count('"') == 5):
                parts = sentence.split('"')
                current_group.append(parts[0])
                quotes.append(' '.join(current_group))
                if parts[1].strip() != '':
                    quotes.append(parts[1])
                quotes.append('"' + parts[2] + '"')
                if (len(parts) == 6):
                    if parts[3].strip() != '':
                        quotes.append(parts[3])
                    quotes.append('"' + parts[4] + '"')
                current_group = []
                in_quote = False
            elif sentence.count('"') == 6:
                parts = sentence.split('"')
                if current_group != []:
                    quotes.append(' '.join(current_group))
                    current_group = []
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        if part.strip():
                            if current_group:
                                current_group.append(part.strip())
                                quotes.append(' '.join(current_group))
                                current_group = []
                            else:
                                quotes.append(part.strip())
                    else:
                        quotes.append('"' + part.strip() + '"')
            else:
                print(sentence)
                print("unaccounted quote structure detected. Adding verbatim.")
                quotes.append(' '.join(current_group))
                current_group = []
                quotes.append(sentence);
        else:
            current_group.append(sentence)


    if current_group:
        quotes.append(' '.join(current_group))

    return quotes


def read(book_name, start_page, end_page):
    text = ""
    if book_name.endswith(".pdf"):
        text = read_pdf(book_name, start_page, end_page)
    elif book_name.endswith(".epub"):
        text = read_epub(book_name, start_page, end_page)

    sentences = text_to_sentences(text.replace("      ", " ").replace("    ", " "))
    quotes = build_quotes(sentences)
    return quotes
