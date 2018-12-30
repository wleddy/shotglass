
import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app
from takeabeltof.get_client import client

#@pytest.fixture
#def client():
#    db_fd, app.app.config['DATABASE_PATH'] = tempfile.mkstemp()
#    app.app.config['TESTING'] = True
#    client = app.app.test_client()
#
#    with app.app.app_context():
#        with app.app.test_request_context():
#            #this context sets up a dummy request with a url of 'http://localhost/'
#            app.initalize_all_tables((app.get_db(app.app.config['DATABASE_PATH'])))
#        
#    yield client
#
#    os.close(db_fd)
#    os.unlink(app.app.config['DATABASE_PATH'])
    
    
filespec = 'instance/test.db'

db = None

#with app.app.app_context():
#    db = app.get_db(filespec)
#    app.init_db(db)

        
def delete_test_db():
        os.remove(filespec)
        
def test_home(client):
    result = client.get('/')   
    assert result.status_code == 200
    assert b'Hello World' in result.data 
    
def test_404(client):
    result = client.get('/nothingtofind')   
    assert result.status_code == 404
    assert b'Sorry' in result.data 
    
############################ The final 'test' ########################
######################################################################
def test_finished():
    try:
        db.close()
        del db
        delete_test_db()
        assert True
    except:
        assert True
