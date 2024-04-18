from flask import Flask, render_template, request, redirect
import sqlite3
import jwt

def configure_database():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        userid INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS repos (
        repoid INTEGER PRIMARY KEY AUTOINCREMENT,
        userid INTEGER NOT NULL,
        name TEXT NOT NULL,
        last_updated TEXT NOT NULL,
        FOREIGN KEY (userid) REFERENCES users (userid)
    )
    ''')
    conn.commit()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS files (
        fileid INTEGER PRIMARY KEY AUTOINCREMENT,
        repoid INTEGER NOT NULL,
        name TEXT NOT NULL,
        contents TEXT NOT NULL,
        last_updated TEXT NOT NULL,
        FOREIGN KEY (repoid) REFERENCES repos (repoid)
    )
    ''')
    conn.commit()                

    conn.close()

app = Flask(__name__)
app.secret_key = 'secret_key'
configure_database()

def encode_jwt(payload):
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

def decode_jwt(token):
    return jwt.decode(token, app.secret_key, algorithms=['HS256'])

def get_user(username):
    username = None
    if 'username' in request.cookies:
        username = decode_jwt(request.cookies['username'])['username']
    return username

@app.route('index')
@app.route('/')
def index():
    username = get_user()
    return render_template('index.html',username=username)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    username = get_user()
    if username:
        return redirect('/')
    return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    username = get_user()
    if username:
        return redirect('/')
    return render_template('register.html')

@app.route('/user')
@app.route('/users')
def users():
    username = get_user()
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT username FROM users')
    users = cur.fetchall()
    conn.close()
    return render_template('users.html', users=users, username=username)

@app.route('/user/<username>', methods = ['GET', 'POST'])
@app.route('/users/<username>', methods = ['GET', 'POST'])
def username_route(username):
    username_logged_in = get_user()
    return render_template('username.html', username=username, username_logged_in=username_logged_in)

app.run()