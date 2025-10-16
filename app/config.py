import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key_if_not_set'
    
    # ************* التعديل هنا *************
    # استخدام DATABASE_URL من .env مباشرة
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # *************************************
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False