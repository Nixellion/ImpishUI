# from adapters import AdapterBase, AdapterCapability
from adapters import AdapterBase, AdapterCapability

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer


NAME = "Sumy"

CAPABILITIES = [
    AdapterCapability.SUMMARIZATION
]


class Adapter(AdapterBase):
    ATTRIBUTES = {
    }

    # def summarize(self, text, **kwargs):
    #     return gensim_summarize(text, ratio = "")

    def __init__(self, attrs=None):
        super().__init__(attrs)


    def summarize_chunk(self, text):
        summary_text = ""
        # Create a plaintext parser
        parser = PlaintextParser.from_string(text, Tokenizer("english"))

        # Create an LSA summarizer
        summarizer = LsaSummarizer()

        # Summarize the document with 3 sentences
        summary = summarizer(parser.document, 3)

        # Print the summary
        for sentence in summary:
            summary_text += str(sentence)


        # =================

        # Create a parser for the text
        parser = PlaintextParser.from_string(text, Tokenizer("english"))

        # Create a TextRank summarizer
        summarizer = TextRankSummarizer()

        # Set the language of the text
        summarizer.stop_words = "english"

        # Set the number of sentences in the summary
        summary = summarizer(parser.document, sentences_count=3)

        # Print the summary
        for sentence in summary:
            summary_text += str(sentence)

        return summary_text
