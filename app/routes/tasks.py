import json
import docker # استيراد مكتبة دوكر
from flask import Blueprint, request, jsonify
from app.models import Task, UserTask
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity

tasks_bp = Blueprint('tasks', __name__)

# إعداد Docker client
client = docker.from_env()

@tasks_bp.route('/<int:task_id>/submit', methods=['POST'])
@jwt_required()
def submit_task(task_id):
    current_user_id = int(get_jwt_identity())
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({"message": "Code submission is required"}), 400
    
    user_code = data.get('code')

    try:
        test_cases = json.loads(task.test_cases)
        all_passed = True
        
        for case in test_cases:
            inp = case.get("input", "")
            expected_out = case.get("output")
            
            # ******************* بداية الجزء المعدل *******************
            try:
                # 1. بنحاكي الـ stdin عن طريق استبدال دالة input()
                # الكود ده بيضيف سطور في أول كود المستخدم
                input_data = json.dumps(inp.splitlines())
                
                # كود بنضيفه في الأول عشان يعمل override لدالة input()
                mock_stdin_code = f"""
import sys
from io import StringIO
sys.stdin = StringIO('\\n'.join({input_data}))
"""
                # بنلزق الكود بتاعنا في كود المستخدم
                final_code = mock_stdin_code + user_code

                # 2. بننفذ الكود المدمج
                container = client.containers.run(
                    'python:3.11-slim',
                    command=['python', '-c', final_code], # بننفذ الكود كله مرة واحدة
                    detach=True
                )

                # 3. بنستنى النتيجة
                result = container.wait(timeout=5)
                stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
                stderr = container.logs(stdout=False, stderr=True).decode('utf-8')

            finally:
                # 4. بننضف الـ container
                if 'container' in locals() and container:
                    container.stop()
                    container.remove()
            # ******************* نهاية الجزء المعدل *******************

            # 6. مقارنة النتائج
            if result['StatusCode'] != 0 or stderr:
                all_passed = False
                print(f"Test case failed with error: {stderr}")
                break
            
            actual_out = stdout.strip()
            if actual_out != expected_out.strip():
                all_passed = False
                print(f"Test case failed: Expected '{expected_out}', got '{actual_out}'")
                break

        # باقي الكود بتاع تحديث الداتابيز زي ما هو
        user_task = UserTask.query.filter_by(user_id=current_user_id, task_id=task_id).first()
        if not user_task:
            user_task = UserTask(user_id=current_user_id, task_id=task_id)
            db.session.add(user_task)

        # --- الكود الجديد والمصحح ---
        # نتأكد إن عدد المحاولات عمره ما يكون None
        if user_task.attempts is None:
            user_task.attempts = 0

        user_task.attempts += 1
        user_task.submitted_code = user_code
        
        if all_passed:
            user_task.is_completed = True
            db.session.commit()
            return jsonify({"message": "Correct! All test cases passed.", "completed": True}), 200
        else:
            db.session.commit()
            # هنا ممكن تضيف الـlogic بتاع الرسائل التحفيزية والنصائح
            if user_task.attempts == 2:
                return jsonify({"message": "Incorrect. Try reading the lesson again.", "completed": False, "hint": "Keep trying!"}), 200
            elif user_task.attempts >= 3:
                return jsonify({"message": "Incorrect. Here is a small tip...", "completed": False, "hint": "Think about edge cases."}), 200
            else:
                return jsonify({"message": "Incorrect. Try again.", "completed": False}), 200

    except docker.errors.ContainerError as e:
        # ده بيحصل لو الكود خد وقت أطول من الـ timeout
        return jsonify({"message": "Your code took too long to execute.", "completed": False}), 408
    except Exception as e:
        # لأي أخطاء تانية
        return jsonify({"message": "An unexpected error occurred", "error": str(e)}), 500