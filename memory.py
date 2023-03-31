import json
from summarizer import summarize, summarize_openai

class Memory():
    def __init__(self) -> None:
        self.memory = []

    def add(self, text, summarizer=summarize):
        self.memory.append(
            {
            "text": text,
            "summary": summarize(text, max_total_tokens=150)
            }
        )

    def to_json(self):
        return json.dumps(self.memory)

    def from_json(self, data):
        self.memory = json.loads(data)

    def memory_summary(self):
        text = ""
        for part in self.memory:
            text += part['summary'] + "\n"