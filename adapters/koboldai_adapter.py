import requests
from adapters import AdapterBase, AdapterCapability
from prompter import format_prompt

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
        "temperature":
        {
            "type": float,
            "default": 0.5,
            "min": 0.0,
            "max": 1.0
        },
        "top_p": {"type": float, "default": 0.9},
        "max_context_length": {"type": int, "default": 2048},
        "max_length": {"type": int, "default": 512},
        "rep_pen": {"type": float, "default": 1},
        "rep_pen_range": {"type": int, "default": 1024},
        "rep_pen_slope": {"type": float, "default": 0.7},
        "frmttriminc": {"type": bool, "default": True}
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def get_max_tokens(self):
        return self.max_context_length - self.max_length

    def generate(self, prompt, **kwargs):
        log.info(f"KoboldAI Prompt: {prompt}")
        log.info(f"-" * 80)

        # Default values
        json_data = {
            "prompt": prompt,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_context_length": self.max_context_length - self.max_length,
            "max_length": self.max_length,
            "rep_pen": self.rep_pen,
            "rep_pen_range": self.rep_pen_range,
            "rep_pen_slope": self.rep_pen_slope,
            "frmttriminc": self.frmttriminc
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

    def summarize_chunk(self, text, max_tokens, **kwargs):
        log.info(f"KoboldAI Summarize: {text} to {max_tokens}")
        log.info(f"-" * 80)

        prompt = format_prompt(text, instruction="Summarize", max_tokens=max_tokens)
        json_data = kwargs
        json_data['prompt'] = prompt
        response = requests.post(self.url + "/api/v1/generate", json=json_data)
        log.info(response.text)
        response = response.json()['results'][0]['text']
        log.info(f"-" * 80)

        return response
