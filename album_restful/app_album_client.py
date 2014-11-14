# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response, json
from contextlib import closing
import os
import requests

UPLOAD_FOLDER = 'pictures'
IP = '127.0.0.1'
PORT = 8001
URL = 'http://' + IP + ':' + str(PORT)
TARGET_URL = 'http://127.0.0.1:8000'

app = Flask(__name__)
app.config.from_pyfile('my_config', silent=True)

# client
@app.route('/', methods=['GET', 'POST'])
def index():
    # TODO
    return redirect(url_for('showAlbums'))

@app.route('/client/show_albums', methods=['GET', 'POST'])
def showAlbums():
    # http GET /albums
    r = requests.get(TARGET_URL + '/albums', cookies=request.cookies)
    if r.status_code == requests.codes.ok:
        params = json.loads(r.text)
        print params
        return render_template('show_albums.html', params=params)
    else:
        return 'error: can not GET %s' % (TARGET_URL + '/albums', )

@app.route('/client/log_in', methods=['GET', 'POST'])
def logIn():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        tempResponse = requests.get(TARGET_URL + '/users/%s/%s' % (username, password))
        if tempResponse.status_code == requests.codes.ok:
            
            if tempResponse.text.find('success') != -1:
                
                tempCookies = dict(tempResponse.cookies)
                request.cookies = tempCookies
                html = showAlbums()
                response = Response(html, )

                for key in tempCookies:
                    response.set_cookie(key, tempCookies[key])
                return response
            else:
                error = 'invalid username of password'

        else:
            return 'error: can not access %s' % (TARGET_URL)

    return render_template('login.html', error=error)
        

@app.route('/client/log_out', methods=['GET', 'POST'])
def logOut():
    if 'username' in request.cookies:
        tempResponse = requests.delete(TARGET_URL + '/users/%s/%s' % (request.cookies['username'], 'xxxx'))
        if tempResponse.status_code == requests.codes.ok:
            
            if tempResponse.text.find('success') != -1:
                tempCookies = dict(tempResponse.cookies)
                r = requests.get(TARGET_URL + '/albums', cookies=tempCookies)
                if r.status_code == requests.codes.ok:
                    params = json.loads(r.text)
                    response = Response(render_template('show_albums.html', params=params), )
                    
                    for key in tempCookies:
                        response.set_cookie(key, tempCookies[key])
                    return response
                else:
                    return 'error: can not GET %s' % (TARGET_URL + '/albums', )

            else:
                return 'error: fail to log out'

        else:
            return 'error: can not access %s' % (TARGET_URL)
    
    else:
        return 'error: username is not in the cookie'

@app.route('/client/sign_in', methods=['GET', 'POST'])
def signIn():
    error = None
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
            tempResponse = requests.post(TARGET_URL + '/users/%s/%s' % (request.form['username'], request.form['password']))
            if tempResponse.status_code == requests.codes.ok:
                if tempResponse.text.find('success') != -1:
                    return showAlbums()
                else:
                    error = 'error: invalid username or password'
            else:
                return 'error: cannot access server'
        else:
            return 'error: invalid input form'    
    return render_template('signin.html', error=error)


@app.route('/client/add_picture', methods=['POST'])
def addPicture():
    tempUrl = TARGET_URL + '/pictures/%s/%s' % (request.cookies.get('username'), request.form.get('title') + '.' + request.files['file'].filename.split('.')[-1], )
    uploadFile = request.files['file']
    r = requests.post(tempUrl, data=uploadFile.read(), cookies=request.cookies)
    if r.text.find('success') != -1:
        return redirect(url_for('showAlbums'))
    else:
        return r.text


@app.route('/client/delete_picture', methods=['GET', 'POST'])
def deletePicture():
    if request.method == 'GET' or request.method == 'POST':
        if request.form.get('deletefile'):
            targetFile = request.form['deletefile']
            username = targetFile.strip('/').split('/')[-2]
            filename = targetFile.strip('/').split('/')[-1]
            tempUrl = TARGET_URL + '/pictures/' + username + '/' + filename
            r = requests.delete(tempUrl, cookies=request.cookies)
            if r.text.find('success') != -1:
                flash('success: delete the picture %s' % filename)
                return redirect(url_for('showAlbums'))

    return 'error: failed to delete the file'




if __name__ == '__main__':
    app.run(host=IP, port=PORT)


