import json
import math
import os
from datetime import datetime

from flask import Flask, render_template, request, session, redirect
# from passlib.hash import sha256_crypt
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from werkzeug import secure_filename

# from MySQLdb import escape_string as thwart


# app initiates here
app = Flask(__name__)
app.secret_key = 'mud123456789'

# config file gets read
with open("config.json", "r") as c:
    params = json.load(c)["params"]  # loading the parameters here from config file

local_server = True

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)  # initialisation of db variable

app.config["upload_folder"] = params["uploader_location"]

# we will define variables here for sending email
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',  # default gmail parameter
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_password"]

)

mail = Mail(app)  # initialisation of mail variable


# now we will form a class, which will define database tables
class Registration(db.Model):
    reg_id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    Phone = db.Column(db.String(50), nullable=False)
    Country = db.Column(db.String(50), nullable=False)
    Services = db.Column(db.String(100), nullable=False)
    Date = db.Column(db.String(120), nullable=True)


class Services(db.Model):
    ser_no = db.Column(db.Integer, primary_key=True)
    ser_title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(50), nullable=False)
    img_file = db.Column(db.String(50), nullable=False)


@app.route('/')
def home():
    return render_template('index.html', params=params)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    items = Services.query.filter_by().all()
    if 'user' in session and session['user'] == params['admin_user']:
        return render_template('dashboard.html', params=params, items=items)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password']:
            session['user'] = username
            return render_template('dashboard.html', params=params, items=items)

    return render_template('admin.html', params=params, items=items)


@app.route("/registration", methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        country = request.form.get('country')
        services = request.form.get('services')
        entry = Registration(Name=name, email=email, password=password, Phone=phone, Country=country, Services=services,
                             Date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('Message from ' + name,
                          sender=email, recipients=[params['gmail_user']],
                          body=services + phone)

    return render_template('registration.html', params=params)


@app.route("/services/<string:service_item>", methods=['GET'])
def service_route(service_item):
    services = Services.query.filter_by(slug=service_item).first()

    return render_template('services_slug.html', params=params, services=services)


@app.route("/services", methods=['GET'])
def services():
    s_items = Services.query.filter_by().all()
    # [0:params['no_of_ser']]
    print(len(s_items))
    last = math.ceil(len(s_items) / int(params['no_of_ser']))
    print(last)
    page = request.args.get('page')

    if not str(page).isnumeric():
        page = 1
    page = int(page)

    s_items = s_items[
              (page - 1) * int(params["no_of_ser"]): (page - 1) * int(params["no_of_ser"]) + int(params["no_of_ser"])]
    print(len(s_items))
    if page == 1:
        prev = "#"
        next = "/services?page=" + str(page + 1)

    elif page == last:
        prev = "/services?page=" + str(page - 1)
        next = "#"

    else:
        prev = "/services?page=" + str(page - 1)
        next = "/services?page=" + str(page + 1)

    return render_template('services.html', params=params, s_items=s_items, prev=prev, next=next)


@app.route("/edit/<string:serviceno>", methods=['GET', 'POST'])
def edit(serviceno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            title_ser = request.form.get('ser_title')
            content_ser = request.form.get('ser_content')
            slug_ser = request.form.get('ser_slug')
            img_ser = request.form.get('ser_img')

            if serviceno == '0':
                services_add = Services(ser_title=title_ser, content=content_ser, slug=slug_ser, img_file=img_ser)
                db.session.add(services_add)
                db.session.commit()

            else:
                services_modify = Services.query.filter_by(ser_no=serviceno).first()
                services_modify.ser_title = title_ser
                services_modify.content = content_ser
                services_modify.slug = slug_ser
                services_modify.img_file = img_ser
                db.session.commit()
                return redirect('/edit/' + serviceno)
        services_modify = Services.query.filter_by(ser_no=serviceno).first()

        return render_template('edit.html', params=params, serviceno=serviceno, services_modify=services_modify)


@app.route("/logout")
def logout():
    session.pop('user')
    return render_template('admin.html', params=params)


@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['upload_folder'], secure_filename(f.filename)))
            return "Uploaded successfully"  # change it


@app.route("/delete/<string:serviceno>", methods=['GET', 'POST'])
def delete(serviceno):
    if 'user' in session and session['user'] == params['admin_user']:
        items = Services.query.filter_by(ser_no=serviceno).first()
        db.session.delete(items)
        db.session.commit()
    return redirect('/admin')


@app.route("/users", methods=['GET', 'POST'])
def users():
    all_user = Registration.query.filter_by().all()
    if 'user' in session and session['user'] == params['admin_user']:
        return render_template('users.html', params=params, all_user=all_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username1 = request.form.get('rname')
        userpass1 = request.form.get('rpass')

        registered_user = Registration.query.filter_by(email=username1).first()
        session['email'] = username1
        if username1 == registered_user.email and userpass1 == registered_user.password:
            return render_template('registereduser.html', params=params, registered_user=registered_user)
    return render_template('loginuser.html', params=params)


@app.route("/logout_user")
def logout_user():
    session.pop('email')
    return render_template('loginuser.html', params=params)


if __name__ == '__main__':
    app.run(debug=True)
