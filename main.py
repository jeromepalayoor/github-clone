from flask import Flask, render_template, request, redirect
import sqlite3
import jwt
from datetime import datetime

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

def get_user():
    username = None
    if 'username' in request.cookies:
        username = decode_jwt(request.cookies['username'])['username']

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    conn.close()

    if not user:
        return None
    return username

@app.route('/index')
@app.route('/')
def index():
    username = get_user()
    return render_template('index.html',username=username)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    username = get_user()
    if username:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        conn.close()
        if user:
            response = redirect('/')
            response.set_cookie('username', encode_jwt({'username': username}))
            return response
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods = ['GET', 'POST'])
def register():
    username = get_user()
    if username:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cur.fetchone()
        if user:
            return render_template('register.html', error='Username already exists')
        cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return redirect('/users/'+username)
    
    return render_template('register.html', error=None)

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
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    if not user:
        return render_template('error.html', error='User not found')
    
    cur.execute('SELECT * FROM repos WHERE userid = (SELECT userid FROM users WHERE username = ?)', (username,))
    repos = cur.fetchall()
    conn.close()
    return render_template('username.html', username=username, username_logged_in=username_logged_in, repos=repos)

@app.route('/upload',methods=['GET','POST'])
def upload():
    return render_template('upload.html')

@app.route('/logout')
def logout():
    response = redirect('/')
    response.set_cookie('username', '', expires=0)
    return response

@app.route('/create_repo',methods=['GET','POST'])
def create_repo():
    username = get_user()
    if username == None:
        return render_template('login.html', error='Please login to create a repository')
    if request.method == 'POST':
        name = request.form['name']
        # validate name, only contain alphanumeric characters and underscores
        for c in name:
            if not c.isalnum() and c != '_':
                return render_template('create_repo.html', error='Invalid repository name')
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM repos WHERE name = ? AND userid = (SELECT userid FROM users WHERE username = ?)', (name, username))
        repo = cur.fetchone()
        conn.close()
        if repo:
            return render_template('create_repo.html', error='Repository already exists')
        time_now = datetime.now().timestamp()
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO repos (userid, name, last_updated) VALUES ((SELECT userid FROM users WHERE username = ?), ?, ?)', (username, name, time_now))
        conn.commit()
        conn.close()
        return redirect('/users/'+username+'/'+name)
    return render_template('create_repo.html', error=None)

@app.route('/users/<username>/<reponame>')
def reponame_route(username, reponame):
    username_logged_in = get_user()
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM repos WHERE name = ? AND userid = (SELECT userid FROM users WHERE username = ?)', (reponame, username))
    repo = cur.fetchone()
    if not repo:
        return render_template('error.html', error='Repository not found')
    cur.execute('SELECT name FROM files WHERE repoid = ?', (repo[0],))
    files = cur.fetchall()
    conn.close()
    return render_template('reponame.html', username=username, reponame=reponame, username_logged_in=username_logged_in, files=files)

@app.route('/users/<username>/<reponame>/<filename>', methods = ['GET', 'POST'])
def filename_route(username, reponame, filename):
    username_logged_in = get_user()
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM repos WHERE name = ? AND userid = (SELECT userid FROM users WHERE username = ?)', (reponame, username))
    repo = cur.fetchone()
    if not repo:
        return render_template('error.html', error='Repository not found')
    cur.execute('SELECT * FROM files WHERE name = ? AND repoid = ?', (filename, repo[0]))
    file = cur.fetchone()
    if not file:
        return render_template('error.html', error='File not found')
    if request.method == 'POST':
        contents = request.form['contents']
        time_now = datetime.now().timestamp()
        cur.execute('UPDATE files SET contents = ?, last_updated = ? WHERE fileid = ?', (contents, time_now, file[0]))
        conn.commit()
        conn.close()
        return redirect('/users/'+username+'/'+reponame+'/'+filename)
    conn.close()
    return render_template('filename.html', username=username, reponame=reponame, filename=filename, contents=file[3], username_logged_in=username_logged_in)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='Page not found'), 404

app.run()