import base64
import io
import json
import uuid
import requests
import websocket
from config import Config
import urllib.request
import urllib.parse

from db_utils import fetch_json, upsert_json
from llm import generate_image_prompt

client_id = str(uuid.uuid4())

prompt_text = """
{
    "39": {
        "inputs": {
            "clip_name": "qwen_3_4b.safetensors",
            "type": "lumina2",
            "device": "default"
        },
        "class_type": "CLIPLoader",
        "_meta": {
            "title": "Load CLIP"
        }
    },
    "40": {
        "inputs": {
            "vae_name": "ae.safetensors"
        },
        "class_type": "VAELoader",
        "_meta": {
            "title": "Load VAE"
        }
    },
    "41": {
        "inputs": {
            "width": 1280,
            "height": 720,
            "batch_size": 1
        },
        "class_type": "EmptySD3LatentImage",
        "_meta": {
            "title": "EmptySD3LatentImage"
        }
    },
    "42": {
        "inputs": {
            "conditioning": [
                "45",
                0
            ]
        },
        "class_type": "ConditioningZeroOut",
        "_meta": {
            "title": "ConditioningZeroOut"
        }
    },
    "43": {
        "inputs": {
            "samples": [
                "44",
                0
            ],
            "vae": [
                "40",
                0
            ]
        },
        "class_type": "VAEDecode",
        "_meta": {
            "title": "VAE Decode"
        }
    },
    "44": {
        "inputs": {
            "seed": 795739787106215,
            "steps": 9,
            "cfg": 1,
            "sampler_name": "res_multistep",
            "scheduler": "simple",
            "denoise": 1,
            "model": [
                "47",
                0
            ],
            "positive": [
                "45",
                0
            ],
            "negative": [
                "42",
                0
            ],
            "latent_image": [
                "41",
                0
            ]
        },
        "class_type": "KSampler",
        "_meta": {
            "title": "KSampler"
        }
    },
    "45": {
        "inputs": {
            "text": {prompt},
            "clip": [
                "39",
                0
            ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": {
            "title": "CLIP Text Encode (Prompt)"
        }
    },
    "46": {
        "inputs": {
            "unet_name": "{image_model}",
            "weight_dtype": "default"
        },
        "class_type": "UNETLoader",
        "_meta": {
            "title": "Load Diffusion Model"
        }
    },
    "47": {
        "inputs": {
            "shift": 3,
            "model": [
                "46",
                0
            ]
        },
        "class_type": "ModelSamplingAuraFlow",
        "_meta": {
            "title": "ModelSamplingAuraFlow"
        }
    },
    "save_image_websocket_node": {
        "class_type": "SaveImageWebsocket",
        "inputs": {
            "images": [
                "43",
                0
            ]
        }
    }
}
"""


def queue_prompt(prompt):
    global client_id
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request(Config.IMAGE_API_URL + "/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())
    
def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(Config.IMAGE_API_URL + "/view?{}".format(url_values)) as response:
        return response.read()

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_image = {}
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break #Execution is done
                    else:
                        current_node = data['node']
        else:
            if current_node == 'save_image_websocket_node':
                output_image = base64.b64encode(out[8:]).decode("utf-8")


    return output_image


def build_images(tomes, av_db):
    global client_id 
    images = fetch_json("images", av_db) or []
    starting_index = 0

    if len(images) > 0:
        starting_index = len(images)
        print(f"Resuming generating images from index {starting_index}")

    ws = websocket.WebSocket()
    ws.connect(f"ws://localhost:8188/ws?clientId={client_id}")

    for index, tome in enumerate(tomes[starting_index:], start=starting_index):
        print("Generating image from tome "+str(index) +" of "+str(len(tomes)-1), end='\r')
        prompt_template = prompt_text
        escaped_prompt = json.dumps(Config.IMAGE_PREPROMPT + tome["image_prompt"])
        prompt_template = prompt_template.replace("{prompt}", escaped_prompt)
        prompt_template = prompt_template.replace("{image_model}", Config.IMAGE_MODEL)
        final_prompt = json.loads(prompt_template)
        images.append(get_images(ws, final_prompt))
        if index % 5 == 0:
            upsert_json("images", images, av_db)

    print("Finished generating images.")
    ws.close()
    return images



def populate_tome_image_prompts(tomes, av_db):
    debug_image_prompts = []
    for index, tome in enumerate(tomes):
        if not tome.get("image_prompt"):
            exerpt = ""
            for i in range(Config.SUMMARY_RADIUS*2 + 1):
                if (index + i >= 0) and (index + i < len(tomes)):
                    exerpt += tomes[index + i]["text"]

            print("Generating image prompt from tome "+str(index)+" of "+str(len(tomes)-1), end='\r')
            tome["image_prompt"] = generate_image_prompt(exerpt, tome["text"]).prompt
            debug_image_prompts.append({"exerpt": exerpt, "image_prompt": tome["image_prompt"]})
            if index % 10 == 0:
                upsert_json("tomes", tomes, av_db)
    print()
    with open("data/debug_image_prompts.json", "w") as f:
        json.dump(debug_image_prompts, f, indent=2)
    print()
    return tomes