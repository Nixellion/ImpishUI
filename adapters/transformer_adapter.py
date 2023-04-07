from transformers import pipeline, set_seed, AutoModelWithLMHead, AutoTokenizer

from adapters import AdapterBase, AdapterCapability

# region Logger
import os
from debug import get_logger
log = get_logger("adapters")
# endregion

NAME = "Transformer"

CAPABILITIES = [
    AdapterCapability.SUMMARIZATION
]


class Adapter(AdapterBase):
    """
    Hugging face transformers library for summarization. May not work with all models.
    """
    ATTRIBUTES = {
        "huggingface_model":
        {
            "type": str,
            "default": "slauw87/bart_summarisation",
            # tuner007/pegasus_summarizer
            # Kaludi/Quick-Summarization
            # slauw87/bart_summarisation
        },
        "min_length":
        {
            "type": int,
            "default": 100,
            "help": "Some models won't work if this is set too low."
        }
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.loaded_model = None
        self.generator = None

    def summarize_chunk(self, text, max_tokens):
        if self.loaded_model != self.huggingface_model:
            log.info(f"Summarizer loading {self.huggingface_model} model...")
            self.generator = pipeline('summarization', model=self.huggingface_model)
            self.loaded_model = self.huggingface_model

        log.info("Running summarization inference...")
        summary_text = self.generator(text, max_length=max_tokens, min_length=max(max_tokens, self.min_length), do_sample=False)[0]['summary_text']

        return summary_text
