import numpy as np
import json
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import nltk
from nltk.corpus import stopwords
import re

# NLTK stopwords yüklə
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class ASANAIAssistant:
    def _init_(self, organization_id="asan_xidmet"):
        self.organization_id = organization_id
        self.questions = []
        self.answers = []
        self.keywords = []
        self.categories = []
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.question_vectors = None
        
        # Daha qabaqcıl model (opsiyonel)
        try:
            self.semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            self.use_semantic = True
        except:
            self.use_semantic = False
            
        self.load_data()
        
    def load_data(self):
        """Məlumat bazasını yüklə"""
        try:
            with open('data/faq_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Təşkilata görə filtrlə
            org_data = data.get(self.organization_id, [])
            
            for item in org_data:
                self.questions.append(item['question'])
                self.answers.append(item['answer'])
                self.keywords.append(item.get('keywords', []))
                self.categories.append(item.get('category', 'general'))
                
            self.prepare_vectors()
            
        except FileNotFoundError:
            # Default data
            self.load_default_data()
            
    def load_default_data(self):
        """Default ASAN məlumatları"""
        asan_data = [
            {
                "question": "Doğum haqqında şəhadətnaməni necə ala bilərəm?",
                "answer": "Doğum haqqında şəhadətnamə almaq üçün:\n1. Valideynlərin şəxsiyyət vəsiqəsi\n2. Doğum haqqında tibbi arayış\n3. Ərizə (ASAN-da doldurulur)\nDövlət rüsumu: 3 AZN",
                "keywords": ["doğum", "körpə", "uşaq", "şəhadətnamə"],
                "category": "sənəd"
            },
            {
                "question": "Şəxsiyyət vəsiqəsimi necə dəyişdirə bilərəm?",
                "answer": "Şəxsiyyət vəsiqəsinin dəyişdirilməsi üçün:\n- Köhnə vəsiqə\n- 2 ədəd foto (3x4)\n- Rüsum: 8 AZN\nMüddət: 5 iş günü",
                "keywords": ["şəxsiyyət", "vəsiqə", "kimlik", "dəyişmək"],
                "category": "sənəd"
            },
            {
                "question": "ASAN xidmətin iş saatları necədir?",
                "answer": "İş saatları: Bazar ertəsi - Şənbə: 08:00 - 20:00\nBazar: Qapalı",
                "keywords": ["iş saatı", "nə vaxt", "açıq", "qrafik"],
                "category": "ümumi"
            }
        ]
        
        self.questions = [item['question'] for item in asan_data]
        self.answers = [item['answer'] for item in asan_data]
        self.keywords = [item['keywords'] for item in asan_data]
        self.categories = [item['category'] for item in asan_data]
        self.prepare_vectors()
        
    def prepare_vectors(self):
        """Sual vektorlarını hazırla"""
        if len(self.questions) > 0:
            # TF-IDF vektorları
            self.question_vectors = self.vectorizer.fit_transform(self.questions)
            
            # Semantik vektorlar (əgər model varsa)
            if self.use_semantic and len(self.questions) <= 1000:
                self.semantic_vectors = self.semantic_model.encode(self.questions)
        
    def preprocess_text(self, text):
        """Mətnləri təmizlə"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        return ' '.join(text.split())
    
    def find_best_answer(self, user_question, threshold=0.3):
        """Ən uyğun cavabı tap"""
        if len(self.questions) == 0:
            return "Məlumat bazası boşdur."
            
        user_question_processed = self.preprocess_text(user_question)
        
        # 1. Açar sözlərə görə axtarış
        keyword_matches = []
        user_words = set(user_question_processed.split())
        
        for idx, keywords in enumerate(self.keywords):
            if any(keyword in user_words for keyword in keywords):
                keyword_matches.append((idx, 1.0))
        
        # 2. TF-IDF cosine similarity
        user_vector = self.vectorizer.transform([user_question_processed])
        similarities = cosine_similarity(user_vector, self.question_vectors).flatten()
        
        # 3. Semantik similarity (əgər varsa)
        if self.use_semantic:
            user_semantic = self.semantic_model.encode([user_question_processed])
            semantic_scores = cosine_similarity(user_semantic, self.semantic_vectors).flatten()
            # Kombinə et
            combined_scores = 0.7 * similarities + 0.3 * semantic_scores
        else:
            combined_scores = similarities
            
        # Ən yaxşı nəticəni tap
        best_idx = np.argmax(combined_scores)
        best_score = combined_scores[best_idx]
        
        # Açar söz nəticələrini də nəzərə al
        if keyword_matches:
            keyword_idx, keyword_score = max(keyword_matches, key=lambda x: x[1])
            if keyword_score > best_score:
                best_idx = keyword_idx
                best_score = keyword_score
        
        if best_score >= threshold:
            return self.answers[best_idx]
        else:
            # Yaxın nəticə yoxdursa, alternativ təklif et
            similar_questions = []
            for idx in np.argsort(similarities)[-3:][::-1]:
                if similarities[idx] > 0.1:
                    similar_questions.append(self.questions[idx])
            
            if similar_questions:
                return f"Bu suala dəqiq cavab tapa bilmədim. Bəlkə bunlardan birini soruşdunuz?\n" + \
                       "\n".join([f"• {q}" for q in similar_questions])
            else:
                return "Üzr istəyirik, sualınızı başa düşmədim. Zəhmət olmasa, sualınızı fərqli şəkildə ifadə edin."
    
    def add_new_question(self, question, answer, keywords, category="general"):
        """Yeni sual-cavab əlavə et"""
        self.questions.append(question)
        self.answers.append(answer)
        self.keywords.append(keywords)
        self.categories.append(category)
        self.prepare_vectors()
        
        # JSON faylına yadda saxla
        self.save_to_json()
        
    def save_to_json(self):
        """Məlumatları JSON-a yaz"""
        data = {}
        try:
            with open('data/faq_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
            
        org_data = []
        for i in range(len(self.questions)):
            org_data.append({
                "question": self.questions[i],
                "answer": self.answers[i],
                "keywords": self.keywords[i],
                "category": self.categories[i]
            })
            
        data[self.organization_id] = org_data
        
        with open('data/faq_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
