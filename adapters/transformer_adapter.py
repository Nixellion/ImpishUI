from transformers import pipeline, set_seed, AutoModelWithLMHead, AutoTokenizer

from adapters import AdapterBase, AdapterCapability

# region Logger
import os
from debug import get_logger
log = get_logger("adapters")
# endregion

NAME = "Transformer"

CAPABILITIES = [
    AdapterCapability.SUMMARIZATION
]


# INSTALLING PYTORCH CUDA https://stackoverflow.com/questions/70340812/how-to-install-pytorch-with-cuda-support-with-pip-in-visual-studio
# Kobold 4bit compatible fir 07.04.2023: pip install torch==1.10.1+cu111 torchvision==0.11.2+cu111 torchaudio==0.10.1 -f https://download.pytorch.org/whl/cu111/torch_stable.html
# This is for me: CUDA_PATH C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.1

class Adapter(AdapterBase):
    """
    Hugging face transformers library for summarization. May not work with all models.
    """
    ATTRIBUTES = {
        "huggingface_model":
        {
            "type": str,
            "default": "slauw87/bart_summarisation",
            # tuner007/pegasus_summarizer
            # Kaludi/Quick-Summarization
            # slauw87/bart_summarisation
        },
        "min_length":
        {
            "type": int,
            "default": 100,
            "help": "Some models won't work if this is set too low."
        },
        "device":
        {
            "type": int,
            "default": 0,
            "help": "Device ordinal for CPU/GPU supports. Setting this to -1 will leverage CPU, >=0 will run the model on the associated CUDA device id."
        },
        # "use_cuda":
        # {
        #     "type": bool,
        #     "default": True
        # }
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.loaded_model = None
        self.generator = None

    def summarize_chunk(self, text, max_tokens):
        if self.loaded_model != self.huggingface_model:
            log.info(f"Summarizer loading {self.huggingface_model} model...")
            self.generator = pipeline('summarization', model=self.huggingface_model, device=self.device)
            self.loaded_model = self.huggingface_model
            if self.device >= 0:
                self.loaded_model.to("cuda")

        log.info(f"------------\nRunning summarization inference: {text}\n------------")
        summary_text = self.generator(text,
                                      max_length=max_tokens,
                                      min_length=max(max_tokens, self.min_length),
                                      do_sample=False)[0]['summary_text']

        return summary_text
