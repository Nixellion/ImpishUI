import requests
import json
from configuration import config
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
import time
from openai_requester import OpenAI
import traceback
from prompter import format_prompt

oai = OpenAI()

class KoboldAI():
    pass

def summarize_openai(prompt, max_total_tokens=300):
    max_total_tokens = min(max_total_tokens, 2000)
    print("Summarizing openAI...")
    chunks = break_up_text_to_chunks(prompt)
    text = ""
    print(f"Chunks: {len(chunks)}")
    max_chunk_tokens = int(max_total_tokens / len(chunks))
    for i, chunk in enumerate(chunks):
        print(i)
        prompt_request = "Summarize this text as short as possible, but keep all important details and events, character states and clothing, location descritions: " + convert_to_detokenized_text(chunk) + "\n\n Story Summary: "

        response = oai.raw_generate(prompt_request, "text-davinci-003", max_chunk_tokens)
        
        text += response
        text += "\n"
        time.sleep(1.5)

    # response = oai.raw_generate(f"Consolidate this story summary, and keep all important details and events, character states and clothing, location descritions: {text}", "text-davinci-003", max_total_tokens)
    
    return response

def summarize(prompt, max_total_tokens=300):
    max_total_tokens = min(max_total_tokens, 512)
    try:
        print("Summarizing...")
        chunks = break_up_text_to_chunks(prompt)
        text = ""
        print(f"Chunks: {len(chunks)}")
        max_chunk_tokens = int(max_total_tokens / len(chunks))
        for i, chunk in enumerate(chunks):
            print(i)
            prompt_request = format_prompt(
                user_prompt=convert_to_detokenized_text(chunk),
                instruction="Summarize"
            )

            # prompt_request = "Summarize this text as short as possible, but keep all important details and events, character states and clothing, location descritions: " + convert_to_detokenized_text(chunk) + "\n\n Story Summary: "

            response = requests.post(config['kobold_url'] + "/api/v1/generate", json={
                "prompt": prompt_request,
                "temperature": .5,
                "top_p": 1,
                "max_context_length": 2048,
                "max_length": max_chunk_tokens
                })

            summary_text = response.json()['results'][0]['text']
            print(summary_text)
            text += summary_text
            text += "\n"
            time.sleep(0.5)
    except Exception as e:
        try:
            print(response.text)
            raise Exception(response.text + str(e) + traceback.format_exc())
        except Exception as e:
            raise Exception(str(e) + traceback.format_exc())
    
    return text
        

def count_tokens(text):
    return len(word_tokenize(text))

def break_up_text(tokens, chunk_size, overlap_size):
    if len(tokens) <= chunk_size:
        yield tokens
    else:
        chunk = tokens[:chunk_size]
        yield chunk
        yield from break_up_text(tokens[chunk_size - overlap_size:], chunk_size, overlap_size)

def break_up_text_to_chunks(text, chunk_size=1400, overlap_size=100):
    tokens = word_tokenize(text)
    return list(break_up_text(tokens, chunk_size, overlap_size))

@staticmethod
def convert_to_detokenized_text(tokenized_text):
    prompt_text = " ".join(tokenized_text)
    prompt_text = prompt_text.replace(" 's", "'s")
    return prompt_text
