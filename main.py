from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json


#app initiates here
app = Flask(__name__)



#config file gets read
with open("config.json", "r") as c:
    params = json.load(c)["params"]      #loading the parameters here from config file

local_server =  True

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db=SQLAlchemy(app)    #initailaisation of db variable



#we will define variables here for sending email
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',  #default gmail parameter
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail_user"],
    MAIL_PASSWORD = params["gmail_password"]

)

mail = Mail(app)   #initailaisation of mail variable


#now we will form a class, which will define database tables
class Registration(db.Model):
    reg_id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    Phone = db.Column(db.String(50), nullable=False)
    Country = db.Column(db.String(50), nullable=False)
    Services = db.Column(db.String(100), nullable=False)
    Date = db.Column(db.String(120),nullable=True)


class Services(db.Model):
    ser_no = db.Column(db.Integer, primary_key=True)
    ser_title = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(50), nullable=False)
    img_file = db.Column(db.String(50), nullable = True)





@app.route('/')
def home():
    return render_template('index.html', params=params)



@app.route('/admin')
def admin():
    return render_template('admin.html', params=params)



@app.route("/registration", methods = ['GET', 'POST'])
def registration():
    if(request.method=='POST'):
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        country=request.form.get('country')
        services=request.form.get('services')
        entry = Registration(Name=name, email=email, Phone=phone, Country=country, Services=services, Date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('Message from' + name,
                          sender = email, recipients = [params['gmail_user']],
                          body = services + phone)

    return render_template('registration.html', params=params)


@app.route("/services/<string:service_item>", methods=['GET'])
def service_route(service_item):
    services=Services.query.filter_by(slug=service_item).first()


    return render_template('services_slug.html',params=params, services=services)



@app.route("/services")
def services():
    items = Services.query.filter_by().all()
    print(items)
    return render_template('services.html', params=params, items=items)



app.run(debug=True)
