# Must be copied to the app's directory
bind = "127.0.0.1:8000"
workers = 8
chdir = "/opt/python/mdrtb"
module = "mdrtb.wsgi:application"
timeout = 60
max_requests = 1000
max_requests_jitter = 100
