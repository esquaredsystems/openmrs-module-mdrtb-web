# Must be copied to the app's directory
bind = "127.0.0.1:8000"
workers = 3
chdir = "/opt/python/mdrtb"
module = "mdrtb.wsgi:application"
