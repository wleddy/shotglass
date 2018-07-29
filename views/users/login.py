from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import sleep

from models import User
from views.users.password import getPasswordHash, matchPasswordToHash

mod = Blueprint('login',__name__, template_folder='templates')


def setExits():
    g.title = 'Login'
    
@mod.route('/login', methods=['POST', 'GET'])
@mod.route('/login/', methods=['POST', 'GET'])
def login():
    setExits()
    g.user = g.get('user',None)
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
        
        #print("db={}".format(db))
        rec = User(g.db).get(request.form["userNameOrEmail"],include_inactive=True)
        #print(rec)
        if rec and matchPasswordToHash(request.form["password"],rec.password):
            session['loginTries'] = 0
            if rec.active == 0:
                flash("Your account is inactive")
                return render_template('/login/inactive.html')
                
            # log user in...
            setUserStatus(request.form["userNameOrEmail"],rec.id)
            
            next = request.form.get('next','')
            if next:
                return redirect(next)
            return redirect(url_for('home')) #logged in...
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
       
    
@mod.route('/logout', methods=['GET'])
@mod.route('/logout/', methods=['GET'])
def logout():
    session.clear()
    g.user = None
    flash("Successfully Logged Out")
    return redirect(url_for("home"))
    
@mod.route('/reset', methods=['GET','POST'])
def reset_password():
    """Give user the chance to change recover a forgotten password
    Will send an email to the matching user"""
    
    return "Not implemented yet"
    
@mod.route('/signup', methods=['GET','POST'])
def register():
    """Allow user to signup for an account"""
    
    return "Not implemented yet"
    
def setUserStatus(userNameOrEmail,user_id):
    session["user"] = userNameOrEmail.strip()
    g.user = userNameOrEmail
    g.user_roles = User(g.db).get_roles(user_id)
    
    
