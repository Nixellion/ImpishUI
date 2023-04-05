# from adapters import AdapterBase, AdapterCapability
from enum import Enum

from adapters import AdapterBase, AdapterCapability

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer


NAME = "Sumy"

CAPABILITIES = [
    AdapterCapability.SUMMARIZATION
]


class SumyAlgorithm(Enum):
    LSA = 10
    TextRank = 20


class Adapter(AdapterBase):
    """
    Fast local summarizer allowing you to perform summarizations using LSA or TextRank algorithms.
    It's not nearly as good as what a Large Language Model would do, but it's incredibly fast.
    """
    ATTRIBUTES = {
        "summarization_algorithm":
        {
            "type": SumyAlgorithm,
            "default": SumyAlgorithm.LSA
        }
    }

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.algorithms = {
            SumyAlgorithm.LSA: LsaSummarizer(),
            SumyAlgorithm.TextRank: TextRankSummarizer()
        }

    def summarize_chunk(self, text, max_tokens):
        summary_text = ""
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = self.algorithms[self.summarization_algorithm]
        summarizer.stop_words = "english"
        summary = summarizer(parser.document, 3) # TODO: Sentences count should not be hardcoded like this
        for sentence in summary:
            summary_text += str(sentence)

        return summary_text
