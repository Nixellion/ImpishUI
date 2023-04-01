class AdapterBase():
    NAME = "OpenAI"
    ATTRIBUTES = {}

    def __init__(self, attrs):
        for key, value in attrs.items():
            # TODO Add validation
            setattr(self, key, value)

    def summarize(self, text):
        pass

    def generate(self, prompt, **kwargs):
        pass