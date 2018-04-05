## Base Settings

import os

class Config(object):
    HOST_NAME = "example.com"
    DEBUG = False
    TESTING = False
    SECRET_KEY = "somereallylongstringtouseasakey"
    REQUIRE_SSL = False
    # work around for some web servers setting wrong path
    CGI_ROOT_FIX_APPLY = False
    CGI_ROOT_FIX_PATH = "/"
    
    DATABASE = "database.sqlite"
    DATABASE_PATH_PREFIX = os.path.dirname(__file__) + '/instance/'
    DATABASE_URI = 'sqlite:///' + DATABASE_PATH_PREFIX + DATABASE
    
    # set session expiration in seconds
    PERMANENT_SESSION_LIFETIME = 60*20
    
    # Email Sending...
    ## Flask_Mail defaults
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = None
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHMENTS = False
    
    # Uploads ...
    MAX_CONTENT_LENGTH = 300000
    
    MAPBOX_PROJECT_ID = ""
    MAPBOX_ACCESS_TOKEN = ""

    LOCATION_DEFAULT_LNG = -121.74439430236818
    LOCATION_DEFAULT_LAT = 38.54422161206573
    
    # Flask-Security settings
    SECURITY_PASSWORD_SALT = '989839ewjieu'
    SECURITY_RECOVERABLE = True
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_EMAIL_SENDER = 'me@example.com'
    
class ProductionConfig(Config):
    pass
    
class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    

