from adapters import AdapterBase, AdapterCapability
import openai


# region Attributes that should be in all adapters
NAME = "OpenAI"

CAPABILITIES = [
    AdapterCapability.TEXT_GENERATION,
    AdapterCapability.SUMMARIZATION
]
# endregion


class Adapter(AdapterBase):
    ATTRIBUTES = {
        "model": {"type": str,
                  "default": "text-davinci-003"},
        "token": {"type": str,
                  "default": "xx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                  "password": True},
    }
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

    def __init__(self, attrs=None):
        super().__init__(attrs)
        openai.api_key = self.token

    def openai_memory_to_plaintext(self, prompt_messages):
        txt = ""
        for message in self.memory:
            txt += "{}: {}\n\n".format(message['role'], message['content'])
        if txt:
            txt += "user: "
        return txt

    def generate(self, prompt, **kwargs):
        if self.model in self.chat_models:
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}],
                max_tokens=kwargs.get('max_length', 512),
                temperature=kwargs.get('temperature', 0.5),
                top_p=kwargs.get('top_p', 0.9),
                frequency_penalty=0,
                presence_penalty=0)
            response = completion.choices[0].message.content

        else:
            if isinstance(prompt, list):
                prompt = self.openai_memory_to_plaintext()
            completion = openai.Completion.create(
                engine=self.model,
                prompt=prompt,
                max_tokens=kwargs.get('max_length', 512),
                temperature=kwargs.get('temperature', 0.5),
                top_p=kwargs.get('top_p', 0.9),
                frequency_penalty=0,
                presence_penalty=0)

            response = completion.choices[0].text
        return response

    def summarize_chunk(self, text, max_tokens, **kwargs):
        return self.generate(f"Summarize the following text:\n{text}")
