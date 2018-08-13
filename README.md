# Shotglass

This is designed as a starter Flask installation with a minimum of dependancies. In conjunction with the 'users' package from
my github account. Shotglass and users provide a very simple framework to start a Flask project with the ability to add and 
manage users and roles to controll access to your app.

By default, the main program file is app.py. App.py expects there to be a python package called 'users' and out-of-the-box 
won't run without it.

The 'users' package is it's own repository on github. All of the database functionality (sqlite3) is in users so the first thing
you probably want to do is clone users into your new flask app. See "Instructions" below.

## Instructions 

A typical approach would be to:

    * create a new empty github repo for your new project
    
    * clone it into your development machine
    
    * get the .zip of the shotglass repo (don't clone it. You're making a new project)
    
    * copy the contents of the .zip into your new project directory
    
    * cd into the directory and clone the 'users' repo into it
    
    * do an initial commit of your new project, but be sure NOT to include users
    
    * in the terminal run `. setup_env` This will create the instance directory where your private
      stuff is stored and will try to create virtualenv directory 'env' and pip the requirements into it.
      
    * Assuming everything went Ok, run `. activate_env` to enter your virtual environment.
    
    * Next, edit the file at `instance/site_settings.py` with all your secrets.
    
    * run python app.py to start the dev server
    
## Special Instructions for A2 Hosting

A2 Hosting uses this `passenger` system to run python apps on their system. `activate_env` will not find the python 
environment which their system creates for your app.

You don't need to, but if you want you can create a new file at `instance/activate_env` with the following contents:

`
    #!/bin/bash

    echo 'activating env from instance'
    source /home/< your account name >/virtualenv/< path to your project >/3.6/bin/activate
`

You can copy the actual command from the Python Setup App in your cPanel.

Next you need to edit the file `passenger_wsgi.py`. Comment out the default text and add:

    `from app import app as application`
    
from the terminal, run `python app.py`

This will start the development web server but also creates the default database records and is a good way to check that 
everything is working.

Go back to the Python Setup App panel and restart your app or from the terminal in the app root directory type 
`touch tmp/restart.txt`


Required packages:

    * python 3.6 (ish)
    
    * Flask and it's default dependencies, of course
    
    * Flask-mail
    
    * pytest
