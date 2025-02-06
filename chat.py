import os
import re
import spacy
import docx2txt
import PyPDF2
from flask import Flask, request, render_template

app = Flask(__name__)
nlp = spacy.load('en_core_web_sm')
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(docx_path):
    return docx2txt.process(docx_path)

def extract_text(file_path):
    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    else:
        return "Unsupported file format"

def extract_skills(text):
    skills = ["Python", "Machine Learning", "Deep Learning", "NLP", "Data Science", "TensorFlow", "PyTorch", "SQL"]
    extracted_skills = [skill for skill in skills if skill.lower() in text.lower()]
    return extracted_skills

def extract_experience(text):
    experience = re.findall(r'\b(\d+)\s*(?:years|yrs|year)\b', text, re.IGNORECASE)
    return max(map(int, experience)) if experience else 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return "No file uploaded!"
    file = request.files['resume']
    if file.filename == "":
        return "No file selected!"
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    text = extract_text(file_path)
    skills = extract_skills(text)
    experience = extract_experience(text)
    
    return render_template('index.html', skills=skills, experience=experience)

if __name__ == '__main__':
    app.run(debug=True)