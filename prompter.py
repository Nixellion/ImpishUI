import os
from enum import Enum
from jinja2 import Environment, BaseLoader
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
from transformers import AutoTokenizer, LlamaTokenizer
from configuration import config
from datetime import datetime, timedelta
from paths import PROMPT_TEMPLATES_DIR
from utilities.jinja_utils import common_filters, common_globals

from state import State

# region Logger
from debug import get_logger
log = get_logger(os.path.basename(os.path.realpath(__file__)))
# endregion


def get_all_formats():
    templates = []
    for x in os.listdir(PROMPT_TEMPLATES_DIR):
        name, ext = os.path.splitext(x)
        if ext.lower() == ".jinja2":
            templates.append(name)
    return templates


def load_selected_template_string():
    with open(os.path.join(PROMPT_TEMPLATES_DIR, f"{State.TEMPLATE_NAME}.jinja2"), "r", encoding="utf-8") as f:
        template_string = f.read()
    return template_string


def render_template_string(**context):
    template_string = load_selected_template_string()
    rtemplate = Environment(loader=BaseLoader).from_string(template_string)

    # region Injecting global variables, functions and filters
    for filter_function in common_filters.enabled_filters:
        rtemplate.filters[filter_function.__name__] = filter_function

    global_vars = dict(
        config=config,
        now=datetime.now()
    )

    for func in common_globals.enabled_functions:
        global_vars[func.__name__] = func

    context.update(global_vars)
    # endregion
    
    return rtemplate.render(**context)


def current_template_string_tokens():
    template_string = load_selected_template_string()
    return count_tokens(template_string)


def tokenize(*args):
    """
    Accepts multple arguments similar to `print` function, and tokenizes resulting text.
    """
    text = " ".join([str(arg) for arg in args])
    if State.TOKENIZER == "nltk":
        tokens = word_tokenize(text)
    else:
        tokenizer = AutoTokenizer.from_pretrained(State.TOKENIZER)
        tokens = tokenizer.tokenize(text)
    return tokens


def untokenize(tokens):
    if State.TOKENIZER == "nltk":
        text = TreebankWordDetokenizer().detokenize(tokens)
    else:
        tokenizer = AutoTokenizer.from_pretrained(State.TOKENIZER)
        text = tokenizer.convert_tokens_to_string(tokens)
    return text


detokenize = untokenize


def count_tokens(*args):
    """
    Accepts multple arguments similar to `print` function, and counts tokens for each of them.
    Casts everything down to string automatically, keep this in mind in case you accidentally pass a "None" or a class value it will be cast with `str()`
    """
    return len(tokenize(*args))


def format_prompt(user_prompt, world_info="", auto_world_info="", summary="", instruction="", history="", max_tokens=None, max_history_tokens=512):
    """
    This is where the magic happens!
    """
    log.info(f"Formatting prompt ({max_tokens}; {user_prompt}; {world_info}; {summary}; {instruction}): {user_prompt}")
    history = trim_text_by_tokens(max_history_tokens)
    test_prompt = render_template_string(
        user_prompt=user_prompt,
        world_info=world_info,
        auto_world_info=auto_world_info,
        instruction=instruction,
        history=history
    )

    used_tokens = count_tokens(test_prompt)

    tokens_remaining = max_tokens - used_tokens

    if summary.strip():
        summary_tokens = count_tokens(summary)
        if summary_tokens >= tokens_remaining:
            log.info(
                f"Prompt with summary is taking too many tokens, trying to summarize it ({summary_tokens} with {max_tokens} limit and {tokens_remaining} remaining)")
            summary = State.SUM_ADAPTER.summarize(summary, tokens_remaining)
            summary_tokens = count_tokens(summary)
            log.info(f"Summarized to: {summary_tokens}")

            used_tokens = count_tokens(current_template_string_tokens(), user_prompt, world_info, summary)
            tokens_remaining = max_tokens - used_tokens
            if world_info.strip() and used_tokens > max_tokens:
                log.info(f"Still too many tokens ({used_tokens} of {max_tokens}), summarizing World Info...")
                world_info = State.SUM_ADAPTER.summarize(summary, count_tokens(
                    world_info) - (abs(used_tokens - max_tokens) * 1.25))

    # Selected scring is chosen from global selection State
    prompt = render_template_string(
        user_prompt=user_prompt,
        world_info=world_info,
        auto_world_info=auto_world_info,
        summary=summary,
        instruction=instruction,
        history=history
    )

    tokens_used = count_tokens(prompt)

    log.info(f"Formatted prompt: {prompt}")
    log.info(f"Formatted prompt tokens {tokens_used} out of {max_tokens} allowed used.")
    return prompt


def trim_text_by_tokens(text, max_tokens, from_start=True):
    if isinstance(text, list):
        text = " ".join(text)

    tokens = tokenize(text)
    if len(tokens) <= max_tokens:
        return text

    # Adding one just in case to make sure we are UNDER the limit. Maybe it's rudimentary.
    trim_tokens_count = len(tokens) - max_tokens + 1

    if from_start:
        trimmed = detokenize(tokens[trim_tokens_count:])
    else:
        trimmed = detokenize(tokens[:len(tokens) - trim_tokens_count])

    return trimmed
