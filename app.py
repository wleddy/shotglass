#from os import open
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, _app_ctx_stack, json
from flask_security import Security, login_required, \
     SQLAlchemySessionUserDatastore, current_user
from flask_security.utils import logout_user, hash_password
from flask_mail import Mail
from flask_admin import Admin
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


class UserModelView(ModelView):
    # for list view
    can_create = False
    #can_edit = False
    #can_delete = False  # disable model deletion
    page_size = 50  # the number of entries to display on the list view
    column_exclude_list = ['password', 'current_login_at', 'last_login_ip', 
            'current_login_ip', 'confirmed_at',
            ]
    column_searchable_list = ['last_name', 'first_name', 'username', 'email', ]
    # for the edit and create forms:
    form_excluded_columns = column_exclude_list
    form_excluded_columns.append('last_login_at')
    form_excluded_columns.append('login_count')
    
    
admin = Admin(app, name= app.config['SITE_NAME'], template_mode='bootstrap3')
admin.add_view(UserModelView(User, db_session))
admin.add_view(ModelView(Role, db_session))

@app.before_request
def before_request():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not app.config['DEBUG'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))

## the basic views

@app.route('/')
#@login_required
def home():
    return render_template('index.html')
    
@app.route("/logout")
def logout():
    logout_user()
    return redirect('/')

        
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
            