from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import time
import re
from users.models import User, Role
from users.utils import printException, cleanRecordID, looksLikeEmailAddress
from users.views.login import matchPasswordToHash, setUserStatus, getPasswordHash

mod = Blueprint('user',__name__, template_folder='templates', url_prefix='/user')


def setExits():
    g.listURL = url_for('.home')
    g.adminURL = url_for('.admin',id=0)
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.homeURL = url_for('home')
    g.title = 'User'

@mod.route('/')
def home():
    setExits()
    return render_template('user/user_index.html')
    
@mod.route('/edit/<int:id>/', methods=['POST','GET'])
def admin(id=None):
    """Administrator access for the User table records
    """
    setExits()
    if not id:
        flash("No User identifier supplied")
        return redirect(g.listURL)
        
    #import pdb;pdb.set_trace()
        
    id = cleanRecordID(id)
    if(id < 0):
        flash("That is an invalid id")
        return redirect(g.listURL)
        
    #session['user_edit_token'] = id
    
    return edit(id)
    

## Edit the user
@mod.route('/edit', methods=['POST', 'GET'])
@mod.route('/edit/', methods=['POST', 'GET'])
def edit(user_handle=None):
    setExits()

    user = User(g.db)
    rec = None
    
    #import pdb;pdb.set_trace()
    
    if user_handle == 0:
        #new recod
        #update the form submission url to go to the admin method
        g.editURL = g.editURL + '{}/'.format(user_handle)
    elif user_handle:
        user_handle = cleanRecordID(user_handle)
        if user_handle < 0:
            flash("That is not a valid ID")
            return redirect(g.listURL)
    elif g.user != None:
        user_handle = g.user
    else:
        flash("You do not have access to that function")
        return redirect(g.homeURL)
        
    if not request.form:
        """ if no form object, send the form page """
        if not user_handle:
            # This should never happen
            flash("You do not have access to that area")
            return redirect(g.homeURL)
        elif user_handle == 0:
            rec = user.new()
        else:
            rec = user.get(user_handle)
            if not rec:
                flash("Unable to locate user record")
                return redirect(url_for('home'))
    else:
        #have the request form
        #import pdb;pdb.set_trace()
        if user_handle and request.form['id'] != 'None':
            rec = user.get(user_handle)
        else:
            # its a new unsaved record
            rec = user.new()
            user.update(rec,request.form)

        if validForm(rec):
        
            #Are we editing the current user's record?
            editingCurrentUser = ''
            if(g.user == rec.username):
                if 'new_username' in request.form:
                    editingCurrentUser = request.form['new_username'].strip()
                else:
                    editingCurrentUser = g.user
            else: 
                if(g.user == rec.email):
                    editingCurrentUser = request.form['email'].strip()
            
            #import pdb;pdb.set_trace()
            #update the record
            user.update(rec,request.form)
            #pdb.set_trace()
            
            #ensure a value for the check box
            rec.active = int(request.form.get('active','0'))
            
            user_name = ''
            if 'new_username' in request.form:
                user_name = request.form['new_username'].strip()
            
                if user_name != '':
                    rec.username = user_name
                else:
                    rec.username = None
        
            if rec.password != None and request.form['new_password'].strip() == '':
                # Don't change the password
                pass
            else:
                user_password = ''
                if request.form['new_password'].strip() != '':
                    user_password = getPasswordHash(request.form['new_password'].strip())

                if user_password != '':
                    rec.password = user_password
                else:
                    rec.password = None
    
            try:
                user.save(rec)
                g.db.commit()
                
                if 'user_edit_token' in session:
                    del session['user_edit_token']
                    
                # if the username or email address are the same as g.user
                # update g.user if it changes
                if(editingCurrentUser != ''):
                    setUserStatus(editingCurrentUser,rec.id)                
                
            except Exception as e:
                g.db.rollback()
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))
            
            return redirect(g.listURL)
        
        else:
            # form did not validate, give user the option to keep their old password if there was one
            #need to restore the username
            user.update(rec,request.form)
            if 'new_username' in request.form:
                rec.username = request.form['new_username'] #preserve user input

    # display form
    return render_template('user/user_edit.html', rec=rec)
    
@mod.route('/register/', methods=['GET'])
def register():
    setExits()
    return "Registration not done yet..."

@mod.route('/delete', methods=['GET'])
@mod.route('/delete/', methods=['GET'])
@mod.route('/delete/<id>/', methods=['GET'])
def delete(int:id=0):
    return "Delete not implemented yet"
#    setExits()
#    id = cleanRecordID(id)
#    if id < 0:
#        flash("That is not a valid ID")
#        return redirect(g.listURL)
#    
#    if id > 0:
#        rec = user.get(id)
#        if rec:
#            try:
#                db.delete(rec)
#                db.commit()
#            except Exception as e:
#                flash(printException('Error attempting to delete '+g.title+' record.',"error",e))
#        else:
#            flash("Record could not be deleted.")
#            
#    return redirect(g.listURL)
#    
#
def validForm(rec):
    # Validate the form
    goodForm = True
    user = User(g.db)
    
    if request.form['email'].strip() == '':
        goodForm = False
        flash('Email may not be blank')

    if request.form['email'].strip() != '' and not looksLikeEmailAddress(request.form['email'].strip()):
        goodForm = False
        flash("That doesn't look like a valid email address")

    if request.form['email'].strip() != '':
        found = user.get(request.form['email'].strip(),include_inactive=True)
        if found:
            if request.form['id'] == 'None' or found.id != int(request.form['id']):
                goodForm = False
                flash('That email address is already in use')
            
    # user name must be unique if supplied
    if 'new_username' in request.form:
        if request.form['new_username'].strip() != '':
            found = user.get(request.form['new_username'].strip(),include_inactive=True)
            if found:
                if request.form['id'] == 'None' or found.id != int(request.form['id']):
                    goodForm = False
                    flash('That User Name is already in use')
        
        if request.form["new_username"].strip() != '' and request.form["new_password"].strip() == '' and rec.password == '':
            goodForm = False
            flash('There must be a password if there is a User Name')
        
    if request.form["new_password"].strip() == '' and request.form["confirm_password"].strip() != '' and rec.password != '':
        goodForm = False
        flash("You can't enter a blank password.")
    
    #passwords must match if present
    if request.form['confirm_password'].strip() != request.form['new_password'].strip():
        goodForm = False
        flash('Passwords don\'t match.')
        
    return goodForm
    

