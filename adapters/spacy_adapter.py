from adapters import AdapterBase, AdapterCapability

from nlp import extract_persons_from_text

NAME = "Spacy"

CAPABILITIES = [
    AdapterCapability.WORLD_INFO_EXTRACTION
]

class Adapter(AdapterBase):
    """
    Entity recognition using Spacy NLP library. No magic, just good old math. Local, fast, reliable.
    """
    ATTRIBUTES = {
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def extract_world_info(self, text):
        return extract_persons_from_text(text)
