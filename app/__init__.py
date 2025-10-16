from flask import Flask, jsonify # تصحيح: شيلنا 'app' من هنا
from dotenv import load_dotenv
import os

# استيراد الـextensions
from .extensions import db, migrate, bcrypt, jwt

load_dotenv()

# هو تعريف واحد فقط للدالة دي
def create_app():
    # بنعمل instance من الـFlask class
    app = Flask(__name__)
    
    # بنحمل الإعدادات
    app.config.from_object('app.config.Config')

    # بنهيء الـextensions مع الـapp
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # بنستورد الـmodels عشان Alembic يشوفها
    from . import models

    # --- تسجيل كل الـBlueprints (الـAPIs) في مكان واحد ---
    
    # 1. الـBlueprint بتاع الـAuthentication
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # 2. الـBlueprint بتاع الـContent
    from .routes.content import content_bp
    app.register_blueprint(content_bp, url_prefix='/content')

    # --- تعريف أي Routes بسيطة هنا لو محتاج ---
    @app.route('/')
    def home():
        return jsonify(message="Welcome to Python Learning Platform Backend API!")
        
    # بنرجع الـapp instance الجاهز في الآخر
    
    # ***** أضف السطور دي *****
    from .routes.tasks import tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    # **************************
    return app