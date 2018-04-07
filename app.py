#from os import open
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack, json
from flask_security import Security, login_required, \
     SQLAlchemySessionUserDatastore, current_user
from flask_security.utils import logout_user, hash_password, url_for_security
from flask_mail import Mail
from flask_admin import Admin
from flask_admin import helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
import logging
import configuration
import sys

# Create app
app = Flask(__name__, instance_relative_config=True)
app.config.from_object(configuration.Config)
app.config.from_pyfile('site_settings.py', silent=True)

app.debug = app.config["DEBUG"]


# work around some web servers that mess up root path
from werkzeug.contrib.fixers import CGIRootFix
if app.config['CGI_ROOT_FIX_APPLY'] == True:
    fixPath = app.config.get("CGI_ROOT_FIX_PATH","/")
    app.wsgi_app = CGIRootFix(app.wsgi_app, app_root=fixPath)

# setup Flask-SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = app.config["DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create a mailer obj
mail = Mail(app)


### views modules need db from above
##import models #### don't import models here, do it in views
#import views.index
#from views.utils import db_init, printException

from database import db_session, init_db
from models import User, Role

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db_session,User, Role)
security = Security(app, user_datastore)


#class AdminBase(ModelView):
#    # protect all admin views
#    roles_accepted = ['superuser','admin']
#
#    def is_accessible(self):
#        roles_accepted = getattr(self, 'roles_accepted', None)
#        if not current_user.is_active or not current_user.is_authenticated:
#            return False
#    
#        return self.has_role()
#        #for role in roles_accepted:
#        #    if current_user.has_role(role):
#        #        return True
#        
#        return False
#
#    def _handle_view(self, name, *args, **kwargs):
#        roles_accepted = getattr(self, 'roles_accepted', None)
#        if not current_user.is_authenticated or not self.has_role():
#            return redirect(url_for_security('login', next="/admin"))
#        if not self.is_accessible():
#            return self.render("admin/denied.html")
#            
#    def has_role(self):
#        roles_accepted = getattr(self, 'roles_accepted', None)
#        for role in roles_accepted:
#            if current_user.has_role(role):
#                return True
#        return False
#        
#class UserModelView(AdminBase):
#    # for list view
#    can_create = False
#    #can_edit = False
#    #can_delete = False  # disable model deletion
#    page_size = 50  # the number of entries to display on the list view
#    column_exclude_list = ['password', 'current_login_at', 'last_login_ip', 
#            'current_login_ip', 'confirmed_at',
#            ]
#    column_searchable_list = ['last_name', 'first_name', 'username', 'email', ]
#    # for the edit and create forms:
#    form_excluded_columns = column_exclude_list
#    form_excluded_columns.append('last_login_at')
#    form_excluded_columns.append('login_count')
    
#admin = Admin(app, name= app.config['SITE_NAME'], template_mode='bootstrap3')
#admin.add_view(UserModelView(User, db_session))
#admin.add_view(AdminBase(Role, db_session))

## the basic views

@app.route('/')
#@login_required
def home():
    return render_template('index.html')
    
#@app.route("/login")
#@app.route("/login/")
#def login():
#    print("login")
#    #logout_user()
#    return redirect(url_for_security('login', next="/admin"))
    
    
#@app.route("/logout")
#def logout():
#    logout_user()
#    return redirect('/')

# Create customized model view class
class MyModelView(ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser') or current_user.has_role('admin'):
            return True

        return False


    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                flash("You don't have access to the admin area")
                #abort(403)
                return redirect(url_for('index', next=request.url))
            else:
                # login
                return redirect(url_for('security.login', next=request.url))
                


class UserModelView(MyModelView):
    # for list view
    can_create = False
    #can_edit = False
    #can_delete = False  # disable model deletion
    page_size = 50  # the number of entries to display on the list view
    column_exclude_list = ['password', 'current_login_at', 'last_login_ip', 
            'current_login_ip', 'confirmed_at',
            ]
    column_searchable_list = ['last_name', 'first_name', 'email', ]
    # for the edit and create forms:
    form_excluded_columns = column_exclude_list
    form_excluded_columns.append('last_login_at')
    form_excluded_columns.append('login_count')
    if current_user and not current_user.has_role('superuser'):
        form_excluded_columns.append('roles')

class SuperUserView(MyModelView):
    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
            
        if current_user.has_role('superuser'): 
            return True

        return False

admin = Admin(
    app,
    app.config['SITE_NAME'],
    base_template='admin_master.html',
    template_mode='bootstrap3',
)
# Add model views
admin.add_view(SuperUserView(Role, db.session))
admin.add_view(UserModelView(User, db.session))

# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


@app.before_request
def before_request():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not app.config['DEBUG'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))


        
if __name__ == '__main__':
    """ Test to see if database file exists.
        if not, create it with init_db()
    """
    db_location = app.config["DATABASE_PATH_PREFIX"] + app.config["DATABASE"]
    try:
        f=open(db_location,'r')
        f.close()
    except IOError as e:
        with app.app_context():
            try:
                print("initializing Database at " + db_location)
                init_db()
            except Exception as e:
                print("Database file was not created. Use Migrations to create it.")
                print("Expected at " + db_location)
                print(str(e))
                sys.exit(0)
            
            
    app.run()
            