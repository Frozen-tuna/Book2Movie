import base64
import io
import json
import requests
from config import Config

voices = []
session = ""

def get_session():
    global session 
    url = Config.IMAGE_API_URL + "/API/GetNewSession"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={}, headers=headers)
    if response.status_code == 200:
        session = json.loads(response.content.decode("utf-8"))["session_id"]
        return True
    else:
        return False


def generate_image(description, index):
    ### this is for swarmUI. Swarm saves the image to disk and returns the path. Make sure to check model and file location
    print(description)
    url = Config.IMAGE_API_URL + "/API/GenerateText2Image"
    data = {
        "prompt": Config.IMAGE_PREPROMPT + description,
        "negative_prompt": Config.IMAGE_NEGATIVE_PROMPT,
        "model": "juggernautXL_ragnarokBy",
        "seed": -1,
        "steps": 25,
        "width": 1280,
        "height": 720,
        "cfg_scale": 6,
        "sampler": "dpmpp_sde",
        "images": 1,
        "session_id": session
    }

    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=data, headers=headers).json()
    
    location = response['images'][0]

    image_data = requests.get(Config.IMAGE_API_URL + "/" + location, headers=headers)
    
    return image_data.content


def build_images(book):
    global session 
    images = []
    get_session()
    for index, tome in enumerate(book["tomes"]):
        print("Generating image from tome "+str(index + 1) +" of "+str(len(book["tomes"])), end='\r')
        images.append(generate_image(tome["image_prompt"], str(index)))
    print("Finished generating images.")
    return images