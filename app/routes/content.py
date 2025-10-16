from flask import Blueprint, json, request, jsonify
from app.models import Task, Topic, Lesson
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

content_bp = Blueprint('content', __name__)

# --- Endpoints for Mentor (Admin) ---

@content_bp.route('/topics', methods=['POST'])
@jwt_required() # Endpoint ده محمي، لازم تكون عامل login
def create_topic():
    # هنا المفروض نتأكد إن اللي بيبعت الطلب ده هو الـmentor
    # (هنعملها بشكل بسيط دلوقتي وهنحسنها بعدين)
    current_user_id = get_jwt_identity()
    # if not User.query.get(current_user_id).is_mentor:
    #     return jsonify({"message": "Admin access required"}), 403

    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({"message": "Title is required"}), 400

    new_topic = Topic(
        title=data.get('title'),
        description=data.get('description'),
        is_premium=data.get('is_premium', False) # افتراضيًا مش مدفوع
    )

    try:
        db.session.add(new_topic)
        db.session.commit()
        return jsonify({"message": "Topic created successfully", "topic_id": new_topic.id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Topic with this title already exists"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

@content_bp.route('/topics/<int:topic_id>/lessons', methods=['POST'])
@jwt_required()
def create_lesson(topic_id):
    # ... (نفس التحقق من الـmentor) ...
    
    topic = Topic.query.get_or_404(topic_id) # نتأكد إن الموضوع موجود

    data = request.get_json()
    if not data or not data.get('title') or not data.get('article_content') or 'order' not in data:
        return jsonify({"message": "Title, article_content, and order are required"}), 400

    new_lesson = Lesson(
        title=data.get('title'),
        video_url=data.get('video_url'),
        article_content=data.get('article_content'),
        example_code=data.get('example_code'),
        order=data.get('order'),
        topic_id=topic.id # نربطه بالموضوع
    )

    db.session.add(new_lesson)
    db.session.commit()

    return jsonify({"message": "Lesson created successfully", "lesson_id": new_lesson.id}), 201

# --- Endpoints for All Users ---

@content_bp.route('/topics', methods=['GET'])
def get_all_topics():
    topics = Topic.query.order_by(Topic.id).all()
    topics_data = [{
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "is_premium": topic.is_premium
    } for topic in topics]
    return jsonify(topics_data), 200

@content_bp.route('/topics/<int:topic_id>/lessons', methods=['GET'])
def get_lessons_for_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    # هنا ممكن نضيف logic لو الموضوع premium والمستخدم مش دافع
    
    lessons = Lesson.query.filter_by(topic_id=topic.id).order_by(Lesson.order).all()
    lessons_data = [{
        "id": lesson.id,
        "title": lesson.title,
        "order": lesson.order
        # ممكن نضيف باقي البيانات لو محتاجينها في القائمة
    } for lesson in lessons]
    return jsonify(lessons_data), 200

@content_bp.route('/lessons/<int:lesson_id>', methods=['GET'])
def get_lesson_details(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    # هنا برضه ممكن نضيف logic للدروس الـpremium
    
    lesson_data = {
        "id": lesson.id,
        "title": lesson.title,
        "video_url": lesson.video_url,
        "article_content": lesson.article_content,
        "example_code": lesson.example_code,
        "order": lesson.order,
        "topic_id": lesson.topic_id
    }
    return jsonify(lesson_data), 200

# ... (باقي الكود في content.py) ...

@content_bp.route('/lessons/<int:lesson_id>/tasks', methods=['POST'])
@jwt_required()
def create_task_for_lesson(lesson_id):
    # هنا ممكن نضيف تحقق إن المستخدم هو الـmentor
    
    lesson = Lesson.query.get_or_404(lesson_id) # نتأكد إن الدرس موجود

    data = request.get_json()
    required_fields = ['title', 'description', 'test_cases']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Title, description, and test_cases are required"}), 400

    # --- الجزء المهم: التعامل مع test_cases ---
    test_cases_data = data.get('test_cases')
    # نتأكد إن الـtest_cases اللي جاية هي list of dicts
    if not isinstance(test_cases_data, list):
        return jsonify({"message": "test_cases must be a list of objects"}), 400
    
    # بنحول الـlist of dicts دي لـJSON string عشان نخزنها في الداتابيز
    test_cases_string = json.dumps(test_cases_data)

    new_task = Task(
        title=data.get('title'),
        description=data.get('description'),
        test_cases=test_cases_string, # بنخزن الـstring هنا
        solution_code=data.get('solution_code'),
        lesson_id=lesson.id # بنربطه بالدرس
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({"message": "Task created successfully", "task_id": new_task.id}), 201