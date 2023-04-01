from adapters import AdapterBase

import openai
from random import uniform

from configuration import config
TOKEN = config['openai_token']
openai.api_key = TOKEN


class OpenAI_Adapter(AdapterBase):
    # region Attributes that should be in all adapters
    NAME = "OpenAI"
    ATTRIBUTES = {
        "model": {"type": str,
                  "default": "text-davinci-003"},
        "token": {"type": str,
                  "default": "xx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                  "password": True},
    }
    # endregion

    known_models = [
        "gpt-3.5-turbo",
        "text-davinci-003",
        "gpt-3.5-turbo-0301",
        "gpt-4-32k-0314",
        "gpt-4-0314"
    ]

    chat_models = [
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0301",
        "gpt-4-32k-0314",
        "gpt-4-0314"
    ]


    def openai_memory_to_plaintext(self, prompt_messages):
        txt = ""
        for message in self.memory:
            txt += "{}: {}\n\n".format(message['role'], message['content'])
        if txt:
            txt += "user: "
        return txt

    def generate(self, prompt, **kwargs):
        if self.model in OpenAI_Adapter.chat_models:
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}],
                max_tokens=kwargs['max_length'],
                temperature=kwargs['temperature'],
                top_p=kwargs['top_p'],
                frequency_penalty=0,
                presence_penalty=0)
            response = completion.choices[0].message.content

        else:
            if isinstance(prompt, list):
                prompt = self.openai_memory_to_plaintext()
            completion = openai.Completion.create(
                engine=self.model,
                prompt=prompt,
                max_tokens=kwargs['max_length'],
                temperature=kwargs['temperature'],
                top_p=kwargs['top_p'],
                frequency_penalty=0,
                presence_penalty=0)

            response = completion.choices[0].text
        return response
