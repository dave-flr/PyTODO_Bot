from pony.orm import Database, Required, Optional, Set, PrimaryKey

db = Database()


class Chat(db.Entity):
    id = PrimaryKey(int)
    type = Required(str)
    title = Optional(str)
    username = Optional(str)
    first_name = Optional(str)
    last_name = Optional(str)
    photo = Optional(str)
    description = Optional(str)
    invite_link = Optional(str)
    pinned_message = Optional(str)

    task = Set(lambda: Task)  # A Chat can contain many Task


class Task(db.Entity):
    id = PrimaryKey(int)
    task = Required(str)
    chat = Required(Chat)  # A task belongs to a chat
    complete = Required(bool)


db.bind(provider='sqlite', filename='../database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)
