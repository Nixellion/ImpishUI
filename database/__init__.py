# region ############################# IMPORTS #############################
import os
import json
from datetime import datetime
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField  # , FTS5Model, SearchField
from configuration import read_config, write_config
from paths import DATABASE_PATH

from adapters.sumy_adapter import Adapter as SumyAdapter
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
    filename = TextField()


class Settings(ImpishBaseModel):
    data = JSONField()
    game = ForeignKeyField(Game, backref="messages")

    @property
    def all_text(self):
        return "\n".join([message.text for message in self.messages])

    @property
    def all_summary_entries(self):
        return "\n".join([message.summary for message in self.messages])


class Message(ImpishBaseModel):
    author = CharField()  
    text = TextField()
    summary = TextField()
    game = ForeignKeyField(Game, backref="messages")

    def add(self, text, author="", summarizer=None):
        if summarizer is None:
            summarizer = SumyAdapter()

        self.messages.append(
            {
                "author": author,
                "text": text,
                "summary": summarizer.summarize(text, max_tokens=150)
            }
        )

class Character(ImpishBaseModel):
    name = CharField()
    description = TextField()
    state = TextField()


log.info(" ".join(["Using DB", str(db), "At path:", str(DATABASE_PATH)]))

# On init make sure we create database

db.connect()
db.create_tables([Game, Settings, Message])

# endregion
