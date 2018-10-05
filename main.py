# -*- coding: utf-8 -*-

import os
import hashlib
import datetime
import random

from collections import defaultdict
from itertools import accumulate

from flask import Flask, flash, redirect, render_template, request, session, send_from_directory, jsonify, \
    make_response, abort
from flask_login import login_user, logout_user, LoginManager, UserMixin, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap

today = datetime.date(10, 1, 1)
dat = {2: '1M', 3: '1E', 5: '1C', 7: '1A', 11: '2M', 13: '2E', 17: '2C', 19: '2A', 23: '3M', 29: '3E',
       31: '3C', 37: '3A', 41: '4M', 43: '4EJ', 47: '4ED', 53: '4C', 59: '4A', 61: '5M', 67: '5EJ',
       71: '5ED', 73: '5C', 79: '5A', 83: '1A.ME', 89: '1A.CA', 97: '2A.ME', 101: '2A.CA'}
dat_rev = {'1M': 2, '1E': 3, '1C': 5, '1A': 7, '2M': 11, '2E': 13, '2C': 17, '2A': 19, '3M': 23, '3E': 29, '3C': 31,
           '3A': 37, '4M': 41, '4EJ': 43, '4ED': 47, '4C': 53, '4A': 59, '5M': 61, '5EJ': 67, '5ED': 71, '5C': 73,
           '5A': 79, '1A.ME': 83, '1A.CA': 89, '2A.ME': 97, '2A.CA': 101, "全体": 1}
all_set = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['JSON_AS_ASCII'] = False
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/manage"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)

with open("password", "r") as f:
    pass1, pass2, pass3 = f.read().split()


class View(db.Model):
    __tablename__ = "view"
    url = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Integer)

    def __init__(self, url, value):
        self.url = url
        self.value = value


class Teacher(UserMixin, db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(32))
    name = db.Column(db.String(32))
    email = db.Column(db.String(32))
    password_hash = db.Column(db.String(128))

    def __init__(self, userid, name, password_hash, email):
        self.userid = userid
        self.name = name
        self.password_hash = password_hash
        self.email = email

    def is_teacher(self):
        return True

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return (self.id)

    def __repr__(self):
        return '<Teacher %r>' % (self.name)


class Entry(db.Model):
    __tablename__ = 'entry'
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
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now())
    published = db.Column(db.Integer)
    remark = db.Column(db.String(256))
    contributor = db.Column(db.Integer)

    def __init__(self,changeid=999, change_from_class="", change_to_class="", change_from_date="", change_to_date="",
                 change_from_time="", change_to_time="", target_depart="", remark="", contributor="",
                 change_from_teacher="", change_to_teacher="", published=0):
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
        self.published = published
        self.change_from_teacher = change_from_teacher
        self.change_to_teacher = change_to_teacher


@login_manager.user_loader
def load_user(user_id):
    return Teacher.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return render_template("login.html")


def get_id(self):
    return self.session_token


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@app.before_request
def before_request():
    try:
        forwarded_protocol = request.headers.get('X-Forwarded-Proto', None)
        if forwarded_protocol is not None:
            if forwarded_protocol == 'http':
                new_url = request.url.replace('http', 'https', 1)
                return redirect(new_url)
    except RuntimeError as e:
        pass
    if request.path == '/count':
        return
    else:
        result = View.query.filter(View.url.in_([request.url])).first()
        if not result:
            db.session.add(View(request.url, 1))
            db.session.commit()
            return
        result.value += 1
        db.session.commit()
        return


def main_page(page, class_=None):
    global dat, all_set, dat_rev
    try:
        global today
        if today < datetime.date.today():
            del_lim()
    except:
        del_lim()
        today = datetime.date.today()
    if class_:
        try:
            tmp = {dat_rev[class_], }
        except ValueError:
            abort(404)
    else:
        if request.method == 'POST':
            tmp = set()
            for key, item in request.form.items():
                if key[:5] == "radio":
                    tmp.add(int(item))
            if not tmp:
                tmp = all_set | {1}
        else:
            if current_user.is_authenticated:
                tmp = all_set | {1}
            else:
                try:
                    tmp = prime_factors(intize(request.cookies))
                except:
                    tmp = all_set | {1}
                if not tmp:
                    tmp = all_set | {1}

    if current_user.is_authenticated:
        p = Entry.query.order_by(Entry.target_depart).all()
    else:
        p = Entry.query.filter(Entry.published.in_([1])).order_by(Entry.target_depart).all()

    for i in p[::]:
        if not prime_factors(i.target_depart) & tmp:
            if i.target_depart != 1:
                p.remove(i)

    return feed_cookie(render_template(page, page=p, prim=prime_factors, dat=dat, user=Teacher,
                                       datetime=datetime, map=map, list=list, int=int, len=len, range=range,
                                       lambda_=lambda x: dat[x]),
                       list(accumulate(tmp, lambda x, y: x * y))[-1])

@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static/icon", "favicon.ico")


@app.route("/", methods=['GET', 'POST'])
def article():
    return main_page("changes.html")


@app.route("/<class_>", methods=['GET', 'POST'])
def article_class(class_):
    return main_page("changes.html", class_)


@app.route("/one/<class_>", methods=['GET', 'POST'])
def ones_class(class_):
    return main_page("ones.html", class_)


@app.route("/one", methods=['GET', 'POST'])
def ones():
    return main_page("ones.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = False

    if request.method == 'GET':
        return render_template('register.html')

    user = Teacher(userid=request.form['userid'], name=str(request.form['name']),
                   password_hash=str(hashlib.sha256(b"%a" % str(request.form['password'])).digest()),
                   email=str(request.form['email']))

    adminpass = str(request.form['adminpass'])

    if adminpass != pass3:
        flash('Admin pass is not correct')
        error = True
    if not request.form["password"]:
        flash('Input Password')
        error = True
    if request.form["password"] != request.form["conf_password"]:
        flash('The password confirmation does not match.')
        error = True
    if Teacher.query.filter(Teacher.userid.in_([request.form['userid']])).first() != current_user:
        flash("The TeacherID is already used")
        error = True
    if Teacher.query.filter(Teacher.email.in_([request.form['email']])).first() != current_user:
        flash("The Email address is already used")
        error = True
    if error:
        return redirect('/register')

    db.session.add(user)
    db.session.commit()
    login_user(Teacher.query.filter(Teacher.userid.in_([request.form['userid']])).first(), remember=True)

    return redirect('/teacher')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'GET':
        return render_template("login.html")

    POST_USERID = str(request.form['userid'])
    POST_PASSWORD = str(hashlib.sha256(b"%a" % str(request.form['password'])).digest())

    result = Teacher.query.filter(Teacher.userid.in_([POST_USERID]),
                                  Teacher.password_hash.in_([POST_PASSWORD])).first()
    if not result:
        result = Teacher.query.filter(Teacher.email.in_([POST_USERID]),
                                      Teacher.password_hash.in_([POST_PASSWORD])).first()
    if result:
        login_user(result, remember=True)
        return redirect("/")
    else:
        flash('Invalid authentication')
        return redirect("/login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/teacher', methods=['GET', 'POST'])
@login_required
def upload():
    error = False
    allen = 0
    del_lim()
    if request.method == 'POST':
        tmp = 1
        for key, item in request.form.items():
            if key == "all":
                tmp = 1
                allen = 1
                break
            if key[:5] == "radio":
                tmp *= int(item)
        if tmp == 1 and not allen:
            flash("クラスを選択してください")
            error = True
        if not (request.form["to_date"] or request.form["from_date"]):
            flash("日付を入力してください")
            error = True
        if not (request.form["to_class"] or request.form["from_class"]):
            flash("授業を入力してください")
            error = True
        if not (request.form["to_time"] or request.form["from_time"]):
            flash("限目を入力してください")
            error = True
        password_hash = str(hashlib.sha256(b"%a" % str(request.form['password'])).digest())
        result = Teacher.query.filter(Teacher.userid.in_([current_user.userid]),
                                      Teacher.password_hash.in_([password_hash])).first()
        if not result:
            flash("パスワードを間違っています")
            error = True
        if error:
            return redirect("/teacher")
        to_class = request.form["to_class"]

        while True:
            id_ = random.randint(500, 1000)
            if not Entry.query.filter(Entry.changeid.in_([id_])):
                break
        entry = Entry(change_from_class=request.form["from_class"], change_to_class=to_class,
                      change_from_date=request.form["from_date"], change_to_date=request.form["to_date"],
                      change_from_time=request.form["from_time"], change_to_time=request.form["to_time"],
                      change_from_teacher=request.form["from_teacher"], change_to_teacher=request.form["to_teacher"],
                      remark=request.form["remark"], contributor=current_user.id, target_depart=tmp, changeid=id_)
        db.session.add(entry)
        db.session.commit()
        return redirect('/')
    return render_template("uploadpage.html")


@app.route('/editself', methods=['GET', 'POST'])
@login_required
def editself():
    if request.method == "GET":
        return render_template("editself_tea.html")
    if request.form["password"] == request.form["conf_password"] and str(hashlib.sha256(
            b'%a' % str(request.form['password'])).digest()) == current_user.password_hash:
        current_user.name = request.form["name"]
        current_user.email = request.form["email"]
        current_user.userid = request.form["userid"]
        if not request.form["name"] or not request.form["email"] or not request.form["userid"]:
            flash("失敗")
            return render_template("editself_tea.html")
        db.session.commit()
        flash("成功")
    else:
        flash("失敗")
    return render_template("editself_tea.html")


@app.route("/json/date/<day>")
def json_date(day):
    try:
        try:
            global today
            if today < datetime.date.today():
                del_lim()
        except:
            del_lim()
            today = datetime.date.today()
        jsons = {i: "" for i in day.replace(" ", "").split(";")}
        for date in day.split(";"):
            tmp = date.split("-")
            tmp = datetime.date(*map(int, tmp))
            p_from = Entry.query.filter(Entry.change_from_date.in_([date])).order_by(Entry.target_depart).all()
            p_to = Entry.query.filter(Entry.change_to_date.in_([date])).order_by(Entry.target_depart).all()
            p_all = list(set(p_from) | set(p_to))
            json = {
                "from_match": {str(i): json_it(m) for i, m in enumerate(p_from)
                               },
                "to_match": {str(i): json_it(m) for i, m in enumerate(p_to)
                             },
                "all_match": {str(i): json_it(m) for i, m in enumerate(p_all)
                              }
            }
            json["from_match"]["count"] = len(p_from)
            json["to_match"]["count"] = len(p_to)
            json["all_match"]["count"] = len(p_all)
            jsons[date] = json
        return jsonify(jsons)
    except:
        abort(500)


@app.route("/json/class/<depart>")
def json_depart(depart):
    try:
        global dat
        try:
            global today
            if today < datetime.date.today():
                del_lim()
        except:
            del_lim()
            today = datetime.date.today()
        p = Entry.query.all()

        dat_rev = {value: key for key, value in dat.items()}

        tmp = set(dat_rev[i] for i in depart.upper().replace(" ", "").split(";"))
        over = defaultdict(list)
        for i in p[::]:
            if not prime_factors(i.target_depart) & tmp:
                p.remove(i)
            for j in tmp:
                if j in prime_factors(i.target_depart):
                    over[dat[j]] += [i]
        json = {
            "all_match": {str(i): json_it(m) for i, m in enumerate(p)
                          }
        }
        json["all_match"]["count"] = len(p)
        for key, value in over.items():
            json[key] = {str(k): json_it(m) for k, m in enumerate(value)}
            json[key]["count"] = len(value)
        return jsonify(json)
    except:
        abort(500)


@app.route("/json/reference")
def api_reference():
    return render_template("reference.html")


@app.route("/edit/<int:num>", methods=['GET', 'POST'])
@login_required
def edit(num=0):
    p = Entry.query.filter(Entry.changeid.in_([num])).first()
    if not p:
        return render_template("404.html")
    global dat
    if request.method == 'POST':
        edited = 0
        tmp = 1
        for key, item in request.form.items():
            if key == "all":
                edited = 1
                break
            if key[:5] == "radio":
                tmp *= int(item)
        if tmp == 1 and not edited:
            tmp = p.target_depart
        if p.contributor != current_user.id:
            return render_template("404.html")
        p.target_depart = tmp
        p.change_from_date = request.form["from_date"]
        p.change_from_class = request.form["from_class"]
        p.change_from_time = request.form["from_time"]
        p.change_from_teacher = request.form["from_teacher"]
        p.change_to_date = request.form["to_date"]
        p.change_to_class = request.form["to_class"]
        p.change_to_time = request.form["to_time"]
        p.change_to_teacher = request.form["to_teacher"]
        p.remark = request.form["remark"]
        p.published = request.form["published"]
        if str(request.form["delete"]) == "いいよ！こいよ！":
            db.session.delete(p)
            db.session.commit()
            return redirect("/")

        tmp = Entry.query.filter(Entry.changeid.in_([int(request.form["number"])])).first()
        if tmp and tmp != p:
            flash("管理ナンバーが重複しています")
        else:
            p.changeid = int(request.form["number"])
            db.session.commit()
    return render_template('edit.html', page=p, prim=prime_factors, dat=dat)


@app.route("/<passw>/count")
def count(passw):
    if passw == pass2:
        return render_template("count.html", que=View.query.all())
    else:
        return redirect("404.html")


@app.route("/proposal", methods=["GET", "POST"])
def proposal():
    if request.method == "GET":
        return render_template("proposal.html")
    else:
        with open("art.txt", "a") as file:
            file.write(request.form["string"].replace("[EOA]", "") + "[EOA]")
        flash("メッセージが投稿されました。")
        return render_template("proposal.html")


@app.route("/proposals/<passw>")
def proposals(passw):
    if passw == pass1:
        try:
            with open("art.txt", "r") as file:
                tmp = file.read().split("[EOA]")[:-1]
            txt = "<table border=\"1\" width=\"400\"><tr><th>body</th></tr><tr><td>" + "</td></tr><tr><td>".join(
                tmp) + "</tb></tr></table>"
            return txt
        except:
            return "no proposals"


@app.route("/flush")
@login_required
def flush():
    del_lim()
    return "flushed!"


@app.route('/<passw>/static/<filename>')
def static_dir(passw, filename):
    if passw == pass2:
        return send_from_directory('static', filename)
    else:
        return redirect("404.html")


@app.route('/<passw>/image/<filename>')
def image_dir(passw, filename):
    if passw == pass2:
        return send_from_directory('image', filename)
    else:
        return redirect("404.html")


@app.route('/file/<filename>')
@login_required
def files(filename):
    return send_from_directory("./", filename)

@app.route('/to_pdf/<id_>')
def to_pdf(id_):
    col = {"m": "red", "e": "orange", "c": "cyan", "a": "green", "all": "#250d00"}
    art = Entry.query.filter(Entry.changeid.in_([id_])).first()
    if not art:
        abort(404)
    depart = art.target_depart
    if depart == 2021:
        depart = "4E"
        color = col["e"]
    elif depart == 4757:
        depart = "5E"
        color = col["e"]
    elif depart == 210:
        depart = "1年"
        color = col["all"]
    elif depart == 46189:
        depart = "2年"
        color = col["all"]
    elif depart == 765049:
        depart = "3年"
        color = col["all"]
    elif depart == 259106347:
        depart = "4年"
        color = col["all"]
    elif depart == 1673450759:
        depart = "5年"
        color = col["all"]
    elif depart == 7387:
        depart = "専攻科1年"
        color = col["all"]
    elif depart == 9797:
        depart = "専攻科2年"
        color = col["all"]
    elif depart == 3217644767340672907899084554130:
        depart = "本科生"
        color = col["all"]
    elif depart == 232862364358497360900063316880507363070:
        depart = "全学生"
        color = col["all"]
    elif depart == 72370439:
        depart = "専攻科生"
        color = col["all"]
    else:
        depart = ",".join(list(map(lambda x: dat[x], prime_factors(depart))))
        color = col[depart[-1].lower()]

    under = "{}月{}日 学生課 No.{}".format(int(datetime.date.today().strftime("%m")), int(datetime.date.today().strftime("%d")), art.changeid)

    situ = "と振替える" if art.change_from_teacher and art.change_to_teacher else "に移動する" if art.change_from_date and art.change_to_date else "休講とする"

    if art.change_from_date == art.change_to_date and art.change_from_teacher == art.change_to_teacher and art.change_from_class == art.change_to_class:
        situ = art.remark
        art.change_to_class = ""
        art.change_to_date = "none"
        art.change_to_teacher = ""

    return render_template("to_pdf.html", datetime=datetime, dat=dat, art=art, depart=depart, map=map, int=int, list=list, under=under, situ=situ, color=color)


def feed_cookie(content, cookie):
    response = make_response(content)
    max_age = 60 * 60 * 24 * 120
    response.set_cookie('depart', value=str(cookie * 810893), max_age=max_age)
    return response


def intize(cookie):
    return int(cookie.get("depart"))


def json_it(entry):
    global dat
    json = {
        "from": {
            "class": entry.change_from_class,
            "date": entry.change_from_date,
            "time": entry.change_from_time,
            "teacher": entry.change_from_teacher
        },
        "to": {
            "class": entry.change_to_class,
            "date": entry.change_to_date,
            "time": entry.change_to_time,
            "teacher": entry.change_to_teacher
        },
        "depart": ";".join([dat[i] for i in prime_factors(entry.target_depart)]),
        "remark": entry.remark
    }
    return json


def del_lim():
    p = Entry.query.all()
    deleted = False
    for ent in p:
        try:
            bef = datetime.date(*list(map(int, ent.change_from_date.split("-"))))
        except:
            bef = datetime.date(1, 1, 1)
        try:
            to = datetime.date(*list(map(int, ent.change_to_date.split("-"))))
        except:
            to = datetime.date(1, 1, 1)
        if max(bef, to) < datetime.date.today():
            db.session.delete(ent)
            deleted = True
    if deleted:
        db.session.commit()


def prime_factors(n):
    global all_set
    if not n:
        return set()
    i = 2
    factors = []
    for i in all_set:
        if not n % i:
            factors.append(i)
    return set(factors)


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='0.0.0.0', port=8888, threaded=True)