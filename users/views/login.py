from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import sleep, time
import random
from users.models import User
from users.views.password import getPasswordHash, matchPasswordToHash
from time import time

mod = Blueprint('login',__name__, template_folder='../templates')


def setExits():
    g.title = 'Login'
    g.loginURL = url_for('.login')
    g.recoverURL = url_for('.recover_password')
    g.logoutURL = url_for('.logout')
    g.registerURL = url_for('.register')
    
@mod.route('/login', methods=['POST', 'GET'])
@mod.route('/login/', methods=['POST', 'GET'])
def login():
    setExits()
    g.user = g.get('user',None)
    next = request.args.get('next',request.form.get('next',''))
    
    if g.user is not None:
        #flash("Already Logged in...")
        return redirect(url_for("home"))
        
    if 'reset' in request.args:
        #Try to find the user record that requested a reset
        rec=User(g.db).select_one(where='temp_password = "{}"'.format(request.args.get('reset','')).strip())
        if rec and rec.temp_password_expires > time():
            userNameOrEmail=rec.username
            if not userNameOrEmail:
                userNameOrEmail=rec.email
            setUserStatus(userNameOrEmail,rec.id)
            return redirect(url_for('user.edit'))
        else:
            flash("That reset request has expired")
            return redirect(url_for('home'))
            
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
        #next = 
        if rec and matchPasswordToHash(request.form["password"],rec.password):
            session['loginTries'] = 0
            if rec.active == 0:
                flash("Your account is inactive")
                return render_template('/login/inactive.html')
                
            # log user in...
            setUserStatus(request.form["userNameOrEmail"],rec.id)
            
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
        
    return render_template('login/login.html', form=request.form, next=next)
       
    
@mod.route('/logout', methods=['GET'])
@mod.route('/logout/', methods=['GET'])
def logout():
    session.clear()
    g.user = None
    flash("Successfully Logged Out")
    return redirect(url_for("home"))
    
@mod.route('/reset', methods=['GET','POST'])
def recover_password():
    """Send reset password and send user an email if they forget their password"""
    
    setExits()
    g.title = "Reset Password"
    rec=None
    temp_pass = None
    email_not_found = False
    
    if not request.form:
        pass
    else:
        #find the user with that email
        rec = User(g.db).select_one(where='email = "{}"'.format(request.form['email'].strip()))
        if rec == None:
            flash("That email address could not be found in the list of users.")
        else:
            # generate a new password that is unique to the system
            temp_rec = 'temp'
            while temp_rec != None:
                temp_pass = ""
                for x in range(22):
                    temp_pass += random.choice('abcdefghijklmnopqrstuvwxyz12344567890')
                #test that temp_pass is unique. break when rec == None
                temp_rec = User(g.db).select_one(where='temp_password = "{}"'.format(temp_pass))
                    
            # save the temporary password
            rec.temp_password = temp_pass
            rec.temp_password_expires = time() + (3600 * 48) # 2 days to reset
            User(g.db).save(rec)
            g.db.commit()
            
            # send an email with instructions
            from users.mailer import send_message
            full_name = rec.first_name + " " + rec.last_name
            context = {'temp_pass':temp_pass,'rec':rec,'full_name':full_name}
            result,msg = send_message(
                context,
                to_address_list=[(full_name,rec.email)],
                html_template='login/email/confirm_reset.html',
                text_template='login/email/confirm_reset.txt',
                subject = 'Confirm Password Reset'
                )
    
    # Return a page telling user what we did
    return render_template('login/recover_password.html',temp_pass=temp_pass,rec=rec)
    
@mod.route('/signup', methods=['GET','POST'])
def register():
    """Allow user to signup for an account"""
    
    return "Not implemented yet"
    
def setUserStatus(userNameOrEmail,user_id):
    #Log the user in
    user = User(g.db)
    user.update_last_access(user_id)
    session["user"] = userNameOrEmail.strip()
    g.user = userNameOrEmail
    g.user_roles = user.get_roles(user_id)
    
    
    
