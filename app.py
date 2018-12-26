from flask import Flask, render_template, g, session, url_for, request, redirect, safe_join, flash
from flask_mail import Mail

from takeabeltof.database import Database
from takeabeltof.utils import send_static_file
from takeabeltof.jinja_filters import register_jinja_filters
from users.models import User,Role,Pref
from users.admin import Admin
import os

# Create app
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('site_settings.py', silent=True)


# work around some web servers that mess up root path
from werkzeug.contrib.fixers import CGIRootFix
if app.config['CGI_ROOT_FIX_APPLY'] == True:
    fixPath = app.config.get("CGI_ROOT_FIX_PATH","/")
    app.wsgi_app = CGIRootFix(app.wsgi_app, app_root=fixPath)

register_jinja_filters(app)


# Create a mailer obj
mail = Mail(app)

def initalize_all_tables(db=None):
    """Place code here as needed to initialze all the tables for this site"""
    if not db:
        db = get_db()
        
    from users.models import init_db as users_init_db 
    users_init_db(db)
    
    
def get_db(filespec=None):
    """Return a connection to the database.
    If the db path does not exist, create it and initialize the db"""
    
    if not filespec:
        filespec = app.config['DATABASE_PATH']
        
    initialize = False
    if 'db' not in g:
        # test the path, if not found, create it
        root_path = os.path.dirname(os.path.abspath(__name__))
        if not os.path.isfile(safe_join(root_path,filespec)):
            initialize = True
            # split it into directories and create them if needed
            path_list = filespec.split("/")
            current_path = root_path
            for d in range(len(path_list)-1):
                current_path = safe_join(current_path,path_list[d])
                if not os.path.isdir(current_path):
                    os.mkdir(current_path, mode=0o744)
                    
        
    g.db = Database(filespec).connect()
    if initialize:
        initalize_all_tables(g.db)
            
    return g.db


@app.before_request
def _before():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))
    
    # update settings for the requested host
    if "SUB_DOMAIN_SETTINGS" in app.config and len(app.config["SUB_DOMAIN_SETTINGS"]) > 0:
        try:
            request_server = request.url
            request_server = request_server[request_server.find('://')+3:]
            #strip the port if present
            pos = request_server.find(":")
            if pos > 0:
                request_server = request_server[:pos]
        
            request_server = request_server.split(".")[0] # the first part of the host name
            server = None
            for value in app.config['SUB_DOMAIN_SETTINGS']:
                if value['config_name'] == request_server:
                    server = value
                    break
        
            #did not find a server to match, use default
            if not server:
                raise ValueError
        except:
            if app.config['DEBUG']:
                #raise ValueError("SUB_DOMAIN_SETTINGS could not be determined")
                flash("Using Default SUB_DOMAIN_SETTINGS")
            server = app.config['SUB_DOMAIN_SETTINGS'][0]
        
        for key, value in server.items():
            app.config.update({key.upper():value})
                    
    get_db()
    
    # Is the user signed in?
    g.user = None
    if 'user' in session:
        g.user = session['user']
        
    if 'admin' not in g:
        g.admin = Admin(g.db)
        # Add items to the Admin menu
        # the order here determines the order of display in the menu
        
        # a header row must have the some permissions or higher than the items it heads
        g.admin.register(User,url_for('user.display'),display_name='User Admin',header_row=True,minimum_rank_required=500)
            
        g.admin.register(User,url_for('user.display'),display_name='Users',minimum_rank_required=500,roles=['admin',])
        g.admin.register(Role,url_for('role.display'),display_name='Roles',minimum_rank_required=1000)
        g.admin.register(Pref,url_for('pref.display'),display_name='Prefs',minimum_rank_required=1000)
        


@app.teardown_request
def _teardown(exception):
    if 'db' in g:
        g.db.close()


@app.errorhandler(404)
def page_not_found(error):
    from takeabeltof.utils import handle_request_error
    handle_request_error(error,request,404)
    g.title = "Page Not Found"
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    from takeabeltof.utils import handle_request_error
    handle_request_error(error,request,500)
    g.title = "Server Error"
    return render_template('500.html'), 500

@app.route('/static_instance/<path:filename>')
def static_instance(filename):
    local_path = None
    if "LOCAL_STATIC_FOLDER" in app.config:
        local_path = app.config['LOCAL_STATIC_FOLDER']

    return send_static_file(filename,local_path=local_path)

from www.views import home
app.register_blueprint(home.mod)

from users.views import user, login, role, pref
app.register_blueprint(user.mod)
app.register_blueprint(login.mod)
app.register_blueprint(role.mod)
app.register_blueprint(pref.mod)

if __name__ == '__main__':
        
    #app.run(host='172.20.10.2', port=5000)
    app.run()
    