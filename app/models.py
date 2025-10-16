# *****************************************************************************
# هام جدًا: السطر ده لازم يكون أول سطر تنفيذي في الملف (بعد أي comments)
# ده بيستورد الـ`db` instance اللي تم تعريفها وتهيئتها في `app.py`
# بحيث كل الـModels هنا تستخدم نفس الـ`SQLAlchemy` instance.
# *****************************************************************************
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
from app import db 

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash # هنحتاج دول لـhashing الباسورد

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True) # أضفت index للسرعة
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) # أضفت index للسرعة
    password_hash = db.Column(db.String(128), nullable=False)
    is_mentor = db.Column(db.Boolean, default=False)
    registered_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # العلاقات (Relationships)
    progress = db.relationship('Progress', backref='user', lazy='dynamic') # غيرت lazy لـ'dynamic' للعلاقات الكبيرة
    user_tasks = db.relationship('UserTask', backref='user', lazy='dynamic') # إضافة علاقة للـUserTask

    def __repr__(self):
        return f'<User {self.username}>'

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True, index=True) # unique و index
    description = db.Column(db.Text, nullable=True)
    is_premium = db.Column(db.Boolean, default=False) # هل الموضوع ده مدفوع؟
    
    lessons = db.relationship('Lesson', backref='topic', lazy='dynamic')
    
    def __repr__(self):
        return f'<Topic {self.title}>'

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, index=True)
    video_url = db.Column(db.String(255), nullable=True) # رابط فيديو يوتيوب
    article_content = db.Column(db.Text, nullable=False) # محتوى المقال (من README.md)
    example_code = db.Column(db.Text, nullable=True) # مثال كود جاهز
    order = db.Column(db.Integer, nullable=False) # ترتيب الدرس داخل الموضوع

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    
    tasks = db.relationship('Task', backref='lesson', lazy='dynamic')

    def __repr__(self):
        return f'<Lesson {self.title}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False) # وصف التاسك
    test_cases = db.Column(db.Text, nullable=False) # ده اللي هنحط فيه الـtest cases عشان نقيم الكود
    solution_code = db.Column(db.Text, nullable=True) # (اختياري) لو عايز تحط حل مقترح

    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    
    user_tasks = db.relationship('UserTask', backref='task', lazy='dynamic')

    def __repr__(self):
        return f'<Task {self.title}>'

class UserTask(db.Model): 
    # ده جدول عشان نربط بين المستخدم والتاسك اللي عمله وحالة حلها
    # وممكن يكون فيه معلومات زي الكود اللي سلمه، عدد المحاولات، وهكذا.
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    submitted_code = db.Column(db.Text, nullable=True) # الكود اللي المستخدم سلمه
    is_completed = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_attempt_on = db.Column(db.DateTime, default=datetime.utcnow)
    
    # عشان تضمن أن كل مستخدم يقدر يحل كل تاسك مرة واحدة فقط (لو عايز كده)
    __table_args__ = (db.UniqueConstraint('user_id', 'task_id', name='_user_task_uc'),) 
    
    def __repr__(self):
        return f'<UserTask User:{self.user_id} Task:{self.task_id} Completed:{self.is_completed}>'

class Progress(db.Model):
    # لتتبع تقدم المستخدم في الدروس.
    # UserTask بتتبع التاسكات، دي بتتبع الدروس ككل
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False) # هل الدرس ده تم إكماله؟
    completed_on = db.Column(db.DateTime, nullable=True)

    # عشان تضمن أن كل مستخدم يقدر يعمل تقدم في كل درس مرة واحدة فقط
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id', name='_user_lesson_progress_uc'),)

    def __repr__(self):
        return f'<Progress User:{self.user_id} Lesson:{self.lesson_id} Completed:{self.is_completed}>'