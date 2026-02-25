from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, ChatStats, Organization, FAQ, Admin  
from nlp_engine import ASANAIAssistant
from datetime import datetime
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asan-chatbot-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asan_chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# AI asistanları cache et
ai_assistants = {}

@login_manager.user_loader
def load_user(user_id):
    # DÜZƏLİŞ: AdminModel yox, Admin olmalıdır (database.py-dakı kimi)
    return Admin.query.get(int(user_id))

def get_ai_assistant(org_id="asan_xidmet"):
    if org_id not in ai_assistants:
        ai_assistants[org_id] = ASANAIAssistant(org_id)
    return ai_assistants[org_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    org_id = data.get('org_id', 'asan_xidmet')
    
    if not user_message:
        return jsonify({'error': 'Mesaj boş ola bilməz'}), 400
    
    assistant = get_ai_assistant(org_id)
    bot_answer = assistant.find_best_answer(user_message)
    
    stat = ChatStats(
        org_id=1, 
        user_question=user_message,
        bot_answer=bot_answer,
        confidence=0.8
    )
    db.session.add(stat)
    db.session.commit()
    
    return jsonify({
        'answer': bot_answer,
        'timestamp': datetime.now().isoformat(),
        'org': org_id
    })

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # DÜZƏLİŞ: AdminModel yox, Admin
        admin = Admin.query.filter_by(username=username).first()
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
    stats = {
        'total_questions': ChatStats.query.count(),
        'total_faqs': FAQ.query.count(),
        'today_questions': ChatStats.query.filter(
            ChatStats.timestamp >= datetime.now().date()
        ).count()
    }
    
    top_questions = db.session.query(
        ChatStats.user_question, 
        db.func.count(ChatStats.user_question).label('count')
    ).group_by(ChatStats.user_question).order_by(db.desc('count')).limit(10).all()
    
    # DÜZƏLİŞ: 'now' dəyişəni template-ə göndərilməlidir
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         top_questions=top_questions,
                         now=datetime.now())

@app.route('/admin/faqs')
@login_required
def manage_faqs():
    faqs = FAQ.query.all()
    return render_template('admin/faqs.html', faqs=faqs)

@app.route('/admin/faq/add', methods=['POST'])
@login_required
def add_faq():
    question = request.form.get('question')
    answer = request.form.get('answer')
    keywords = request.form.get('keywords', '').split(',')
    category = request.form.get('category')
    
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
    
    assistant = get_ai_assistant()
    assistant.add_new_question(question, answer, keywords, category)
    
    return redirect(url_for('manage_faqs'))

@app.route('/admin/faq/delete/<int:faq_id>')
@login_required
def delete_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    return redirect(url_for('manage_faqs'))

@app.route('/admin/stats')
@login_required
def view_stats():
    daily_stats = db.session.query(
        db.func.date(ChatStats.timestamp).label('date'),
        db.func.count(ChatStats.id).label('count')
    ).group_by('date').order_by('date').limit(30).all()
    
    return render_template('admin/stats.html', daily_stats=daily_stats, stats={})

# DÜZƏLİŞ: Main blokundakı boşluq (indentation) və məntiq səhvləri düzəldildi
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Default admin yoxdursa yarat
        admin_user = Admin.query.filter_by(username='admin').first()
        if not admin_user:
            # Əgər Organization cədvəli boşdursa, əvvəlcə bir org yaratmaq lazımdır
            if not Organization.query.get(1):
                default_org = Organization(name="ASAN Xidmət", code="asan_xidmet")
                db.session.add(default_org)
                db.session.commit()
            
            admin = Admin(username='admin', org_id=1)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin yaradıldı: admin / admin123")
            
    app.run(debug=True, host='0.0.0.0', port=5000)
    
