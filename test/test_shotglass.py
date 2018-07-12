
import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app
from flask import g

filespec = 'instance/test.db'


@pytest.fixture
def client():
    db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.app.test_client()

    with app.app.app_context():
        print(app.app.config['DATABASE'])
        app.init_db(app.get_db(app.app.config['DATABASE'])) 
        print(app.g.db)
        
    yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE'])
    
    
with app.app.app_context():
    db = app.get_db(filespec)
    app.init_db(db)
    #get a file descriptor to the db file so we can delete it later...
    #file_des = os.open(filespec,1)
    #os.close(file_des)

        
def delete_test_db():
        #os.close(file_des)
        os.remove(filespec)


def test_first_user(client):
    """there is always at least one user"""

    rv = client.get('/')
    assert b'Your roles include:' in rv.data
    assert b'No users found' not in rv.data
    
    
def test_user():
    from models import User
    #db = get_test_db()
    
    rec = User(db).get(1)
    assert rec.first_name == 'Admin'
    rec = User(db).get_by_username_or_email('admin')
    assert rec.first_name == 'Admin'
    
    db.execute('insert into user (first_name,last_name,email) values (?,?,?)',('Marcia','Leddy','marcia@user_test.com',))
    db.execute('insert into user (first_name,last_name,email) values (?,?,?)',('Bill','Leddy','bill@user_test.com',))
    db.execute('insert into user (first_name,last_name,email,active) values (?,?,?,?)',('Inactive','Leddy','no_longer@user_test.com',0))
    db.commit()
    
    recs = User(db).select(order_by = 'first_name')
    assert len(recs) == 3
    
    rec = User(db).get_by_username_or_email('marcia@user_test.com')
    assert rec.first_name == 'Marcia'
    
    #test that inactive records are returned...
    recs = User(db).select(include_inactive=True)
    assert len(recs) == 4
    
    recs = User(db).select(order_by='first_name desc')
    assert recs[0].first_name == 'Marcia'
    
    rec = User(db).select_one(where='first_name = "Bill"')
    assert rec.first_name == 'Bill'

    #test no return
    rec = User(db).get_by_username_or_email("nothing to find here")
    assert rec == None
    rec = User(db).select_one(where="first_name = 'nothing to find here'")
    assert rec == None
    recs = User(db).select(where="first_name = 'nothing to find here'")
    assert recs == None
    
    #test get user roles
    user = User(db)
    recs = user.get_roles(1)
    assert recs != None
    assert len(recs) == 1
    assert recs[0].name == 'super'
    
    #get a new record of nulls
    rec = User(db).new()
    assert rec.first_name == None
    
def test_get_roles():
    from models import Role
    #db = get_test_db()
    
    recs = Role(db).select()
    assert recs != None
    assert len(recs)==3
    assert recs[0].name != None
    
    
def test_finished():
    delete_test_db()
    
    assert True
