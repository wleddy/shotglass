import sys
#print(sys.path)
sys.path.append('') ##get import to look in the working dir.

import os
import pytest
import tempfile

import app
from models import User, Role

@pytest.fixture
def client():
    db_fd, app.app.config['DATABASE'] = tempfile.mkstemp()
    app.app.config['TESTING'] = True
    client = app.app.test_client()

    with app.app.app_context():
        app.init_db(app.get_db())

    yield client

    os.close(db_fd)
    os.unlink(app.app.config['DATABASE'])

with app.app.app_context():
    db = app.get_db()

#def test_first_user(client):
#    """there is always at least one user"""
#
#    rv = client.get('/')
#    assert b'Your roles include:' in rv.data
#    assert b'No users found' not in rv.data

import views.utils as utils

def test_cleanRecordID():
    """Tesst the cleanRecordID utility fuction"""
    
    assert utils.cleanRecordID(1234) == 1234
    assert utils.cleanRecordID("1234") == 1234
    assert utils.cleanRecordID("this is a test4455") == -1
    assert utils.cleanRecordID("1234this is a test") == -1
    assert utils.cleanRecordID(-4) == -4
    assert utils.cleanRecordID('-4') == -1
    assert utils.cleanRecordID(None) == -1
    

def test_looksLikeEmailAddress():
    """Does this string look like an email address?"""
    assert utils.looksLikeEmailAddress("bill@example.com")
    assert utils.looksLikeEmailAddress("bill.leddy@example.com")
    assert utils.looksLikeEmailAddress() != True
    assert utils.looksLikeEmailAddress(2343345) != True
    assert utils.looksLikeEmailAddress("@Exmaple.com") != True
    assert utils.looksLikeEmailAddress("bill@example") != True
    