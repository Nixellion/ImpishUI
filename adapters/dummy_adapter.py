import requests
from adapters import AdapterBase, AdapterCapability

# region Logger
import os
from debug import get_logger
log = get_logger(os.path.basename(os.path.realpath(__file__)))
# endregion

NAME = "Dummy"

CAPABILITIES = [
    AdapterCapability.TEXT_GENERATION,
    AdapterCapability.SUMMARIZATION
]


class Adapter(AdapterBase):
    """Dummy adapter that sends your prompt back at you after formatting. For developers and testing."""
    ATTRIBUTES = {
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def generate(self, prompt, **kwargs):
        return f"I am a dummy! Back atcha!\n\n{prompt}"

    def summarize_chunk(self, text, **kwargs):
        return "Dummy summary would go right here!"
