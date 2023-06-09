import time
import traceback
import os
from enum import Enum
import importlib
from paths import APP_DIR

import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize

from prompter import count_tokens

# region Logger
import os
from debug import get_logger
log = get_logger("adapters")
# endregion


class AdapterBase():
    # NOTE This was supposed to help reduce memory consumption, to only create one instance per adapter type. However this complicated handling of settings, so, at least for now, back to non-singletons
    # # region Singleton
    # def __new__(cls):
    #     if not hasattr(cls, 'instance'):
    #         log.info("Adapter initializing...")
    #         cls.instance = super(AdapterBase, cls).__new__(cls)
    #     return cls.instance
    # # endregion

    def __init__(self, attrs=None):
        self.set_settings()

    def get_max_tokens(self):
        return 2048-512

    def set_settings(self, attrs=None):
        if attrs is not None:
            log.debug(f"Set settings: {attrs}")
        else:
            log.debug("Set default adapter settings.")
            
        new_attrs = {}
        for key, value in self.ATTRIBUTES.items():
            new_attrs[key] = value["default"]

        if attrs is not None:
            new_attrs.update(attrs)

        for key, value in new_attrs.items():
            setattr(self, key, value)

    def summarize_chunk(self, text, max_tokens):
        pass

    def generate(self, prompt, **kwargs):
        pass

    def extract_world_info(self, text):
        pass
    
    def summarize(self, text_to_summarize, max_tokens=150, tokens_percent=None, min_tokens=100):
        """
        tokens_percent will override max_tokens and calculate it based on percentage.
        """
        text_to_summarize_tokens = count_tokens(text_to_summarize)
        if tokens_percent:
            max_tokens = max(min_tokens, int(text_to_summarize_tokens * tokens_percent))

        # It is very possible that text to summarize will be smaller than max_tokens, in which case - return as is.
        if text_to_summarize_tokens <= max_tokens:
            return text_to_summarize

        max_tokens = int(min(max_tokens, text_to_summarize_tokens))
        
        summary = None

        # Split text into chunks that can fit into most models and summarize each chunk
        try:
            chunks = [self.convert_to_detokenized_text(i) for i in self.break_up_text_to_chunks(text_to_summarize)]
            tokens_per_chunk = int(max_tokens / len(chunks))
            summary = ""
            print(f"Chunks: {len(chunks)}")
            for i, chunk in enumerate(chunks):
                log.debug(f"{i}: {chunk}")
                summary_text = self.summarize_chunk(chunk, max_tokens=tokens_per_chunk)
                if not summary_text:
                    log.warning(f"Summarize chunk returned empty response for this chunk: '{chunk}'")
                log.debug(summary_text)
                summary += summary_text if summary_text else ""
                summary += "\n"
                time.sleep(0.5)
        except Exception as e:
            raise Exception(str(e) + traceback.format_exc())

        # Iteratively try to keep summarizing the text until it fits into the max tokens, but return as is if it's impossible
        retries = 0
        max_retries = 1
        success = False
        while not success and retries < max_retries:
            if count_tokens(summary) <= max_tokens:
                break

            summary = self.summarize_chunk(summary, max_tokens=max_tokens)
            retries += 1

        return summary

    def word_tokenize(self, text):
        return word_tokenize(text)

    def break_up_text(self, tokens, chunk_size, overlap_size):
        if len(tokens) <= chunk_size:
            yield tokens
        else:
            chunk = tokens[:chunk_size]
            yield chunk
            yield from self.break_up_text(tokens[chunk_size - overlap_size:], chunk_size, overlap_size)

    def break_up_text_to_chunks(self, text, chunk_size=1000, overlap_size=250):
        tokens = self.word_tokenize(text)
        return list(self.break_up_text(tokens, chunk_size, overlap_size))

    def convert_to_detokenized_text(self, tokenized_text):
        prompt_text = " ".join(tokenized_text)
        prompt_text = prompt_text.replace(" 's", "'s")
        return prompt_text
    
    def coherence_score(self, text):
        pass

    def unload(self):
        """
        TODO: Create adapter unloading functionality for things that have a lot in memory, like tokenizers. IF NEEDED, maybe not? Will Python be able to handle it?
        """
        pass

    def generate_character(self):
        pass


class AdapterCapability(Enum):
    TEXT_GENERATION = 10
    SUMMARIZATION = 20
    WORLD_INFO_EXTRACTION = 30
    TEXT_COHERENCE_SCORING = 40
    CHARACTER_GENERATOR = 50  # Reserverd for downloading character info from various wikis, roleplaying websites, etc, or for dynamically generating them
    # PROMPT_GENERATOR = 60  # Reserved for downloading prompts from different prompt websites, or for dynamically generating them

def capability_title(capability):
    return capability.name.replace("_", " ").title()


available_adapters = {}

files = os.listdir(os.path.join(APP_DIR, "adapters"))
for file in files:
    name, ext = os.path.splitext(file)
    if not name.startswith("__") and ext.lower() == ".py":
        log.info(f"Loading adapter from file: {file}")
        try:
            adapter_module = importlib.import_module(f"adapters.{name}")
            log.info(f"Adapter loaded: {adapter_module.NAME}")
            available_adapters[name] = adapter_module
        except Exception as e:
            log.error(e, exc_info=True)
