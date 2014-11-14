from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, Response, json
from contextlib import closing

from suds.client import Client
import base64
import json
import os

UPLOAD_FOLDER = 'pictures'
IP = '127.0.0.1'
PORT = 9001
URL = 'http://' + IP + ':' + str(PORT)
TARGET_URL = 'http://127.0.0.1:9000'

app = Flask(__name__)
app.config.from_pyfile('my_config', silent=True)


client = Client('%s/?wsdl' % (TARGET_URL,))
# client
@app.route('/', methods=['GET', 'POST'])
def index():
    # TODO
    return redirect(url_for('showAlbums'))

@app.route('/client/show_albums', methods=['GET', 'POST'])
def showAlbums():
	# ---- get albums ----
	result = list(client.service.get_albums())[0][1]
	# print result
	temp = {}
	temp['entries'] = []
	temp['username'] = request.cookies.get('username')
	temp['logged_in'] = request.cookies.get('logged_in')	

	params = json.loads(result[-1])
	if params:
		# print params
		for i in range(len(result)-1):
			filestream = result[i]
			if not os.path.isdir('%s/%s' % (UPLOAD_FOLDER, params[str(i)]['username'],)):
				os.mkdir('%s/%s' % (UPLOAD_FOLDER, params[str(i)]['username'],))
			with open('%s/%s/%s' % (UPLOAD_FOLDER, params[str(i)]['username'], params[str(i)]['filename']), 'wb') as fd:
				filestream = base64.decodestring(filestream)		
				fd.write(filestream)
				temp['entries'].append({'title': params[str(i)]['filename'], 'path': URL + '/' + UPLOAD_FOLDER + '/' + params[str(i)]['username'] + '/' + params[str(i)]['filename'], 'isTheUser': params[str(i)]['username']==temp['username']})

	params = temp		
	# print params
	
	return render_template('show_albums.html', params=params)


@app.route('/client/log_in', methods=['GET', 'POST'])
def logIn():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        result = client.service.log_in(username, password)
        if result.find('success') == 0:
			tempCookies = dict(request.cookies)
			tempCookies['username'] = username
			tempCookies['logged_in'] = '1'
			request.cookies = tempCookies
			html = showAlbums()
			resp = Response(html, )
			resp.set_cookie('username', username)
			resp.set_cookie('logged_in', '1')
			resp.set_cookie('password', password)
			return resp
        else:
        	error = result

    return render_template('login.html', error=error)
        

@app.route('/client/log_out', methods=['GET', 'POST'])
def logOut():
    if 'username' in request.cookies:
    	username = request.cookies.get('username')
    	password = request.cookies.get('password')
        result = client.service.log_out(username, password)
        if result.find('success') == 0:
			tempCookies = dict(request.cookies)
			tempCookies['logged_in'] = '0'
			request.cookies = tempCookies
			html = showAlbums()
			resp = Response(html, )
			resp.set_cookie('username', username, expires=0)
			resp.set_cookie('logged_in', '1', expires=0)
			resp.set_cookie('password', password, expires=0)
			return resp
        else:
        	return result
    
    else:
        return 'error: username is not in the cookie'

@app.route('/client/sign_in', methods=['GET', 'POST'])
def signIn():
    error = None
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form:
	    	username = request.form.get('username')
	    	password = request.form.get('password')
	        result = client.service.sign_in(username, password)
	        if result.find('success') == 0:

				return redirect(url_for('showAlbums'))
	        else:
	        	error = result
        else:
            error = 'error: invalid input form'    

    return render_template('signin.html', error=error)


@app.route('/client/add_picture', methods=['POST'])
def addPicture():
    uploadFile = request.files['file']
    filestream = base64.encodestring(uploadFile.read())
    filename = request.form.get('title') + '.' + request.files['file'].filename.split('.')[-1]
    result = client.service.upload_picture(request.cookies.get('username'), filename, filestream)
    if result.find('success') == 0:
        return redirect(url_for('showAlbums'))
    else:
        return result


@app.route('/client/delete_picture', methods=['GET', 'POST'])
def deletePicture():
    if request.method == 'GET' or request.method == 'POST':
        if request.form.get('deletefile'):
			targetFile = request.form['deletefile']
			username = targetFile.strip('/').split('/')[-2]
			filename = targetFile.strip('/').split('/')[-1]
			# ---- delete picture ----
			result = client.service.delete_picture(username, filename)
			if result.find('success') != -1:
				flash('success: delete the picture %s' % filename)
				return redirect(url_for('showAlbums'))

	return 'error: failed to delete the file'

# server
@app.route('/pictures/<username>/<filename>', methods=['GET', 'POST'])
def get_picture(username, filename):
    targetFile = UPLOAD_FOLDER + '/' + username + '/' + filename
    if request.method == 'POST' or request.method == 'GET':
        if os.path.isfile(targetFile):
            return Response(open(targetFile, 'r').read(), mimetype='image/' + filename.split('.')[-1])
        abort(401)




if __name__ == '__main__':
    app.run(host=IP, port=PORT)







# if __name__=='__main__':
# 	client = Client('http://localhost:9999/?wsdl')
	# print client
	# ---- upload picture ----
	# pictureFile = open('test1.jpg', 'r')
	# filestream = base64.encodestring(pictureFile.read()) 
	# filename = 'test1.jpg'
	# result = client.service.upload_picture('admin', filename, filestream)
	# ---- delete picture ----
	# result = client.service.delete_picture('admin', 'hello.jpg')
	# ---- get albums ----
	# result = list(client.service.get_albums())[0][1]
	# print result
	# params = json.loads(result[-1])
	# if params:
	# 	print params
	# 	for i in range(len(result)-1):
	# 		filestream = result[i]
	# 		if not os.path.isdir('pictures/%s' % (params[str(i)]['username'],)):
	# 			os.mkdir('pictures/%s' % (params[str(i)]['username'],))
	# 		with open('pictures/%s/%s' % (params[str(i)]['username'], params[str(i)]['filename']), 'wb') as fd:
	# 			filestream = base64.decodestring(filestream)		
	# 			fd.write(filestream)
		

