from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    faqs = db.relationship('FAQ', backref='organization', lazy=True)
    stats = db.relationship('ChatStats', backref='organization', lazy=True)

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(500))  # JSON formatında saxlanır
    category = db.Column(db.String(100))
    hit_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_keywords(self):
        return json.loads(self.keywords) if self.keywords else []
    
    def set_keywords(self, keywords_list):
        self.keywords = json.dumps(keywords_list)

class ChatStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    user_question = db.Column(db.String(500))
    bot_answer = db.Column(db.Text)
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(UserMixin, db.Model):
  class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    is_super = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
        class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey('organization.id'))
    is_super = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
