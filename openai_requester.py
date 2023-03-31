import openai
from random import uniform

from configuration import config
TOKEN = config['openai_token']
openai.api_key = TOKEN

class OpenAI:
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

    def raw_generate(self, prompt, model, max_tokens=512):
        if model in OpenAI.chat_models:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=uniform(0.3, 0.65),
                top_p=uniform(0.6, 1),
                frequency_penalty=0,
                presence_penalty=0)
            response = completion.choices[0].message.content

        else:
            if isinstance(prompt, list):
                prompt = self.openai_memory_to_plaintext()
            completion = openai.Completion.create(
                engine=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=uniform(0.3, 0.65),
                top_p=uniform(0.6, 1),
                frequency_penalty=0,
                presence_penalty=0)

            response = completion.choices[0].text
        return response
