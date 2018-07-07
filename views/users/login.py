from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
#from database import getDB
#from models import User
#from views.utils import printException, cleanRecordID, looksLikeEmailAddress
#from views.user import findUser
from instance.site_settings import SECRET_KEY
from time import sleep
import hmac
import hashlib
import random

mod = Blueprint('login',__name__)

db = None

def setExits():
   db = getDB()
   g.title = 'Login'

@mod.route('/login', methods=['POST'])
@mod.route('/login/', methods=['POST'])
def login():
    setExits()
    
    g.user = g.get('user', None)
    if g.user is not None:
        flash("Already Logged in...")
        return redirect(url_for("home"))
        
    if not request.form:
        if 'loginTries' not in session:
            session['loginTries'] = 0
        
    if request.form:
        if 'loginTries' not in session:
            #Testing that user agent is keeping cookies.
            #If not, there is no point in going on... Also, could be a bot.
            return render_template('login/no-cookies.html')
                
        if validateUser(request.form["password"],request.form["userNameOrEmail"]):
            setUserSession(request.form["userNameOrEmail"].strip())
            return redirect(url_for("home"))
        else:
            flash("Invalid User Name or Password")
        
    if 'loginTries' not in session:
        session['loginTries'] = 0
        
    #remember howmany times the user has tried to log in
    session['loginTries'] = session['loginTries'] + 1
    #slow down login attempts
    if session['loginTries'] > 5:
        sleep(session['loginTries']/.8)
        
    return render_template('login/user_login.html', form=request.form)
       
#def validateUser(password,userNameOrEmail):
#    if password and userNameOrEmail: 
#        password = password.strip()
#        userNameOrEmail = userNameOrEmail.strip()
#        #Check for a password match
#        passHash = getUserPasswordHash(userNameOrEmail)
#        if passHash != '':
#            if matchPasswordToHash(password,passHash):
#                return setUserStatus(userNameOrEmail)
#            
#            
#    return False
#    
#    
#@mod.route('/logout', methods=['GET'])
#@mod.route('/logout/', methods=['GET'])
#def logout():
#    session.clear()
#    g.user = None
#    flash("Successfully Logged Out")
#    return redirect(url_for("home"))
    
    
def setUserSession(userNameOrEmail):
    session["user"] = userNameOrEmail
        
def matchPasswordToHash(pw,passHash):
    if pw and passHash:
        s = passHash.split('.')
        if len(s) != 3:
            return False
        salt = s[0]
        timesAround = s[1]
        hashToTest = getPasswordHash(pw,salt,timesAround)
        if hashToTest == passHash:
            return True
        
    return False
    
def getUserPasswordHash(emailOrUserName=''):
    includeInactive = True
    rec = findUser(emailOrUserName.strip(),includeInactive)
    if rec:
        return rec.password
        
    return ""
    
def setUserStatus(emailOrUserName):
    if emailOrUserName == None:
        return False
    emailOrUserName = emailOrUserName.strip()
    rec = findUser(emailOrUserName)
    if rec:
        g.user = emailOrUserName
        g.role = rec.role
        g.orgID = rec.organization_ID
        
        if g.role == "super" and ('superOrgID' in session) :
            ## super user is managing another organization's data
            if 'superOrgID' in session:
                g.orgID = int(session.get('superOrgID'))
        
        return True
    else:
        flash("User is not on file")
        return False
           
def getPasswordHash(pw, theSalt=None, timesAround='05',encoding='utf-8'):
    if type(pw) is str or type(pw) is unicode:
        pw = pw.strip()
        if not theSalt:
            theSalt = getPasswordSalt()
        codeWord = str(pw) + theSalt
        
        for i in range(int(timesAround) * 1000):
            codeWord = hmac.new(bytearray(SECRET_KEY.encode(encoding)), str(codeWord).encode(encoding), hashlib.sha256).hexdigest() 
        return theSalt +'.'+timesAround+'.'+codeWord
    return "" #test this for error
    
def getPasswordSalt():
    theChars = '0123456789abcdef'
    s = random.sample(theChars,16)
    salt = ''
    for i in range(len(s)):
        salt = salt + s[i]
        
    return salt
    
