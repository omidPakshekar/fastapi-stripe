# from pydantic import BaseModel
from mongoengine import Document, StringField, IntField, ListField


class User(Document):
    username = StringField()
    password = StringField()
    stripe_id = StringField()

class Payment(Document):
    stripe_id = StringField()
    password = StringField()
    subscription = StringField()
    total = StringField()

