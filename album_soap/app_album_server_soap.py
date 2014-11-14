import soaplib
from soaplib.core import Application
from soaplib.core.server import wsgi
from soaplib.core.service import soap
from soaplib.core.service import DefinitionBase
from soaplib.core.model.primitive import String, Integer
from soaplib.core.model.clazz import ClassModel, Array
from soaplib.core.model.binary import Attachment

SERVICE_BASEDIR = 'service_basedir'
import json
import os
import base64

HOST_IP = '127.0.0.1'
HOST_PORT = 9000
HOST_ADDRESS = 'http://%s:%s' % (HOST_IP, str(HOST_PORT))

class AlbumsService(DefinitionBase):

    def isLoggedIn(username):
        usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'r')
        usersDict = json.loads(usersListFile.read())
        usersListFile.close()
        if username in usersDict and usersDict[username]['logged_in'] == 1:
            return True
        else:
            return False

    @soap(String, String, _returns=String)
    def log_in(self, username, password):
        usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'r')
        usersDict = json.loads(usersListFile.read())
        usersListFile.close()
        if username in usersDict and password == usersDict[username]['password']:
            usersDict[username]['logged_in'] = 1
            usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'w')
            strUsersDict = json.dumps(usersDict, indent=4)
            usersListFile.write(strUsersDict)
            usersListFile.close()
            return 'success: log in'
        else:        
            return 'error: invalid username or password'   

    @soap(String, String, _returns=String)
    def log_out(self, username, password):
        usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'r')
        usersDict = json.loads(usersListFile.read())
        usersListFile.close()
        if username in usersDict and password == usersDict[username]['password']:
            usersDict[username]['logged_in'] = 0
            usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'w')
            strUsersDict = json.dumps(usersDict, indent=4)
            usersListFile.write(strUsersDict)
            usersListFile.close()
            return 'success: log out'
        else:        
            return 'error: invalid username or password' 

    @soap(String, String, _returns=String)
    def sign_in(self, username, password):
        usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'r')
        usersDict = json.loads(usersListFile.read())
        usersListFile.close()
        if username not in usersDict:
            usersDict[username] = {'password': password, 'logged_in': 0}
            usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'w')
            strUsersDict = json.dumps(usersDict, indent=4)
            usersListFile.write(strUsersDict)
            usersListFile.close()
            return 'success: sign in'
        else:        
            return 'error: the conflict username'         

    @soap(String, String, String, _returns=String)
    def upload_picture(self, username, filename, filestream):
        filestream = base64.decodestring(str(filestream))
        usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'r')
        usersDict = json.loads(usersListFile.read())
        usersListFile.close()
        if username in usersDict and usersDict[username]['logged_in'] == 1:
            targetFile = SERVICE_BASEDIR + '/%s/%s' % (username, filename)
            targetDir = SERVICE_BASEDIR + '/' + username
            if os.path.isfile(targetFile):
                return 'error: the file has already existed'

            if not os.path.isdir(targetDir):
                os.mkdir(targetDir)

            tempFile = open(targetFile, 'wb')
            tempFile.write(filestream)
            tempFile.close()
            return 'success: upload the file'

        else:        
            return 'error: the user has not logged in'    

    @soap(String, String, _returns=String)
    def delete_picture(self, username, filename):
        usersListFile = open('%s/users_list' % (SERVICE_BASEDIR, ), 'r')
        usersDict = json.loads(usersListFile.read())
        usersListFile.close()
        if username in usersDict and usersDict[username]['logged_in'] == 1:
            targetFile = SERVICE_BASEDIR + '/%s/%s' % (username, filename)
            if not os.path.isfile(targetFile):
                return 'error: can not find the picture'
            else:
                os.remove(targetFile)
                return 'success: delete the file'

        else:        
            return 'error: the user has not logged in'  

    @soap(String, String, _returns=String)
    def get_picture(self, username, filename):       
        if isLoggedIn(username):
            targetFile = SERVICE_BASEDIR + '/%s/%s' % (username, filename)
            if not os.path.isfile(targetFile):
                return 'error: no such file'
            else:
                with open(targetFile, 'r') as fd:
                    filestream = base64.encodestring(fd.read())
                    return filestream
        else:        
            return 'error: the user has not logged in'

    @soap(_returns=Array(String))
    def get_albums(self):
        tempList = []  
        params = {}
        users = os.listdir(SERVICE_BASEDIR)
        for user in users:
            if user[0] != '.':
                if os.path.isdir(SERVICE_BASEDIR + '/' + user):
                    for filename in os.listdir(SERVICE_BASEDIR + '/' + user):
                        if filename[0] != '.':
                            targetFile = SERVICE_BASEDIR + '/%s/%s' % (user, filename)
                            with open(targetFile, 'r') as fd:
                                filestream = base64.encodestring(fd.read())
                                tempList.append(filestream)
                                params[str(len(tempList)-1)] = {'username': user, 'filename': filename}
        
        tempList.append(json.dumps(params))
        return tempList



if __name__=='__main__':
    try:
        from wsgiref.simple_server import make_server
        soap_application = soaplib.core.Application([AlbumsService, ], 'tns')
        wsgi_application = wsgi.Application(soap_application)

        print "listening to %s" % (HOST_ADDRESS, )
        print "wsdl is at: %s/?wsdl" % (HOST_ADDRESS, )

        server = make_server(HOST_IP, HOST_PORT, wsgi_application)
        server.serve_forever()

    except ImportError:
        print "Error: example server code requires Python >= 2.5"


