from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import time
import re
from models import User, Role
from views.utils import printException, cleanRecordID, looksLikeEmailAddress
from views.users.login import matchPasswordToHash, setUserStatus, getPasswordHash

mod = Blueprint('user',__name__, template_folder='templates')


def setExits():
    g.listURL = url_for('.home')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'User'

@mod.route('/user/')
def home():
    setExits()
    return render_template('user/user_index.html')


## Edit the user
@mod.route('/user/edit', methods=['POST', 'GET'])
@mod.route('/user/edit/', methods=['POST', 'GET'])
@mod.route('/user/edit/<id>/', methods=['POST', 'GET'])
def edit(id=0):
    setExits()

    user = User(g.db)
    rec = None
    current_password = ""
    user_handle = None
    
    if id == 0 and g.user != None:
        user_handle = g.user
    elif id == 0:
        #create a new record
        pass
    else:
        id = cleanRecordID(id)
        if id < 0:
            flash("That is not a valid ID")
            return redirect(g.listURL)
        user_handle = id
        
    if not request.form:
        """ if no form object, send the form page """
        rec = user.get(user_handle)
        if not rec:
            flash("Unable to locate user record")
            return redirect(url_for('home'))
            
        current_password = rec.password
            
        
    else:
        #have the request form
        #import pdb;pdb.set_trace()
        if user_handle:
            rec = user.get(user_handle)
        else:
            ## create a new record stub
            rec = user.new()

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
    
@mod.route('/user/register/', methods=['GET'])
def register():
    setExits()
    return "Registration not done yet..."

@mod.route('/user/delete', methods=['GET'])
@mod.route('/user/delete/', methods=['GET'])
@mod.route('/user/delete/<id>/', methods=['GET'])
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
        flash('That doesn\'t look like a valid email address')

    if request.form['email'].strip() != '':
        #usr = select(where="lower(email) = '{}' and id <> {}".format(request.form['email'].lower().strip(),request.form['id']) func.lower(User.email) == request.form['email'].strip().lower(), User.ID != request.form['ID']).count()
        found = user.get(request.form['email'].strip(),include_inactive=True)
        if found and found.id != int(request.form['id']):
            goodForm = False
            flash('That email address is already in use')
            
    # user name must be unique if supplied
    if 'new_username' in request.form:
        if request.form['new_username'].strip() != '':
            found = user.get(request.form['new_username'].strip(),include_inactive=True)
            if found and found.id != int(request.form['id']):
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
    

