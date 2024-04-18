from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
def index():
    username='jeromepalayoor'
    return render_template('index.html',username=username)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/user')
@app.route('/users')
def users():
    return render_template('username.html')

@app.route('/user/<username>', methods = ['GET', 'POST'])
@app.route('/users/<username>', methods = ['GET', 'POST'])
def username_route(username):
    return render_template('username.html', username=username)

@app.route('/upload',methods=['GET','POST'])
def upload():
    return render_template('upload.html')


app.run()