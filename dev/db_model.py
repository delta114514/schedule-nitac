from general import *


class ViewCount(db.Model):
    __tablename__ = "viewcount"
    url = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Integer)

    def __init__(self, url, value):
        self.url = url
        self.value = value


class User(UserMixin, db.Model):
    __tablename__ = "teachers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    email = db.Column(db.String(32))
    password_hash = db.Column(db.String(128))
    teacher = db.Column(db.Boolean)

    def __init__(self, name, password_hash, email, teacher):
        self.name = name
        self.password_hash = password_hash
        self.email = email
        self.teacher = teacher

    def is_teacher(self) -> bool:
        return bool(self.teacher)

    def is_clerk(self) -> bool:
        return bool(not self.teacher)

    @staticmethod
    def is_authenticated() -> bool:
        return True

    @staticmethod
    def is_active() -> bool:
        return True

    @staticmethod
    def is_anonymous() -> bool:
        return False

    def get_id(self) -> int:
        return self.id

    def __repr__(self) -> str:
        return '<User %r>' % self.name


class Entry(db.Model):
    __tablename__ = "entry"
    changeid = db.Column(db.Integer, primary_key=True)
    change_from_class = db.Column(db.String(32))
    change_to_class = db.Column(db.String(32))
    change_from_date = db.Column(db.String(32))
    change_to_date = db.Column(db.String(32))
    change_from_time = db.Column(db.String(32))
    change_to_time = db.Column(db.String(32))
    change_from_teacher = db.Column(db.String(32))
    change_to_teacher = db.Column(db.String(32))
    target_depart = db.Column(db.Integer)
    timestamp = db.Column(db.Integer, default=datetime.datetime.now(JST).timestamp())
    published = db.Column(db.Boolean, default=False)
    remark = db.Column(db.String(256))
    contributor = db.Column(db.Integer)
    publisher = db.Column(db.Integer)

    def __init__(self, changeid=999, change_from_class="", change_to_class="", change_from_date="", change_to_date="",
                 change_from_time="", change_to_time="", target_depart="", remark="", contributor="", publisher="",
                 change_from_teacher="", change_to_teacher="", published=False):
        self.changeid = changeid
        self.change_from_class = change_from_class
        self.change_to_class = change_to_class
        self.change_from_date = change_from_date
        self.change_to_date = change_to_date
        self.change_from_time = change_from_time
        self.change_to_time = change_to_time
        self.target_depart = target_depart
        self.remark = remark
        self.contributor = contributor
        self.publisher = publisher
        self.published = published
        self.change_from_teacher = change_from_teacher
        self.change_to_teacher = change_to_teacher


class ValidMails(db.Model):
    __tablename__ = "valid_mail"
    email = db.Column(db.String(32))
    class_ = db.Column(db.Integer)
    token = db.Column(db.String(32), primary_key=True)

    def __init__(self, email, class_, token):
        self.email = email
        self.class_ = class_
        self.token = token


class Proposal(db.Model):
    __tablename__ = "proposal"
    body = db.Column(db.String(512))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(JST), primary_key=True)
    ip = db.Column(db.String(32), unique=False)

    def __init__(self, body, ip):
        self.body = body
        self.ip = ip
