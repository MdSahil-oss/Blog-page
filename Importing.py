from datetime import datetime
from flask import Flask
from flask import render_template,request
from flask_sqlalchemy import SQLAlchemy
import json
import flask_mail
from flask import session
import os
from werkzeug.utils import redirect, secure_filename
import math

app = Flask(__name__)

with open('config.json','r') as c:
    params = json.load(c)["params"]
    
if params["localserver"] == 'True':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/usingflask'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/usingflask'
    
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = params['location_of_Saving_file']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["userID"],
    MAIL_PASSWORD = params["password"]
)
mail = flask_mail.Mail(app)
class Contactdata(db.Model):
    sno = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(30),nullable=False)
    phone_no= db.Column(db.String(12),nullable=False)
    email = db.Column(db.String(25),nullable=False)
    message = db.Column(db.String(150),nullable=False)
    date = db.Column(db.String(12),nullable=True)

class Posts(db.Model):
    Sno = db.Column(db.Integer,primary_key = True)
    Title = db.Column(db.String(50),nullable=False)
    slug = db.Column(db.String(20),nullable=False)
    Content = db.Column(db.String(30),nullable=False)
    date = db.Column(db.String(50),nullable=False)

@app.route("/")
def welcome():
    posts = Posts.query.filter_by().all()
    page = request.args.get('page')
    last = math.ceil(len(posts)/params["no_of_posts"])
    if not str(page).isnumeric():
        page=1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page == 1:
        prev='#'
        next='/?page='+str(page+1)
    elif page == last:
        prev='/?page='+str(page-1)
        next="#"
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)
    return render_template('index.html',params=params,posts=posts,next=next,prev=prev)
@app.route("/index")
def home():
    posts = Posts.query.filter_by().all()[0:params["no_of_posts"]]
    return render_template('index.html',params=params,posts=posts)
@app.route("/about")
def about():
    return render_template('about.html',params=params)
@app.route("/contact",methods=['GET','POST'])
def contact():
    if request.method=='POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        message = request.form.get('message')
        entry = Contactdata(name=name,phone_no=phone,email=email,message=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        msg=flask_mail.Message(subject=f'New Message form {name}',
            recipients = [f'{params["userID"]}'],
            body = message,
            sender = email
            )
        # print(msg)
        mail.send(msg)
            
    return render_template('contact.html',params=params)
@app.route("/post/<string:post_slug>",methods=['GET'])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)

@app.route("/login",methods= ['GET','POST'])
def login():
    posts = Posts.query.all()
    if 'user' in session and session['user'].lower()==params['userID'].lower():
        return render_template("dashbord.html",params=params,posts=posts)
    if request.method=='POST':
        global userId
        global password
        userId = request.form.get('userId')
        password = request.form.get('pass')
        if userId.lower()==params['userID'].lower() and password == params["password"]:
            posts = Posts.query.all()
            session['user'] = userId
            return render_template('dashbord.html',params=params,posts=posts)
    return render_template('login.html')

@app.route('/dashbord',methods = ['GET','POST'])
def dashbord():
    if 'user' in session and session['user'].lower()==params['userID'].lower():
        posts = Posts.query.all()
        return render_template('dashbord.html',params=params,posts=posts)
    if request.method == 'POST':
        global userId
        global password
        userId = request.form.get('userId').lower()
        password = request.form.get('pass')
        if(userId==params['userID'].lower() and password==params['password']):
            session['user'] = userId
            posts = Posts.query.all()
            return render_template('dashbord.html',params=params,posts=posts)
    return render_template('login.html')

@app.route('/postAdder')
def postAdder():
    posts = Posts.query.all()
    return render_template("postAdder.html",params=params,posts=posts)
@app.route('/editable/<string:sno>')
def edit(sno):
    
    post = Posts.query.filter_by(Sno = sno).first()
    return render_template("edit.html",params=params,posts=post)
@app.route('/edit/<string:sno>',methods= ['GET','POST'])
def postPosts(sno):
    
    if request.method == 'POST':        
        Sno = request.form.get('Sno')
        Title = request.form.get('Title')
        Content = request.form.get('Content')
        slug = request.form.get('slug')
        if sno == '0':
            print('Hey',Sno,Title,Content,slug)
            entry = Posts(Sno=Sno,Title=Title,Content=Content,slug = slug,date = datetime.now())
            db.session.add(entry)
            db.session.commit()
            
        else:
            post = Posts.query.filter_by(Sno=Sno).first()
            post.Sno = Sno
            post.Title = Title
            post.Content = Content
            post.slug = slug
            post.date = datetime.now()
            db.session.commit()
    posts = Posts.query.all()
    return render_template('dashbord.html',params=params,posts=posts)
@app.route('/uploader' ,methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user'].lower()==params['userID'].lower():
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config["UPLOAD_FOLDER"],secure_filename(f.filename)))
            return "Uploaded Successfully"
    return "Couldn't Upload"
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashbord')
@app.route('/delete/<string:sno>')
def delete(sno):
    if 'user' in session and session['user'].lower() == params['userID'].lower():
        post = Posts.query.filter_by(Sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashbord')
    
if __name__ == '__main__':
    app.secret_key = 'Super Secret Key'
    app.run(debug=True)