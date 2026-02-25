from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, ChatStats, Organization, FAQ, Admin
from nlp_engine import ASANAIAssistant
from models import Admin as AdminModel
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asan-chatbot-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asan_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# AI asistanları cache et
ai_assistants = {}

@login_manager.user_loader
def load_user(user_id):
    return AdminModel.query.get(int(user_id))

def get_ai_assistant(org_id="asan_xidmet"):
    """AI asistanı yarat və ya cache-dən götür"""
    if org_id not in ai_assistants:
        ai_assistants[org_id] = ASANAIAssistant(org_id)
    return ai_assistants[org_id]

@app.route('/')
def index():
    """Əsas chat interfeysi"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat API endpoint"""
    data = request.json
    user_message = data.get('message', '')
    org_id = data.get('org_id', 'asan_xidmet')
    
    if not user_message:
        return jsonify({'error': 'Mesaj boş ola bilməz'}), 400
    
    # AI asistanından cavab al
    assistant = get_ai_assistant(org_id)
    bot_answer = assistant.find_best_answer(user_message)
    
    # Statistikanı yadda saxla
    stat = ChatStats(
        org_id=1,  # Default org
        user_question=user_message,
        bot_answer=bot_answer,
        confidence=0.8  # Real confidence hesablanmalıdır
    )
    db.session.add(stat)
    db.session.commit()
    
    return jsonify({
        'answer': bot_answer,
        'timestamp': datetime.now().isoformat(),
        'org': org_id
    })

@app.route('/api/feedback', methods=['POST'])
def feedback():
    """İstifadəçi feedback-i"""
    data = request.json
    message_id = data.get('message_id')
    rating = data.get('rating')  # 1-5 arası
    comment = data.get('comment', '')
    
    # Feedback-i bazada saxla
    # TODO: Feedback modeli yarat
    
    return jsonify({'status': 'success'})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin panel login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = AdminModel.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
            
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin panel əsas səhifə"""
    stats = {
        'total_questions': ChatStats.query.count(),
        'total_faqs': FAQ.query.count(),
        'today_questions': ChatStats.query.filter(
            ChatStats.timestamp >= datetime.now().date()
        ).count()
    }
    
    # Ən çox soruşulan suallar
    top_questions = db.session.query(
        ChatStats.user_question, 
        db.func.count(ChatStats.user_question).label('count')
    ).group_by(ChatStats.user_question).order_by(db.desc('count')).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         top_questions=top_questions)

@app.route('/admin/faqs')
@login_required
def manage_faqs():
    """FAQ-ları idarə et"""
    faqs = FAQ.query.all()
    return render_template('admin/faqs.html', faqs=faqs)

@app.route('/admin/faq/add', methods=['POST'])
@login_required
def add_faq():
    """Yeni FAQ əlavə et"""
    question = request.form.get('question')
    answer = request.form.get('answer')
    keywords = request.form.get('keywords', '').split(',')
    category = request.form.get('category')
    
    # Keywords-i təmizlə
    keywords = [k.strip() for k in keywords if k.strip()]
    
    new_faq = FAQ(
        org_id=1,
        question=question,
        answer=answer,
        category=category
    )
    new_faq.set_keywords(keywords)
    
    db.session.add(new_faq)
    db.session.commit()
    
    # AI asistanını yenilə
    assistant = get_ai_assistant()
    assistant.add_new_question(question, answer, keywords, category)
    
    return redirect(url_for('manage_faqs'))

@app.route('/admin/faq/delete/<int:faq_id>')
@login_required
def delete_faq(faq_id):
    """FAQ sil"""
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    return redirect(url_for('manage_faqs'))

@app.route('/admin/stats')
@login_required
def view_stats():
    """Ətraflı statistika"""
    # Günlük statistika
    daily_stats = db.session.query(
        db.func.date(ChatStats.timestamp).label('date'),
        db.func.count(ChatStats.id).label('count')
    ).group_by('date').order_by('date').limit(30).all()
    
    return render_template('admin/stats.html', daily_stats=daily_stats)

def init_db():
    """İlk dəfə işə salarkən database yarat"""
    with app.app_context():
        db.create_all()
        
        # Default admin yarat
        if not AdminModel.query.filter_by(username='admin').first():
            admin = AdminModel(username='admin', email='admin@asan.az')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
     with app.app_context():
       init_db()
       app.run(debug=True, host='0.0.0.0', port=5000)
