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
