LLAMA_PROMPT_DICT = {
    "prompt_input":
        """Below is an instruction that describes a task, paired with an input that provides further context. 
Write a response that appropriately completes the request.


### Instruction:

{instruction}

### Input:
{input}

### Response:""",
    "prompt_no_input":
        """Below is an instruction that describes a task. 
Write a response that appropriately completes the request.


### Instruction:
{instruction}

### Response:"""

}


def format_prompt(user_prompt, world_info=None, summary=None, instruction="Reply to this request", format="instruct_llama"):
    if format == "instruct_llama":
        prompt = ""
        if world_info is not None and world_info.strip():
            prompt += f"{world_info}\n\n"

        if summary is not None and summary.strip():
            prompt += f"\n{summary}\n\n"

        if user_prompt is not None and user_prompt.strip():
            prompt += f"{user_prompt}\n\n"

        prompt = LLAMA_PROMPT_DICT["prompt_input"].format(
            instruction=instruction,
            input=prompt
        )

    else:
        prompt = ""
        if world_info is not None and world_info.strip():
            prompt += f"{world_info}\n\n"

        if summary is not None and summary.strip():
            prompt += f"Story so far:\n{summary}\n\n"

        if user_prompt is not None and user_prompt.strip():
            prompt += f"{instruction}:\n{user_prompt}\n\n"

    return prompt

# TODO There's place here to make it all more modular to allow adding more 'adapters' other than just openai and kobold
def send_prompt(user_prompt, world_info=None, summary=None, attrs={
    "temperature": 0.65,
    "top_p": 0.9,
    "max_context_length": 2048,
    "max_length": 512,
    "rep_pen": 3,
    "rep_pen_range": 1024,
    "rep_pen_slope": 0.7,
    "frmttriminc": True
},
openai_summarize=False,
openai_text=False
):
    TOKENS_LEFT = int(attrs['max_context_length'] - (count_tokens(user_prompt) + count_tokens(world_info)))

    summarize_func = summarize if openai_summarize is False else summarize_openai
    if len(data_cache.get("plain_text_log", "")) > 0:
        summary = summarize_func(data_cache.get("plain_text_log", ""),
                                    max_total_tokens=max(TOKENS_LEFT, 64))
    else:
        summary = ""

    prompt = format_prompt(user_prompt, world_info, summary, instruction=INSTRUCTION, format="instruct_llama" if USE_LLAMA_INSTRUCT_FORMAT else "")
    kobold_args['prompt'] = prompt
    print("=" * 80)
    print(f"Prompt:\n{prompt}")
    print("-" * 80)

    if not OPENAI_TEXT:
        response = requests.post(config['kobold_url'] + "/api/v1/generate", json={
            "prompt": prompt,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_context_length": max_context,
            "max_length": max_length,
            "rep_pen": REPETITION_PENALTY,
            "rep_pen_range": REPETITION_PENALTY,
            "rep_pen_slope": REPETITION_PENALTY,
            "frmttriminc": True
        })

        print(response.text)
        response = response.json()['results'][0]['text']

    else:
        response = oai.raw_generate(prompt, model=config['openai_model'],
                                    max_tokens=max_length)
    print(f"Response:\n{response}")
    print("=" * 80)

    data_cache.set("plain_text_log", data_cache.get("plain_text_log", "") + response)