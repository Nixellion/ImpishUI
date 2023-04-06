"""
Functions from this module are added to jinja's filters
Make sure to add them to enabled_filters list
"""

from jinja2 import Markup
import prompter

def trim_tokens(text, max_tokens):
    return prompter.trim_text_by_tokens(text, max_tokens)

enabled_filters = [
    trim_tokens
]