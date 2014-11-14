# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response, json
from contextlib import closing
import os
import requests

UPLOAD_FOLDER = 'pictures'
IP = '127.0.0.1'
PORT = 8000
URL = 'http://' + IP + ':' + str(PORT)
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_pyfile('my_config', silent=True)

# preprocess
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()





# server
@app.route('/albums', methods=['GET', 'POST'])
def getAlbums():
    params = {}
    username = None
    if 'username' in request.cookies and 'logged_in' in request.cookies and request.cookies['logged_in']=='1':
        params['username'] = request.cookies['username']
        username = params['username']

    if 'logged_in' in request.cookies and request.cookies['logged_in']=='1':
        params['logged_in'] = '1'
    else:
        params['logged_in'] = '0'

    users = os.listdir(UPLOAD_FOLDER)
    params['entries'] = []
    for user in users:
        if user[0] != '.':
            for filename in os.listdir(UPLOAD_FOLDER + '/' + user):
                if filename[0] != '.':
                    params['entries'].append({'title': filename, 'path': URL + '/' + UPLOAD_FOLDER + '/' + user + '/' + filename, 'isTheUser': user == username, })
    # print params['entries']
    return json.dumps(params) 

@app.route('/pictures/<username>/<filename>', methods=['GET', 'POST', 'DELETE'])
def getPicture(username, filename):
    targetFile = UPLOAD_FOLDER + '/' + username + '/' + filename
    if request.method == 'GET':
        if os.path.isfile(targetFile):
            return Response(open(targetFile, 'r').read(), mimetype='image/' + filename.split('.')[-1])
        abort(401)
    
    if request.method == 'POST':

        if request.cookies.get('logged_in') != '1':
            abort(401)

        content = request.data

        if filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS:
            targetPath = UPLOAD_FOLDER + '/' + request.cookies.get('username')
            if not os.path.isdir(targetPath):
                os.mkdir(targetPath)
                tempFile = open(os.path.join(targetPath, filename), 'wb')
                tempFile.write(content)
                tempFile.close()
            elif os.path.isfile(os.path.join(targetPath, filename)):
                return 'error: repeated picture' 
            else:
                tempFile = open(os.path.join(targetPath, filename), 'wb')
                tempFile.write(content)
                tempFile.close()
        return 'success: New picture was successfully posted'

    if request.method == 'DELETE':
        if request.cookies.get('logged_in') == '1' and username == request.cookies.get('username'):
            if os.path.isfile(targetFile):
                try:
                    os.remove(targetFile)
                    resp = Response('success: delete /pictures/%s' % (username + '/' + filename))
                    return resp
                except:
                    resp = Response('error: failed to delete /pictures/$s' % (username + '/' + filename))
                    return resp
            else:
                resp = Response('error: invalid url')
                return resp
        else:
            return 'error: unauthorized'

@app.route('/users/<username>/<password>', methods=['GET', 'POST', 'DELETE'])
def userService(username, password):
    error = None

    if request.method == 'GET':
        cur = g.db.execute('select username, password from users where username = ?', [username,])
        result = cur.fetchone()
        if not result: 
            error = 'no such username'
            return 'failed: no such user name'
        elif password != result[1]: 
            error = 'Invalid password'
            return 'failed: invalid password'
        else:
            resp = Response('success: log in')
            resp.set_cookie('logged_in', '1')
            resp.set_cookie('username', username)
            return resp 
    # sign in
    if request.method == 'POST':
        cur = g.db.execute('select username from users where username = ?', [username, ])
        result = cur.fetchone()
        if result:
            return 'error: the username has existed'
        else:
            g.db.execute('insert into users (username, password) values (?, ?)', [username, password])
            g.db.commit()
            return 'success: account created'
    # log out
    if request.method == 'DELETE':
        resp = Response('success: log out')
        resp.set_cookie('logged_in', '0')
        resp.set_cookie('username', 'None')
        return resp 



if __name__ == '__main__':
    app.run(host=IP, port=PORT)


