# region ############################# IMPORTS #############################
import os
import json
import jsonpickle
from datetime import datetime
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField  # , FTS5Model, SearchField
from playhouse.fields import CompressedField
from configuration import config
from paths import DATABASE_PATH
import adapters
import nlp
from state import State
from paths import DATA_DIR
from copy import copy



from adapters.sumy_adapter import Adapter as SumyAdapter
import adapters
# endregion

from debug import get_logger
log = get_logger("database")


# region ############################# GLOBALS #############################
pragmas = [
    ('journal_mode', 'wal'),
    ('cache_size', -1000 * 32)]
db = SqliteExtDatabase(DATABASE_PATH, pragmas=pragmas)
# endregion


# region ############################# TABLE CLASSES #############################


class ImpishBaseModel(Model):
    date_created = DateTimeField()
    date_updated = DateTimeField()
    date_deleted = DateTimeField(null=True)
    deleted = BooleanField(default=False)

    class Meta:
        database = db

    def mark_deleted(self):
        self.deleted = True
        self.date_deleted = datetime.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.date_created is None:
            self.date_created = datetime.now()

        self.date_updated = datetime.now()

        super(ImpishBaseModel, self).save(*args, **kwargs)


class Game(ImpishBaseModel):
    name = CharField()
    state_pickle = CompressedField(null=True, compression_level=9)

    def add_message(self, text, author="", skip_summarization=False):
        message = Message()
        message.author = author
        message.text = text
        message.game = self
        if not skip_summarization:
            message.summarize()
        message.save()

    @property
    def all_text(self):
        return "\n\n".join([message.text for message in self.messages])

    @property
    def all_summary_entries(self):
        return "\n\n".join([message.summary for message in self.messages])

    @property
    def ai_summary_entries(self):
        messages = []
        for message in self.messages:
            if message.author.lower() == "impish":
                messages.append(message.summary)

        return "\n\n".join(messages)
    
    def get_automatic_world_info(self):
        """
        filters: Any text, if it containts the name it's info will be included (case insensitive).
        """
        entities = State.instance.adapters_ui_data['ui'][adapters.AdapterCapability.WORLD_INFO_EXTRACTION]['selected'].extract_world_info(self.all_text)
        # text = ""
        # for entity, description in entities.items():
        #     if filters is None or entity.lower() in filters.lower():
        #         text += entity + ":\n" + description + "\n\n"
        return entities

class Settings(ImpishBaseModel):
    data = JSONField()
    game = ForeignKeyField(Game, backref="messages")

    


class Message(ImpishBaseModel):
    author = CharField()
    text = TextField()
    summary = TextField()
    game = ForeignKeyField(Game, backref="messages")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def summarize(self, tokens_percent=0.4, min_tokens=100):
        log.info(f"Message {self.id} - summarizing...")
        self.summary = State.instance.SUM_ADAPTER.summarize(self.text, tokens_percent=tokens_percent, min_tokens=min_tokens)

    def save(self, *args, **kwargs):
        log.info(f"Message {self.id} - saving...")
        # self.summary = State.instance.SUM_ADAPTER.summarize(self.text, tokens_percent=0.4, min_tokens=100)
        super(Message, self).save(*args, **kwargs)


class Character(ImpishBaseModel):
    name = CharField()
    description = TextField()
    state = TextField()


def load_game(game_id):
    game = Game.select().where(Game.id == game_id).get()
    if game.state_pickle is not None:
        # FIXME: Recursion
        try:
            state_pickle = copy(game.state_pickle)
            loaded_state = jsonpickle.decode(state_pickle.decode("utf-8"))
            # State.instance = loaded_state  # BUG Disabling until fixed
        except Exception as e:
            log.warning(f"Failed loading UI state from db: {e}")
    State.instance.LOADED_GAME = Game.select().where(Game.id == game_id).get()

log.info(" ".join(["Using DB", str(db), "At path:", str(DATABASE_PATH)]))

# On init make sure we create database

db.connect()
db.create_tables([Game, Settings, Message])

if len(Game.select()) == 0:
    game = Game()
    game.name = "default"
    game.save()

# endregion
