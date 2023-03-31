# https://docs.streamlit.io/library/get-started/create-an-app


import logging

import streamlit as st
from streamlit.components.v1 import html
from functools import wraps
import requests
import traceback

from configuration import config

from datacache import data_cache

from prompter import format_prompt

from summarizer import summarize, summarize_openai, count_tokens
from openai_requester import OpenAI



# region Configure logger
logging.basicConfig(format="\n%(asctime)s\n%(message)s", level=logging.INFO, force=True)
# endregion

# region Configure OpenAI
oai = OpenAI()
# endregion


# region Define common templates
html_temp = """
                <div style="background-color:{};padding:1px">
                
                </div>
                """


all_state_variables = [
    ["text_error", ""],
    ["user_prompt", ""],
    ["n_requests", ""],
    ["edit_mode", False],
    ["memory", {}]
    # ["plain_text_log", data_cache.get("plain_text_log", "")]
]


def initialize_session_variables():
    for key, value in all_state_variables:
        if key not in st.session_state:
            st.session_state[key] = value
# endregion


# region Define primary functions
def session_limited(limit=1):
    """
    Decorator to prevent multiple requests, WIP
    """
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if st.session_state.n_requests >= limit:
                st.session_state.text_error = "Too many requests. Please wait a few seconds."
                logging.info(f"Session request limit reached: {st.session_state.n_requests}")
                st.session_state.n_requests = 1
                return
            retval = function(*args, **kwargs)
            return retval
        return wrapper
    return decorator


def on_submit():
    with text_spinner_placeholder:
        with st.spinner("Please wait..."):
            try:
                data_cache.set("world_info", world_info)
                TOKENS_LEFT = int(MAX_CONTEXT - (count_tokens(user_prompt) + count_tokens(world_info)))

                summarize_func = summarize if OPENAI_SUM is False else summarize_openai
                if len(data_cache.get("plain_text_log", "")) > 0:
                    summary = summarize_func(data_cache.get("plain_text_log", ""),
                                             max_total_tokens=max(TOKENS_LEFT, 64))
                else:
                    summary = ""

                data_cache.set("user_prompt", user_prompt)
                data_cache.set("plain_text_log", data_cache.get("plain_text_log", "") + user_prompt)
                data_cache.set("summary", summary)

                prompt = format_prompt(user_prompt, world_info, summary, instruction=INSTRUCTION, format="instruct_llama" if USE_LLAMA_INSTRUCT_FORMAT else "")

                print("=" * 80)
                print(f"Prompt:\n{prompt}")
                print("-" * 80)

                if not OPENAI_TEXT:
                    response = requests.post(config['kobold_url'] + "/api/v1/generate", json={
                        "prompt": prompt,
                        "temperature": TEMPERATURE,
                        "top_p": TOP_P,
                        "max_context_length": MAX_CONTEXT,
                        "max_length": MAX_TOKENS,
                        "rep_pen": REPETITION_PENALTY,
                        "rep_pen_range": REPETITION_PENALTY,
                        "rep_pen_slope": REPETITION_PENALTY,
                        "frmttriminc": True
                    })

                    print(response.text)
                    response = response.json()['results'][0]['text']

                else:
                    response = oai.raw_generate(prompt, model=config['openai_model'],
                                                max_tokens=MAX_TOKENS)
                print(f"Response:\n{response}")
                print("=" * 80)

                data_cache.set("plain_text_log", data_cache.get("plain_text_log", "") + response)

            except Exception as e:
                st.session_state.text_error = str(e) + str(traceback.format_exc())
                traceback.print_exc()


# @session_limited(1)
def on_clear():
    with text_spinner_placeholder:
        with st.spinner("Please wait..."):
            data_cache.set("plain_text_log", "")


def on_rewrite():
    with text_spinner_placeholder:
        with st.spinner("Please wait..."):
            data_cache.set("plain_text_log", user_prompt)


def on_edit_checkbox():
    with text_spinner_placeholder:
        with st.spinner("Please wait..."):
            st.session_state.edit_mode = not edit


def on_edit():
    with text_spinner_placeholder:
        with st.spinner("Please wait..."):
            if edited_log:
                data_cache.set("plain_text_log", edited_log)

# endregion


# region Stremlit UI
st.set_page_config(page_title="ImpishUI")

# Initnializing all required variables if they are not found in session state
initialize_session_variables()


with st.sidebar:
    st.markdown("""
    # About 
    ImpishUI is a proof of concept UI for KoboldAI with focus on automatically summarizing previous text to fit as much relevant data as possible into each prompt, to help stay within prompt-length limits, while keeping AI LLM model on track. 
    """)
    st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"), unsafe_allow_html=True)
    st.markdown("""
    [Github](#)
    """,
                unsafe_allow_html=True,
                )
    st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"), unsafe_allow_html=True)

    with st.expander("Settings:"):
        try:
            model_name = requests.get(config['kobold_url'] + "/api/v1/model").json()['result']
        except Exception as e:
            model_name = str(e)
        st.markdown("""Model: {}""".format(
            model_name
        ))

        MAX_CONTEXT = st.slider("Max Context Length", min_value=512, max_value=2048, value=2048)
        MAX_TOKENS = st.slider("Max Response Tokens", min_value=1, max_value=512, value=512)
        TEMPERATURE = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.5)
        TOP_P = st.slider("Top P", min_value=0.0, max_value=1.0, value=0.9)
        REPETITION_PENALTY = st.slider("Repetition Penalty", min_value=1.0, max_value=5.0, value=3.0)
        REP_PEN_RANGE = st.slider("Rep Pen Range", min_value=1.0, max_value=4096.0, value=950.0)
        REP_PEN_SLOPE = st.slider("Rep Pen Slope", min_value=0.0, max_value=10.0, value=0.7)
        # SUMMARIZE_PARTS = st.checkbox("Summarize Parts", value=False,
        #                               help="Whether to summarize each part separately, or to summarize the entire thing.")
        USE_LLAMA_INSTRUCT_FORMAT = st.checkbox("Use LLAMA Instruct format", value=True if "llama" in str(model_name).lower() or "alpaca"  in str(model_name).lower() else False, help="Enable this for LLAMA models.")
        INSTRUCTION = st.text_input("Instruction", value="Continue the story", help="Instruction, mostly needed if LLAMA Instruct format is on.")
        OPENAI_SUM = st.checkbox("Use OpenAI for summaries", value=False)
        OPENAI_TEXT = st.checkbox("Use OpenAI for text", value=False)

    st.markdown("# Summary\n" + data_cache.get("summary", ""))


st.title('ImpishUI')

if st.session_state.edit_mode:
    edited_log = st.text_area("Edit Log", value=data_cache.get("plain_text_log", ""))
    edited_log_button = st.button("Save Edits", on_click=on_edit)
else:
    st.markdown(data_cache.get("plain_text_log", ""))
    edited_log = None

text_spinner_placeholder = st.empty()
if st.session_state.text_error:
    st.error(st.session_state.text_error)

# form = st.form("Write")
world_info = st.text_area("World Info", value=data_cache.get(
    "world_info", ""), help="This information will always persist at the beginning of each prompt. Try to keep it within a reasonable token length.")
user_prompt = st.text_area("User Prompt", value=data_cache.get("user_prompt", ""))

col1, col2, col3, col4 = st.columns(4)

with col1:
    submit = st.button("Submit", on_click=on_submit)

with col2:
    rewrite = st.button("Rewrite", on_click=on_rewrite)

with col3:
    clear = st.button("Clear", on_click=on_clear)

with col4:
    edit = st.checkbox("Edit", value=False, on_change=on_edit_checkbox)
# endregion

# streamlit run .\app.py
