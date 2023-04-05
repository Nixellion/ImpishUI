import os
from enum import Enum
from jinja2 import Environment, BaseLoader
from nltk.tokenize import word_tokenize
from transformers import AutoTokenizer, LlamaTokenizer
from paths import PROMPT_TEMPLATES_DIR

from database import State

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
    return rtemplate.render(**context)

def current_template_string_tokens():
    template_string = load_selected_template_string()
    return count_tokens(template_string)


def count_tokens(text):
    if State.TOKENIZER == "nltk":
        return len(word_tokenize(text))
    else:
        tokenizer = AutoTokenizer.from_pretrained(State.TOKENIZER)
        tokens = tokenizer.tokenize(text)
        return len(tokens)

def count_used_tokens(*args):
    all_text = "".join([str(arg) for arg in args])
    return count_tokens(all_text)

def format_prompt(user_prompt, world_info="", summary="", instruction="", max_tokens=None):
    """
    This is where the magic happens!
    """
    log.info(f"Formatting prompt ({max_tokens}; {user_prompt}; {world_info}; {summary}; {instruction}): {user_prompt}")
    used_tokens = count_used_tokens(current_template_string_tokens(), user_prompt, world_info)
    tokens_remaining = max_tokens - used_tokens

    if summary.strip():
        summary_tokens = count_tokens(summary)
        if summary_tokens >= tokens_remaining:
            log.info(f"Prompt with summary is taking too many tokens, trying to summarize it ({summary_tokens} with {max_tokens} limit and {tokens_remaining} remaining)")
            summary = State.SUM_ADAPTER.summarize(summary, tokens_remaining)
            summary_tokens = count_tokens(summary)
            log.info(f"Summarized to: {summary_tokens}")

            used_tokens = count_used_tokens(current_template_string_tokens(), user_prompt, world_info, summary)
            tokens_remaining = max_tokens - used_tokens
            if world_info.strip() and used_tokens > max_tokens:
                log.info(f"Still too many tokens ({used_tokens} of {max_tokens}), summarizing World Info...")
                world_info = State.SUM_ADAPTER.summarize(summary, count_tokens(world_info) - (abs(used_tokens - max_tokens) * 1.25))

    # Selected scring is chosen from global selection State
    prompt = render_template_string(
        user_prompt=user_prompt,
        world_info=world_info,
        summary=summary,
        instruction=instruction
    )

    tokens_used = count_tokens(prompt)

    log.info(f"Formatted prompt: {prompt}")
    log.info(f"Formatted prompt tokens {tokens_used} out of {max_tokens} allowed used.")
    return prompt

