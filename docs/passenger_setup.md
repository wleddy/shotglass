# How to manually configure passenger setup

As of today, Nov. 27, 2018, this is what I think you need to do to manually fix/adjust/create the python settings 
for a site hosted on A2 Hosting

To begin with, setup the virtual environment using the  "Python Setup" cpanel. This will usually do everything needed to get you going, 
but the problem I have is that the cpanel does not show all of my environments so I could not make the changes I needed to make.

Below are the places to look for the bits to change the virtual environment and the python app settings that the server
will be looking for. Since I have no real idea what is going on under the hood this what I figured out by trial and error
as so it may not work in all cases

__Create .htaccess file__: if there is not one already, you need to create an file named `.htaccess` in the **document root** 
directory of your site. The file should contain something like this:

```
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION BEGIN
PassengerAppRoot "/home/leddysle/Sites/lindcraft/lindcraft2"
PassengerBaseURI "/"
PassengerPython "/home/leddysle/virtualenv/Sites_lindcraft_lindcraft2/3.6/bin/python3.6"
# DO NOT REMOVE. CLOUDLINUX PASSENGER CONFIGURATION END

```

The "PassengerAppRoot" is the path to your python app. "PassengerPython" is the path to the virtual environment to use with
the app.

You can use the same `.htaccess` file in multiple doc roots if for some reason you want that.

My guess is that when a visitor hits the site, the Passenger... directives cause the web server to pipe the request to the 
python app indicated. That's just a guess...