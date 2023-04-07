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
log = get_logger("default")
# endregion


def get_all_formats():
    templates = []
    for x in os.listdir(PROMPT_TEMPLATES_DIR):
        name, ext = os.path.splitext(x)
        if ext.lower() == ".jinja2":
            templates.append(name)
    return templates


def load_selected_template_string():
    with open(os.path.join(PROMPT_TEMPLATES_DIR, f"{State.instance.TEMPLATE_NAME}.jinja2"), "r", encoding="utf-8") as f:
        template_string = f.read()
    return template_string


def render_template_string(**context):
    template_string = load_selected_template_string()

    env = Environment(autoescape=True, loader=BaseLoader)

    # region Injecting global variables, functions and filters
    for filter_function in common_filters.enabled_filters:
        env.filters[filter_function.__name__] = filter_function

    global_vars = dict(
        config=config,
        now=datetime.now()
    )

    for func in common_globals.enabled_functions:
        global_vars[func.__name__] = func

    context.update(global_vars)
    # endregion

    rtemplate = env.from_string(template_string)

    return rtemplate.render(**context)


def current_template_string_tokens():
    template_string = load_selected_template_string()
    return count_tokens(template_string)


def tokenize(*args):
    """
    Accepts multple arguments similar to `print` function, and tokenizes resulting text.
    """
    text = " ".join([str(arg) for arg in args])
    if State.instance.TOKENIZER == "nltk":
        tokens = word_tokenize(text)
    else:
        tokenizer = AutoTokenizer.from_pretrained(State.instance.TOKENIZER)
        tokens = tokenizer.tokenize(text)
    return tokens


def untokenize(tokens):
    if State.instance.TOKENIZER == "nltk":
        text = TreebankWordDetokenizer().detokenize(tokens)
    else:
        tokenizer = AutoTokenizer.from_pretrained(State.instance.TOKENIZER)
        text = tokenizer.convert_tokens_to_string(tokens)
    return text


detokenize = untokenize


def count_tokens(*args):
    """
    Accepts multple arguments similar to `print` function, and counts tokens for each of them.
    Casts everything down to string automatically, keep this in mind in case you accidentally pass a "None" or a class value it will be cast with `str()`
    """
    return len(tokenize(*args))


def format_prompt(user_prompt, world_info="", auto_world_info_entities={}, summary="", instruction="", history="", max_tokens=None, max_history_tokens=512):
    """
    This is where the magic happens!
    """
    log.info(f"Formatting prompt ({max_tokens}; {user_prompt}; {world_info}; {summary}; {instruction}): {user_prompt}")

    # We tring history by allowed tokens, from the start
    history = trim_text_by_tokens(history, max_history_tokens)

    # This is the text used to filter which auto_world_info entities are included.
    # If an entity name is included in this text string, then it will be included
    # in the final prompt
    # Filtering is case insensitive (.lower())
    filters = history + user_prompt
    auto_world_info = ""
    for entity, description in auto_world_info_entities.items():
        if filters is None or entity.lower() in filters.lower():
            auto_world_info += entity + ":\n" + description + "\n\n"

    # Here we generate a test prompt to see how many tokens we have left for summary
    test_prompt = render_template_string(
        user_prompt=user_prompt,
        world_info=world_info,
        auto_world_info=auto_world_info,
        instruction=instruction,
        history=history
    )

    # Calculate remaining tokens
    used_tokens = count_tokens(test_prompt)
    tokens_remaining = max_tokens - used_tokens

    # IF we even have summary to work with - now is the time to try and slim it down to
    # fit into remaining tokens. IF we have remaining tokens of course.
    # I'm also adding a minimum number of tokens remaining that is greater than 0,
    # because it's probably not even worth it to try and summarize history down to less
    # than a sane amount of tokens
    MIN_SUMMARY_TOKENS = 15
    if summary is not None and summary.strip() and tokens_remaining < MIN_SUMMARY_TOKENS:
        summary_tokens = count_tokens(summary)
        if summary_tokens >= tokens_remaining:
            log.info(
                f"Prompt with summary is taking too many tokens, trying to summarize it ({summary_tokens} with {max_tokens} limit and {tokens_remaining} remaining)")
            summary = State.instance.SUM_ADAPTER.summarize(summary, tokens_remaining)
            summary_tokens = count_tokens(summary)
            log.info(f"Summarized to: {summary_tokens}")

            used_tokens = count_tokens(current_template_string_tokens(), user_prompt, world_info, summary)
            tokens_remaining = max_tokens - used_tokens
    else:
        if tokens_remaining < MIN_SUMMARY_TOKENS:
            log.warning(f"Summary is NOT added, because not enough tokens remaining: {tokens_remaining}")

    # Selected prompt string is chosen from global selection State inside the function
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
