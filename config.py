"""Flask configuration."""

# Base Flask configurations
TESTING = True
DEBUG = False
FLASK_ENV = 'production'
SECRET_KEY = '5791628bb0b13ce0c676dfde280ba245'

UPLOAD_FOLDER = 'static/upload_folder/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Run configurations for Flask-Mail
MAIL_SERVER = 'smtp.mailtrap.io'
MAIL_PORT = 2525
MAIL_USERNAME = "856aa3cf52e478"
MAIL_PASSWORD = "c838d789c4c3bc"
MAIL_USE_TLS = True
MAIL_USE_SSL = False
