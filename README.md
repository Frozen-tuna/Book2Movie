# Book2Movie

A local-first script to process ebooks into slideshows or movies using several types of generative AI.

---
[![Sherlock Holmes - A Study In Scarlet Youtube Output](https://img.youtube.com/vi/ugKktBD26ls/0.jpg)](https://www.youtube.com/watch?v=ugKktBD26ls)
---

## Requirements

- [conda](https://docs.conda.io/en/latest/)
- [portaudio19-dev](http://www.portaudio.com/)
- [ffmpeg](https://ffmpeg.org/)
- [ComfyUI](https://github.com/Comfy-Org/ComfyUI)
- [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)

---

## Installation

```sh
conda create --name book2movie python=3.11
pip install -r requirements.txt
```

---

## Usage

### Basic Processing

```sh
python main.py data/AStudyInScarlet.epub 4 17
```

### ComfyUI Setup

```sh
python main.py --listen 0.0.0.0 --port 8188
```

---

## Kokoro-FastAPI Voice Mapping

- For best results, prepend all models in Kokoro-FastAPI with `male`, `female`, and at least one `machine`.
- Leave `af_heart.pt` as is (it's hardcoded).
- This improves voice mapping so male characters are more likely to use male voices, etc. Current voice types are "Masculine", "Feminine", "Machine", and "Unknown".

---

## Ollama (for 24GB VRAM users)

```sh
ollama pull gemma3:27b-it-qat
ollama pull mistral-small3.2:24b
```

- **Gemma3**: Best for structured outputting a list of characters.
- **Mistral-small3.2**: Slightly better for mapping characters to quotes.
- Model names are in the config.

---