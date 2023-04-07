import spacy

# load the spaCy NER model
nlp = spacy.load("en_core_web_sm")

# region Logger
import os
from debug import get_logger
log = get_logger("default")
# endregion

def extract_persons_from_text(text):
    log.info("Spacy extracting person information from text...")
    # extract all persons and their associated information
    doc = nlp(text)
    persons = {}
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # extract name and description
            name = ent.text
            start = ent.start_char
            end = ent.end_char
            desc = text[end:].split(".")[0].strip()
            if name not in persons:
                persons[name] = ""
            persons[name] += f" {name} {desc}."

    # Cleanup
    for name, desc in persons.items():
        persons[name] = desc.strip()
    # for person, desc in persons.items():
    #     print("="*80)
    #     print(person)
    #     print(desc)

    #     print()
    return persons