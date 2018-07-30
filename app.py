from models import Database, init_db
from flask import Flask, render_template, g, session, url_for
from flask_mail import Mail

from models import User,Role
from admin import Admin

# Create app
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('site_settings.py', silent=True)


# work around some web servers that mess up root path
from werkzeug.contrib.fixers import CGIRootFix
if app.config['CGI_ROOT_FIX_APPLY'] == True:
    fixPath = app.config.get("CGI_ROOT_FIX_PATH","/")
    app.wsgi_app = CGIRootFix(app.wsgi_app, app_root=fixPath)


# Create a mailer obj
mail = Mail(app)


def get_db(filespec=app.config['DATABASE_PATH']):
    if 'db' not in g:
        g.db = Database(filespec).connect()
    return g.db


@app.before_request
def _before():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))
        
    get_db()
    
    # Is the user signed in?
    g.user = None
    if 'user' in session:
        g.user = session['user']
        
    if 'admin' not in g:
        g.admin = Admin(g.db)
        g.admin.register(User,url_for('user.home'),display_name='Users')
        g.admin.register(Role,url_for('user.home'),display_name='User Permissions')



@app.teardown_request
def _teardown(exception):
    if 'db' in g:
        g.db.close()


from views.users import user
@app.route('/')
def home():
    return render_template('index.html')
    return user.test()

from views.users import user, login
app.register_blueprint(user.mod)
app.register_blueprint(login.mod)

if __name__ == '__main__':
    with app.app_context():
        init_db(get_db())
        get_db().close()
        
    app.run()
    