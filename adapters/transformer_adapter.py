import numpy as np
import torch
import math

from transformers import pipeline, set_seed, AutoModelWithLMHead, AutoTokenizer, AutoModel

from adapters import AdapterBase, AdapterCapability

# region Logger
import os
from debug import get_logger
log = get_logger("adapters")
# endregion

NAME = "Transformer"

CAPABILITIES = [
    AdapterCapability.SUMMARIZATION,
    AdapterCapability.TEXT_COHERENCE_SCORING
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
            "default": -1,
            "help": "Device ordinal for CPU/GPU supports. Setting this to -1 will leverage CPU, >=0 will run the model on the associated CUDA device id."
        }

    }

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.loaded_model_name = None
        self.model = None
        self.tokenizer = None
        self.summarization_pipeline = None

    def ensure_loaded_model(self):
        if self.loaded_model_name != self.huggingface_model:
            log.info(f"Transformer adapter loading {self.huggingface_model} model...")
            self.summarization_pipeline = pipeline('summarization', model=self.huggingface_model, device=self.device)
            self.loaded_model_name = self.huggingface_model
            self.tokenizer = AutoTokenizer.from_pretrained(self.loaded_model_name)
            self.model = AutoModel.from_pretrained(self.loaded_model_name)
            if self.device >= 0:
                # self.loaded_model_name.to("cuda")
                self.model.to("cuda")
                # self.tokenizer.to("cuda")

    def summarize_chunk(self, text, max_tokens):
        self.ensure_loaded_model()

        log.info(f"------------\nRunning summarization inference: {text}\n------------")
        summary_text = self.summarization_pipeline(text,
                                      max_length=max_tokens,
                                      min_length=max(max_tokens, self.min_length),
                                      do_sample=False)[0]['summary_text']

        return summary_text
    
    def coherence_score(self, text):
        log.info(f"Calculating coherence score...")
        self.ensure_loaded_model()
        # Tokenize the text into sentences
        sentences = [sent.strip() for sent in text.split('.')]
        sentences = [sent for sent in sentences if len(sent) > 0]
        num_sentences = len(sentences)

        # Compute the sentence embeddings using BERT
        embeddings = []
        for sent in sentences:
            inputs = self.tokenizer(sent, padding=True, truncation=True, return_tensors='pt')
            with torch.no_grad():
                if self.device >= 0:
                    outputs = self.model(**inputs.to(self.device))
                else:
                    outputs = self.model(**inputs)

            # If the tensor is already on the CPU, calling the cpu() method will have no effect and it will return the tensor unchanged. Therefore, you don't need to add any condition to handle that case.
            # BUT! Could be wrong.
            embeddings.append(outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy())

        # Compute the pairwise cosine similarity between sentence embeddings
        similarity_matrix = np.zeros((num_sentences, num_sentences))
        for i in range(num_sentences):
            for j in range(num_sentences):
                if i != j:
                    similarity_matrix[i][j] = np.dot(embeddings[i], embeddings[j]) / (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j]))

        # Compute the coherence score as the average pairwise similarity
        coherence = np.sum(similarity_matrix) / (num_sentences * (num_sentences - 1))
        if math.isnan(coherence) or coherence == "nan" or coherence is None:
            coherence = 0
        return coherence
