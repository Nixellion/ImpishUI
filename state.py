from configuration import config

class State():
    BUSY: bool = False
    LOADED_GAME = None
    TOKENIZER: str = config['tokenizers'][0]
    SUM_ADAPTER = None
    TEMPLATE_NAME: str = "instruct_llama_with_input"