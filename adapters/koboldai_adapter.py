import requests
from adapters import AdapterBase, AdapterCapability
from prompter import format_prompt, PromptFormat

# region Logger
import os
from debug import get_logger
log = get_logger(os.path.basename(os.path.realpath(__file__)))
# endregion

NAME = "KoboldAI"

CAPABILITIES = [
    AdapterCapability.TEXT_GENERATION,
    AdapterCapability.SUMMARIZATION
]


class Adapter(AdapterBase):
    ATTRIBUTES = {
        "url": {
            "type": str,
            "default": "http://127.0.0.1:5000"
        },
        "prompt_format":
        {
            "type": PromptFormat,
            "default": PromptFormat.INSTRUCT_LLAMA
        },
        "temperature":
        {
            "type": float,
            "default": 0.5,
            "min": 0.0,
            "max": 1.0
        }
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def generate(self, prompt, **kwargs):
        log.info(f"KoboldAI Prompt: {prompt}")
        log.info(f"-" * 80)

        # Default values
        json_data = {
            "prompt": prompt,
            "temperature": 0.5,
            "top_p": 0.9,
            "max_context_length": 2048-512,
            "max_length": 512,
            "rep_pen": 1,
            "rep_pen_range": 1024,
            "rep_pen_slope": 0.7,
            "frmttriminc": True
        }

        # Update with incoming values
        json_data.update(kwargs)

        # Add prompt
        json_data['prompt'] = prompt

        response = requests.post(self.url + "/api/v1/generate", json=json_data)
        log.info(response.text)
        log.info(f"-" * 80)

        response = response.json()['results'][0]['text']
        return response

    def summarize_chunk(self, text, **kwargs):
        log.info(f"KoboldAI Summarize: {text}")
        log.info(f"-" * 80)

        prompt = format_prompt(text, instruction="Summarize")
        json_data = kwargs
        json_data['prompt'] = prompt
        response = requests.post(self.url + "/api/v1/generate", json=json_data)
        log.info(response.text)
        response = response.json()['results'][0]['text']
        log.info(f"-" * 80)

        return response
