import requests
from adapters import AdapterBase, AdapterCapability

# region Logger
import os
from debug import get_logger
log = get_logger("adapters")
# endregion

NAME = "Dummy"

CAPABILITIES = [
    AdapterCapability.TEXT_GENERATION,
    AdapterCapability.SUMMARIZATION
]


class Adapter(AdapterBase):
    """Dummy adapter that sends your prompt back at you after formatting. For developers and testing."""
    ATTRIBUTES = {
        "test1": 
        {
        "type": str,
        "default": "Default"
        },
        "test2": 
        {
        "type": int,
        "default": 1
        },
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def generate(self, prompt, **kwargs):
        log.info(f"Dummy generate! ({self.__dict__})")
        return f"I am a dummy! Back atcha!\n\n{prompt}\n\n{self.test1} {self.test2}"

    def summarize_chunk(self, text, **kwargs):
        log.info(f"Dummy summarize_chunk ({self.__dict__})")
        return f"Dummy summary would go right here! {self.test1} {self.test2}"
