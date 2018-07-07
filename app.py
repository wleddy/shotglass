from models import Database, init_db, User, Role
from flask import Flask, render_template, g, Blueprint
from flask_mail import Mail

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


@app.before_request
def _before():
    # Force all connections to be secure
    if app.config['REQUIRE_SSL'] and not request.is_secure :
        return redirect(request.url.replace("http://", "https://"))
   
    g.db = Database(app.config['DATABASE_PATH']).connect()

@app.teardown_request
def _teardown(exception):
    if g.db:
        g.db.close()

@app.route('/')
def index():
    out = "No users found"
    user = User(g.db)
    rec = user.get_by_username_or_email("admin")
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
            out += "<p>No records found</p>"
            
    return out

#from views.users.user import new_test
#@app.route('/new')
#@app.route('/new/')
#def new():
#    return new_test()

if __name__ == '__main__':
    db = Database(app.config['DATABASE_PATH']).connect()
    init_db(db)
    app.run()
    