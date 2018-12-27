# -*- coding: utf-8 -*-

import hashlib
import random
import secrets
import smtplib

from email import message
from collections import defaultdict
from itertools import compress
from threading import Thread

from db_model import *
from general import *

with open("password", "r") as f:
    proposal_pass, count_pass, teacher_create_pass, clerk_create_pass, mail_pass, jwt_pass = f.read().split()


def int2bin(n: int) -> str:
    try:
        return format(n, "027b")
    except:
        return "1" * 27


def bin2int(n: str) -> int:
    try:
        return int(n, 2)
    except:
        return bins[0]


def int2classes(n: int) -> list:
    try:
        return list(compress(classes, map(lambda x: int(x), list(int2bin(n)))))
    except:
        return classes


def bin2classes(n: str) -> list:
    try:
        return list(compress(classes, map(lambda x: int(x), list(n))))
    except:
        return bins


def int2bins(n: int) -> list:
    try:
        return list(compress(bins, map(lambda x: int(x), list(int2bin(n)))))
    except:
        return classes


def bin2bins(n: str) -> list:
    try:
        return list(compress(bins, map(lambda x: int(x), list(n))))
    except:
        return [1] * 27


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return render_template("login.html")


def get_id(self):
    return self.session_token


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500


@app.before_request
def before_request():
    try:
        forwarded_protocol = request.headers.get("X-Forwarded-Proto", None)
        if forwarded_protocol is not None:
            if forwarded_protocol == "http":
                new_url = request.url.replace("http", "https", 1)
                return redirect(new_url)
    except RuntimeError as e:
        pass
    if request.path == "/count":
        return
    else:
        result = ViewCount.query.get(request.url)
        if not result:
            db.session.add(ViewCount(request.url, 1))
            db.session.commit()
            return
        result.value += 1
        db.session.commit()


def send_verify_mail(email, token):
    text = f"""
こちらClassManager(Schedule-Nitac)運営です。
メール通知サービスへの登録ありがとうございます。
以下のURLに接続いただくとご登録が完了します。

    https://schedule-nitac.mybluemix.net/mail/token/{token}

認証URLは30分後の {(datetime.datetime.now(JST)+datetime.timedelta(0,1800)).strftime("%Y/%m/%d %H:%M")} まで有効です。
心当たりのない方はこのメールを破棄してください。

ClassManager(Schedule-Nitac)
https://schedule-nitac.mybluemix.net/
    """
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    from_email = "schedule.nitac@gmail.com"
    to_email = email
    username = "schedule.nitac@gmail.com"
    password = mail_pass

    msg = message.EmailMessage()
    msg.set_content(text)
    msg["Subject"] = "【ClassManager】登録認証URL"
    msg["From"] = from_email
    msg["To"] = to_email

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    server.send_message(msg)
    server.quit()


def send_change_mail(user, changes):
    global dat
    text = f"""
こちらClassManager(Schedule-Nitac)運営です。<br>
本日の授業の変更です。<br>
<hr>
<html>
<table border=1 cellspacing="0" bordercolor="#C4CAC7">
        <thead>
        <tr>
            <th>対象</th>
            <th>内容</th>
            <th>日時</th>
            <th>科目</th>
            <th>備考</th>
        </tr>
        </thead>
        <tbody>"""
    for art in changes:
        col_bef = datetime.datetime.strptime(art.change_from_date, timestamp_str)
        col_aft = datetime.datetime.strptime(art.change_to_date, timestamp_str)
        text += f"""
            <tr>

                {"<td>" + ", ".join(int2classes(art.target_depart)) + "</td>"}
                <td>{"振替" if art.change_from_teacher and art.change_to_teacher else "移動" if
                    art.change_from_date and art.change_to_date else "休講"}
                </td>
                <td>{"{}-{}({}):{}限".format(col_bef.month, col_bef.day, "月火水木金土日"[col_bef.weekday()], art.change_from_time) if art.change_from_date else "休講"}
                    {'⇔' if (art.change_from_teacher and art.change_to_teacher) else '→'}
                    {"{}-{}({}):{}限".format(col_aft.month, col_aft.day, "月火水木金土日"[col_aft.weekday()], art.change_to_time) if art.change_to_date else "休講"}
                </td>
                <td>{art.change_from_class+ "(" + art.change_from_teacher + ")" if
                    art.change_from_class else "なし"}
                    {'⇔' if (art.change_from_teacher and art.change_to_teacher) else '→'}
                    {art.change_to_class + "(" + art.change_to_teacher + ")" if art.change_to_class
                    else "なし"}
                </td>
                <td>{art.remark if art.remark else "なし"} </td>
            </tr>
            </tbody>"""
    text += f"""
</table>
</html>
<hr>
<br>
配信停止を希望される方はこちらのURLまで接続してください。
<br><br>
https://schedule-nitac.mybluemix.net/mail/unsub/{user.token}
<br><br>
ClassManager(Schedule-Nitac)
https://schedule-nitac.mybluemix.net/
    """
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    from_email = "schedule.nitac@gmail.com"
    to_email = user.email
    username = "schedule.nitac@gmail.com"
    password = mail_pass

    msg = message.EmailMessage()
    msg.set_content(text, subtype="html")
    msg["Subject"] = "【ClassManager】本日の変更"
    msg["From"] = from_email
    msg["To"] = to_email

    server = smtplib.SMTP(smtp_host, smtp_port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(username, password)
    server.send_message(msg)
    server.quit()


def change_mail():
    timestamp = str(datetime.date.fromtimestamp(datetime.datetime.now(JST).timestamp()))
    ents = Entry.query.filter((Entry.change_from_date.in_([timestamp])) | (Entry.change_to_date.in_([timestamp])))
    sends = defaultdict(set)
    for ent in ents:
        for change in ents:
            for class_ in int2bins(change.target_depart):
                sends[class_].add(ent)
    users = ValidMails.query.all()
    tmp = set()
    for user in users:
        for depart in int2bins(user.class_):
            tmp |= sends[depart]
        if tmp:
            send_change_mail(user, tmp)


def main_page(page, class_=None):
    try:
        global today
        if today < datetime.datetime.now(JST):
            del_lim()
            thread = Thread(target=change_mail)
            thread.start()
            today = datetime.datetime.now(JST)
    except:
        del_lim()
        today = datetime.datetime.now(JST)
    if class_:
        try:
            tmp = dat_rev[class_]
        except ValueError:
            abort(404)
    else:
        if request.method == "POST":
            tmp = 0
            for key, item in request.form.items():
                if key[:5] == "radio":
                    tmp += int(item)
            if not tmp:
                tmp = bins[0]
        else:
            if current_user.is_authenticated:
                tmp = bins[0]
            else:
                try:
                    tmp = get_dep_cookie(request.cookies)
                except Exception:
                    tmp = bins[0]
                if not tmp:
                    tmp = bins[0]
    if tmp > 2 ** 64:
        tmp = bins[0]
    try:
        last = request.cookies.get("last_seen")
        if datetime.datetime.strptime(last, cookie_timestamp_str) < datetime.datetime.fromtimestamp(
                Entry.query.filter(Entry.published).order_by(Entry.timestamp.desc()).first().timestamp, tz=JST):
            new = 1
        else:
            new = 0
    except Exception:
        new = 0

    if current_user.is_authenticated:
        p = Entry.query.order_by(Entry.target_depart).all()
    else:
        p = Entry.query.filter(Entry.published, Entry.target_depart.op("&")(tmp)).order_by(Entry.target_depart).all()
    return feed_cookie(render_template(page, page=p, date_str=timestamp_str, user=User, str=str, format=format,
                                       datetime=datetime, new=new, int2classes=int2classes), tmp)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static/icon", "favicon.ico")


@app.route("/", methods=["GET", "POST"])
def article():
    return main_page("changes.html")


@app.route("/<class_>", methods=["GET", "POST"])
def article_class(class_):
    return main_page("changes.html", class_)


@app.route("/one/<class_>", methods=["GET", "POST"])
def ones_class(class_):
    return main_page("ones.html", class_)


@app.route("/one", methods=["GET", "POST"])
def ones():
    return main_page("ones.html")


@app.route("/register/teacher", methods=["GET", "POST"])
def register_teacher():
    error = False

    if request.method == "GET":
        return render_template("register_teacher.html")

    user = User(name=str(request.form["name"]),
                password_hash=str(hashlib.sha256(b"%a" % str(request.form["password"])).digest()),
                email=str(request.form["email"]), teacher=True)

    adminpass = str(request.form["adminpass"])

    if adminpass != teacher_create_pass:
        flash("Admin-pass is not correct")
        error = True
    if not request.form["password"]:
        flash("Input Password")
        error = True
    if request.form["password"] != request.form["conf_password"]:
        flash("The password confirmation does not match.")
        error = True
    if User.query.filter(User.email.in_([request.form["email"]])).first() not in [user, None]:
        flash("The Email address is already in use")
        error = True
    if error:
        return redirect("/register/teacher")

    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)

    return redirect("/")


@app.route("/register/clerk", methods=["GET", "POST"])
def register_clerk():
    error = False

    if request.method == "GET":
        return render_template("register_clerk.html")

    user = User(name=str(request.form["name"]),
                password_hash=str(hashlib.sha256(b"%a" % str(request.form["password"])).digest()),
                email=str(request.form["email"]), teacher=False)

    adminpass = str(request.form["adminpass"])

    if adminpass != clerk_create_pass:
        flash("Admin-pass is not correct")
        error = True
    if not request.form["password"]:
        flash("Input Password")
        error = True
    if request.form["password"] != request.form["conf_password"]:
        flash("The password confirmation does not match.")
        error = True
    if User.query.filter(User.email.in_([request.form["email"]])).first() not in [user, None]:
        flash("The Email address is already in use")
        error = True
    if error:
        return redirect("/register/clerk")

    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)

    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    POST_EMAIL = str(request.form["email"])
    POST_PASSWORD = str(hashlib.sha256(b"%a" % str(request.form["password"])).digest())

    result = User.query.filter(User.email.in_([POST_EMAIL]),
                               User.password_hash.in_([POST_PASSWORD])).first()
    if result:
        login_user(result, remember=True)
        return redirect("/")
    else:
        flash("Invalid authentication")
        return redirect("/login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/mail/request", methods=["GET", "POST"])
def mail_request():
    if request.method == "GET":
        return render_template("mail_request.html")
    error = 0
    if not request.form["email"]:
        flash("emailアドレスを入力してください")
        error = 1
    if len(request.form) < 2:
        flash("クラスを選択して下さい")
        error = 1
    if ValidMails.query.filter(ValidMails.email.in_([request.form["email"]])).first():
        flash("すでに登録されています")
        error = 1
    if error:
        return render_template("mail_request.html")
    class_ = 0
    for key, value in request.form.items():
        if key != "email":
            class_ += int(value)
    token = jwt.encode({"email": request.form["email"], "class": class_,
                        "expired": (datetime.datetime.now(JST) + datetime.timedelta(0, 1800)).timestamp()}, jwt_pass,
                       algorithm="HS256").decode()
    send_verify_mail(token=token, email=request.form["email"])

    return render_template("mail_request_fin.html")


@app.route("/mail/token/<token>")
def mail_token(token):
    timestamp = datetime.datetime.now(JST)
    try:
        dec = jwt.decode(token, jwt_pass, algorithms=["HS256"])
    except jwt.DecodeError:
        abort(404)
    if datetime.datetime.now().timestamp() > float(dec["expired"]):
        abort(404)
    va_user = ValidMails(email=dec["email"], class_=dec["class"], token=secrets.token_urlsafe(32).lower())
    db.session.add(va_user)
    db.session.commit()
    return render_template("mail_fin.html")


@app.route("/mail/unsub/<token>")
def mail_unsub(token):
    user = ValidMails.query.get_or_404(token)
    return render_template("mail_unsub_conf.html", user=user)


@app.route("/mail/unsub/submit", methods=["POST"])
def mail_unsub_fin():
    token = token_re.search(request.referrer)[0][11:]
    user = ValidMails.query.get_or_404(token)
    db.session.delete(user)
    db.session.commit()
    return render_template("mail_unsub_fin.html")


@app.route("/edit", methods=["GET", "POST"])
@login_required
def upload():
    error = False
    del_lim()
    if request.method == "POST":
        tmp = 0
        for key, item in request.form.items():
            if key == "all":
                tmp = bins[0]
                break
            if key[:5] == "radio":
                tmp += int(item)
        if not tmp:
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
        password_hash = str(hashlib.sha256(b"%a" % str(request.form["password"])).digest())
        result = User.query.filter(User.email.in_([current_user.email]),
                                   User.password_hash.in_([password_hash])).first()
        if not result:
            flash("パスワードを間違っています")
            error = True
        if error:
            return redirect("/teacher")
        to_class = request.form["to_class"]

        while True:
            id_ = random.randint(500, 1000)
            if not Entry.query.filter(Entry.changeid.in_([id_])).first():
                break
        entry = Entry(change_from_class=request.form["from_class"], change_to_class=to_class,
                      change_from_date=request.form["from_date"], change_to_date=request.form["to_date"],
                      change_from_time=request.form["from_time"], change_to_time=request.form["to_time"],
                      change_from_teacher=request.form["from_teacher"], change_to_teacher=request.form["to_teacher"],
                      remark=request.form["remark"], contributor=current_user.id, target_depart=tmp, changeid=id_)
        db.session.add(entry)
        db.session.commit()
        return redirect("/")
    return render_template("uploadpage.html")


@app.route("/editself", methods=["GET", "POST"])
@login_required
def editself():
    if request.method == "GET":
        return render_template("editself_tea.html")
    if request.form["password"] == request.form["conf_password"] and str(hashlib.sha256(
            b"%a" % str(request.form["password"])).digest()) == current_user.password_hash:
        current_user.name = request.form["name"]
        current_user.email = request.form["email"]
        if not request.form["name"] or not request.form["email"]:
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
            if today < datetime.datetime.now(JST):
                del_lim()
        except:
            del_lim()
            today = datetime.datetime.now(JST)
        jsons = {i: "" for i in day.replace(" ", "").split(";")}
        for date in day.split(";"):
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
    except Exception:
        abort(500)


@app.route("/json/class/<depart>")
def json_depart(depart):
    try:
        try:
            global today
            if today < datetime.datetime.now(JST):
                del_lim()
        except:
            del_lim()
            today = datetime.datetime.now(JST)
        tmp = sum([dat_rev[class_] for class_ in depart.upper().replace(" ", "").split(";")])
        p = Entry.query.filter(Entry.published, Entry.target_depart.op("&")(tmp)).order_by(Entry.target_depart).all()

        json = {
            "all_match": {str(i): json_it(m) for i, m in enumerate(p)
                          }
        }
        json["all_match"]["count"] = len(p)
        for class_ in int2classes(tmp):
            json[class_] = dict()
            json[class_]["count"] = 0
        for change in p:
            if change.target_depart & tmp:
                for class_ in int2classes(change.target_depart & tmp):
                    json[class_][str(len(json[class_]))] = json_it(change)
                    json[class_]["count"] += 1
        return jsonify(json)
    except Exception:
        abort(500)


@app.route("/json/reference")
def api_reference():
    return render_template("reference.html")


@app.route("/edit/<int:num>", methods=["GET", "POST"])
@login_required
def edit(num=0):
    p = Entry.query.filter(Entry.changeid.in_([num])).first()
    if not p:
        return render_template("404.html")
    global dat
    if current_user.is_teacher():
        if request.method == "POST":
            class_ = 0
            for key, value in request.form.items():
                if key == "all":
                    class_ = bins[0]
                    break
                if key[:5] == "radio":
                    class_ += int(value)
            if class_:
                p.target_depart = class_
            if p.contributor != current_user.id:
                abort(404)
            p.change_from_date = request.form["from_date"]
            p.change_from_class = request.form["from_class"]
            p.change_from_time = request.form["from_time"]
            p.change_from_teacher = request.form["from_teacher"]
            p.change_to_date = request.form["to_date"]
            p.change_to_class = request.form["to_class"]
            p.change_to_time = request.form["to_time"]
            p.change_to_teacher = request.form["to_teacher"]
            p.remark = request.form["remark"]
            if str(request.form["delete"]) == str(request.form["del_string"]):
                db.session.delete(p)
                db.session.commit()
                return redirect("/")
            db.session.commit()
        return render_template("edit.html", page=p, dat=dat, del_string=random.randint(1000, 9999),
                               int2classes=int2classes, teacher="", clerk="disabled")
    if request.method == "POST":
        p.changeid = request.form["number"]
        p.published = request.form["published"]
        p.timestamp = datetime.datetime.now(JST)
        if str(request.form["delete"]) == str(request.form["del_string"]):
            db.session.delete(p)
            db.session.commit()
            return redirect("/")
        p.publisher = current_user.id
        db.session.commit()
    return render_template("edit.html", page=p, dat=dat, del_string=random.randint(1000, 9999),
                           int2classes=int2classes, teacher="disabled", clerk="")


@app.route("/<passw>/count")
def count(passw):
    if passw == count_pass:
        return render_template("count.html", que=ViewCount.query.all())
    else:
        return redirect("404.html")


@app.route("/proposal", methods=["GET", "POST"])
def proposal():
    if request.method == "GET":
        return render_template("proposal.html")
    else:
        prop = Proposal(body=request.form["string"], ip=request.remote_addr)
        db.session.add(prop)
        db.session.commit()
        flash("メッセージが投稿されました。")
        return render_template("proposal.html")


@app.route("/proposals/<passw>")
def proposals(passw):
    if passw == proposal_pass:
        txt = "<table border=\"1\" width=\"400\"><tr><th>timestamp</th><th>ip</th><th>body</th></tr>"
        for prop in Proposal.query.all():
            txt += "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(prop.timestamp, prop.ip, prop.body)
        txt += "</table>"
        return txt
    else:
        abort(404)


@app.route("/flush")
@login_required
def flush():
    del_lim()
    return "flushed!"


@app.route("/<passw>/static/<filename>")
def static_dir(passw, filename):
    if passw == count_pass:
        return send_from_directory("static", filename)
    else:
        return redirect("404.html")


@app.route("/<passw>/image/<filename>")
def image_dir(passw, filename):
    if passw == count_pass:
        return send_from_directory("image", filename)
    else:
        return redirect("404.html")


@app.route("/file/<filename>")
@login_required
def files(filename):
    return send_from_directory("./", filename)


@app.route("/to_pdf/<id_>")
def to_pdf(id_):
    col = {"m": "#d6331d", "e": "#ffac3f", "c": "#6da5ff", "a": "#8fb70b", "all": "#250d00"}
    art = Entry.query.filter(Entry.changeid.in_([id_])).first()
    if not art:
        abort(404)
    depart = art.target_depart
    if depart == 24576:
        depart = "4E"
        color = col["e"]
    elif depart == 786432:
        depart = "5E"
        color = col["e"]
    elif depart == 15:
        depart = "1年"
        color = col["all"]
    elif depart == 240:
        depart = "2年"
        color = col["all"]
    elif depart == 3840:
        depart = "3年"
        color = col["all"]
    elif depart == 126976:
        depart = "4年"
        color = col["all"]
    elif depart == 4063232:
        depart = "5年"
        color = col["all"]
    elif depart == 12582912:
        depart = "専攻科1年"
        color = col["all"]
    elif depart == 50331648:
        depart = "専攻科2年"
        color = col["all"]
    elif depart == 4194303:
        depart = "本科生"
        color = col["all"]
    elif depart in {134217726, 67108863}:
        depart = "全学生"
        color = col["all"]
    elif depart == 62914560:
        depart = "専攻科生"
        color = col["all"]
    else:
        dep = int2classes(depart)
        depart = ",".join(dep)
        if len(dep) != 1:
            color = col["all"]
        else:
            color = col[depart[-1].lower()]

    under = "{}月{}日 学生課 No.{}".format(int(datetime.datetime.now(JST).strftime("%m")),
                                      int(datetime.datetime.now(JST).strftime("%d")), art.changeid)

    situ = "と振替える" if art.change_from_teacher and art.change_to_teacher else "に移動する" if art.change_from_date and art.change_to_date else "休講とする"

    if art.change_from_date == art.change_to_date and art.change_from_teacher == art.change_to_teacher and art.change_from_class == art.change_to_class:
        situ = art.remark
        art.change_to_class = ""
        art.change_to_date = "none"
        art.change_to_teacher = ""

    return render_template("to_pdf.html", datetime=datetime, dat=dat, art=art, depart=depart, map=map, int=int,
                           list=list, under=under, situ=situ, color=color)


def feed_cookie(content, cookie):
    response = make_response(content)
    max_age = 60 * 60 * 24 * 120
    response.set_cookie("depart", value=str(cookie), max_age=max_age)
    response.set_cookie("last_seen", value=datetime.datetime.now(JST).strftime("%Y-%m-%d-%H-%M-%S"), max_age=max_age)
    return response


def get_dep_cookie(cookie):
    return int(cookie.get("depart"))


def json_it(entry):
    global dat
    json = {
        "from": {
            "class": entry.change_from_class,
            "date": entry.change_from_date,
            "time": entry.change_from_time,
            "User": entry.change_from_teacher
        },
        "to": {
            "class": entry.change_to_class,
            "date": entry.change_to_date,
            "time": entry.change_to_time,
            "User": entry.change_to_teacher
        },
        "depart": ";".join(int2classes(entry.target_depart)),
        "remark": entry.remark
    }
    return json


def del_lim():
    p = Entry.query.all()
    deleted = False
    for ent in p:
        try:
            bef = datetime.datetime(*list(map(int, ent.change_from_date.split("-"))), tzinfo=JST)
        except:
            bef = datetime.datetime(1, 1, 1, tzinfo=JST)
        try:
            to = datetime.datetime(*list(map(int, ent.change_to_date.split("-"))), tzinfo=JST)
        except:
            to = datetime.datetime(1, 1, 1, tzinfo=JST)
        if max(bef, to) < datetime.datetime.now(JST):
            db.session.delete(ent)
            deleted = True
    if deleted:
        db.session.commit()


if __name__ == "__main__":
    if not os._exists("database.db"):
        db.create_all()
    app.secret_key = os.urandom(12)
    app.run(debug=False, host="0.0.0.0", port=8080, threaded=True)
