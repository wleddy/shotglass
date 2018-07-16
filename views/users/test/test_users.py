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
        
        
def test_password_hash():
    import views.users.login as login
    # basic tests
    passwords = ("password", 
                 "PassWord",
                 "nota passwoerd",
                 "password ",
                )
    results = ()
    for x in range(len(passwords)):
        results += (login.getPasswordHash(passwords[x]),)
        
    for x in range(len(passwords)):
        print('Basic test {}; pw: {}, hash: {}'.format(x,passwords[x],results[x]))
        assert results[x] != ''
        print(len(results[x]))
        assert len(results[x]) == 84
        if x > 0:
            assert results[x] != results[x-1]
    
    ### test the helper method to test a password
    for x in range(len(passwords)):
        print('Match test {}; pw: {}, hash: {}'.format(x,passwords[x],results[x]))
        assert login.matchPasswordToHash(passwords[x],results[x])
        
    ### test the None inputs and returns
    assert login.getPasswordHash('') == None
    assert login.matchPasswordToHash('',4) == False
    assert login.matchPasswordToHash('password','') == False
    assert login.matchPasswordToHash('password',234234) == False
    assert login.matchPasswordToHash('password',None) == False
    assert login.matchPasswordToHash(None,None) == False
    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        delete_test_db()
        assert True
    except:
        assert True

