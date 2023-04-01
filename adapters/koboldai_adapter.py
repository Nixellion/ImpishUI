import requests
from adapters import AdapterBase


class KoboldAI_Adapter(AdapterBase):
    NAME = "KoboldAI"
    ATTRIBUTES = {
        "url": {
            "type": str,
            "default": "http://127.0.0.1:5000"
        }
    }

    def generate(self, prompt, **kwargs):
        json_data = kwargs
        json_data['prompt'] = prompt
        response = requests.post(self.url + "/api/v1/generate", json=json_data)
        print(response.text)
        response = response.json()['results'][0]['text']