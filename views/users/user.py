from flask import request, session, g, redirect, url_for, abort, \
     render_template, flash, Blueprint
from time import time
import re
from models import User, Role
from views.utils import printException, cleanRecordID, looksLikeEmailAddress
from views.users.login import matchPasswordToHash, setUserStatus

mod = Blueprint('user',__name__)

def test():
    out = "No users found"
    user = User(g.db)
    rec = user.get_by_username_or_email("admin")
    print(session)
    if rec:
        out = "<h1>Hello {} {}</h1>".format(rec.first_name,rec.last_name)
        roles = user.get_roles(rec.id,order_by='name')
        if roles:
            out += "<p>Your roles include:</p>"
            out += '<table><tr>'
            cols = Role(g.db).get_column_names()
            del cols[0]
            for col in cols:
                out += '<th style="border:1pt black solid;">{}</th>'.format(col.title())
            for role in roles:
                out += "<tr>"
                for col in range(1,len(cols)+1):
                    out += '<td style="border:1pt #666 solid;">{}</td>'.format(role[col])
                out += "</tr>"
            out += "</table>"
        else:
            out += "<p>You have no roles assigned.</p>"
            
        recs = Role(g.db).select(order_by='description')
        if recs:
            for rec in recs:
                out +='<p>{} {}</p>'.format(rec.name,rec.description)
        else:
            out += "<p>No Role records found</p>"
            
        recs = User(g.db).select()
        if recs:
            out += '<h3>Users</h3>'
            for rec in recs:
                out += '<p>{} {}</p>'.format(rec.first_name,rec.last_name)
        else:
            out += "No Users Found"
    return out
    

def setExits():
    g.listURL = url_for('.home')
    g.editURL = url_for('.edit')
    g.deleteURL = url_for('.delete')
    g.title = 'User'

@mod.route('/user/')
def home():
    setExits()
    return render_template('user/index.html')


## Edit the user
@mod.route('/user/edit', methods=['POST', 'GET'])
@mod.route('/user/edit/', methods=['POST', 'GET'])
@mod.route('/user/edit/<id>/', methods=['POST', 'GET'])
def edit(id=0):
    #printException(str(request.form)) 
    
    setExits()
    id = cleanRecordID(id)
    
    if id < 0:
        flash("That is not a valid ID")
        return redirect(g.listURL)
            
    rec = None
    
    if not request.form:
        """ if no form object, send the form page """
        # get the user record if you can
        currentPassword = ""
        if id > 0:
            rec = User.query.get(id)
            currentPassword = rec.password
                
        
    else:
        #have the request form
        #ensure a value for the check box
        inactive = request.form.get('inactive')
        if not inactive: 
            inactive = "0"
        

        if validForm():
            if id > 0:
                rec = User.query.get(id)
            else:
                ## create a new record stub
                rec = User(request.form['name'],request.form['email'])
                db.add(rec)
                #db.commit() # this loads the new ID into rec
                
                rec.username = db.null()
                rec.password = db.null()
        
            #Are we editing the current user's record?
            editingCurrentUser = ''
            if(g.user == rec.username):
                editingCurrentUser = request.form['username'].strip()
            else: 
                if(g.user == rec.email):
                    editingCurrentUser = request.form['email'].strip()
            
            #update the record
            rec.name = request.form['name'].strip()
            rec.email = request.form['email'].strip()
            rec.role = request.form['role'].strip()
            rec.inactive = str(inactive)
            
            user_name = ''
            if request.form['username']:
                user_name = request.form['username'].strip()
            
            if user_name != '':
                rec.username = user_name
            else:
                rec.username = db.null()
        
            # Null values in db are returned as None
            if str(rec.password) != 'NULL' and request.form['password'].strip() == '':
                # Don't change the password
                pass
            else:
                user_password = ''
                if request.form['password'].strip() != '':
                    user_password = getPasswordHash(request.form['password'].strip())

                if user_password != '':
                    rec.password = user_password
                else:
                    rec.password = db.null()
    
            try:
                db.commit()
                
                # if the username or email address are the same as g.user
                # update g.user if it changes
                if(editingCurrentUser != ''):
                    setUserStatus(editingCurrentUser,rec.id)                
                
            except Exception as e:
                db.rollback()
                flash(printException('Error attempting to save '+g.title+' record.',"error",e))
            
            return redirect(g.listURL)
        
        else:
            # form did not validate, give user the option to keep their old password if there was one
            currentPassword = ""
            if request.form["password"].strip() != "" and id > 0:
                rec = User(g.db).get(id)
                currentPassword = rec.password
            rec=request.form

    # display form
    return render_template('user/user_edit.html', rec=rec, currentPassword=currentPassword)
    
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
#        rec = User.query.get(id)
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
def validForm():
    # Validate the form
    goodForm = True
    
    if request.form['name'].strip() == '':
        goodForm = False
        flash('Name may not be blank')

    if request.form['email'].strip() == '':
        goodForm = False
        flash('Email may not be blank')

    if request.form['email'] != '':
        cur = User.query.filter(func.lower(User.email) == request.form['email'].strip().lower(), User.ID != request.form['ID']).count()
        if cur == 0:
            # be sure that no other user has this email as their username. Very unlikely...
            cur = User.query.filter(func.lower(User.username) == request.form['email'].strip().lower(), User.ID != request.form['ID']).count()

        if cur > 0 :
            goodForm = False
            flash('That email address is already in use')
        #test the format of the email address (has @ and . after @)
        elif not looksLikeEmailAddress(request.form['email']):
            goodForm = False
            flash('That doesn\'t look like a valid email address')
            
    # user name must be unique
    uName = request.form['username'].strip()
    if uName == "None":
        uName = ""
    else :
        cur = User.query.filter(func.lower(User.username) == request.form['username'].strip().lower(), User.ID != request.form['ID']).count()
        if cur == 0:
            # be sure no one else has this email address as their username... Unlikely, I know.
            cur = User.query.filter(func.lower(User.email) == request.form['username'].strip().lower(), User.ID != request.form['ID']).count()
            
        if cur > 0 :
            goodForm = False
            flash('That User Name is already in use')
        
    passwordIsSet = ((User.query.filter(User.password != db.null(), User.ID == request.form['ID']).count()) > 0)
    
    if request.form["username"].strip() != '' and request.form["password"].strip() == '' and not passwordIsSet:
        goodForm = False
        flash('There must be a password if there is a User Name')
        
    if len(request.form["password"].strip()) == 0 and len(request.form["password"]) != 0 and passwordIsSet:
        goodForm = False
        flash('You can\'t enter a blank password.')
    
    #passwords must match if present
    if request.form['password'].strip() != '' and request.form['confirmPassword'].strip() != request.form['password'].strip():
        goodForm = False
        flash('Passwords don\'t match.')
        
    return goodForm
    

