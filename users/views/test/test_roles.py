
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
    
    
filespec = 'instance/test_roles.db'
db = None

with app.app.app_context():
    db = app.get_db(filespec)
    app.init_db(db)

        
def delete_test_db():
        os.remove(filespec)

    
def test_roles():
    from users.models import Role
    #db = get_test_db()
    
    assert Role(db).get(0) == None 
    
    recs = Role(db).select()
    assert recs != None
    assert len(recs)==3
    assert recs[0].name != None
    
    rec = Role(db).new()
    rec.name = "Testing"
    rec.description = "A test role"
    
    recID = Role(db).save(rec)
    rec = Role(db).get(recID)
    assert rec.id == recID
    assert rec.name == 'Testing'
    assert rec.rank == 0
    
    #Modify the record
    rec.name = "New Test"
    rec.rank = 300
    Role(db).save(rec)
    rec = Role(db).get(rec.id)
    assert rec.name == "New Test"
    assert rec.rank == 300
    
    db.rollback()
    
    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        db.close()
        delete_test_db()
        assert True
    except:
        assert True
