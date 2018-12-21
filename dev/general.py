import datetime
import re
import os

from flask import Flask, flash, redirect, render_template, request, send_from_directory, jsonify, make_response, abort
from flask_login import login_user, logout_user, LoginManager, UserMixin, login_required, current_user

import jwt

from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

JST = datetime.timezone(datetime.timedelta(hours=+9), 'JST')
today = datetime.datetime.now(JST)

timestamp_str = "%Y-%m-%d"
cookie_timestamp_str = "%Y-%m-%d-%H-%M"

dat = {1: "1M", 2: "1E", 4: "1C", 8: "1A", 16: "2M", 32: "2E", 64: "2C", 128: "2A", 256: "3M", 512: "3E", 1024: "3C",
       2048: "3A", 4096: "4M", 8192: "4EJ", 16384: "4ED", 32768: "4C", 65536: "4A", 131072: "5M", 262144: "5EJ",
       524288: "5ED", 1048576: "5C", 2097152: "5A", 4194304: "1A.ME", 8388608: "1A.CA", 16777216: "2A.ME",
       33554432: "2A.CA", 67108864: "全体"}

dat_rev = {"1M": 1, "1E": 2, "1C": 4, "1A": 8, "2M": 16, "2E": 32, "2C": 64, "2A": 128, "3M": 256, "3E": 512,
           "3C": 1024, "3A": 2048, "4M": 4096, "4EJ": 8192, "4ED": 16384, "4C": 32768, "4A": 65536, "5M": 131072,
           "5EJ": 262144, "5ED": 524288, "5C": 1048576, "5A": 2097152, "1A.ME": 4194304, "1A.CA": 8388608,
           "2A.ME": 16777216, "2A.CA": 33554432, "全体": 67108864}

classes = ["全体", "2A.CA", "2A.ME", "1A.CA", "1A.ME", "5A", "5C", "5ED", "5EJ", "5M", "4A", "4C", "4ED", "4EJ", "4M",
           "3A", "3C", "3E", "3M", "2A", "2C", "2E", "2M", "1A", "1C", "1E", "1M"]

bins = [67108863, 33554432, 16777216, 8388608, 4194304, 2097152, 1048576, 524288, 262144, 131072, 65536, 32768, 16384,
        8192, 4096, 2048, 1024, 512, 256, 128, 64, 32, 16, 8, 4, 2, 1]


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config["JSON_AS_ASCII"] = False


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/manage"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

token_re = re.compile(r"mail/unsub/.+")