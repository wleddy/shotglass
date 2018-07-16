
import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app


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
    
    
filespec = 'instance/test.db'

with app.app.app_context():
    db = app.get_db(filespec)
    app.init_db(db)

        
def delete_test_db():
        os.remove(filespec)

    
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
    
    #get by username or password
    rec = User(db).get('marcia@user_test.com')
    assert rec.first_name == 'Marcia'
    
    # treat email address as case insensitive
    rec = User(db).get('Marcia@User_Test.com')
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
    
    # put some values in the new record and save it to the db
    rec = User(db).new()
    rec.first_name = " Some " #tests for strip strings
    rec.last_name = "Guy"
    rec.email = "sYg@Test.com"
    rec.password = "password"
    
    new_id = User(db).save(rec)
    
    assert rec.id != None
    assert rec.first_name == 'Some'
    assert rec.email == 'sYg@Test.com'
    assert rec.active == 1
    assert rec.password == "password"

    #db.commit()
    
    # Don't strip strings
    rec.first_name = " Some "
    User(db).save(rec,strip_strings=False)
    assert rec.first_name == " Some "
    
    #update the record
    rec = User(db).get(rec.id)
    rec.last_name = 'Yung Guy'
    User(db).save(rec)
    
    assert rec.last_name == 'Yung Guy'
    
    #Test Rollback
    db.rollback()
    rec = User(db).get(new_id)
    assert rec == None

    
def test_roles():
    from models import Role
    #db = get_test_db()
    
    recs = Role(db).select()
    assert recs != None
    assert len(recs)==3
    assert recs[0].name != None
    
    rec = Role(db).new()
    rec.name = "Testing"
    rec.description = "A test role"
    
    recID = Role(db).save(rec)
    assert rec.id == recID
    assert rec.name == 'Testing'
    assert rec.rank == 0
    
    #Modify the record
    rec.name = "New Test"
    rec.rank = 300
    Role(db).save(rec)
    assert rec.name == "New Test"
    assert rec.rank == 300
    
    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        delete_test_db()
        assert True
    except:
        assert True
