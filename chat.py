from flask import Flask, request, jsonify
import spacy
import pdfplumber
import re

app = Flask(__name__)

# Load NLP model for text processing
nlp = spacy.load("en_core_web_sm")

# Job role and required skills mapping
JOB_SKILLS = {
    "data scientist": {"python", "sql", "machine learning", "deep learning", "data analysis", "tensorflow"},
    "web developer": {"html", "css", "javascript", "react", "node.js", "flask", "django"},
    "ai engineer": {"python", "tensorflow", "pytorch", "nlp", "computer vision", "ai"},
    "software engineer": {"java", "c++", "python", "sql", "oop", "algorithms"},
}

EXPECTED_SECTIONS = ["experience", "education", "skills", "projects", "certifications", "contact"]
WEAK_PHRASES = ["hardworking", "team player", "responsible", "dedicated", "detail-oriented"]
ACTION_VERBS = {"developed", "led", "managed", "created", "designed", "implemented", "optimized"}

def extract_text_from_pdf(pdf_file):
    """Extracts text from a PDF resume using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""  
    except Exception as e:
        print(f"Error extracting text: {e}")
    return text.strip() if text else "No text extracted"

def evaluate_resume(text, job_role):
    """Extracts skills and evaluates resume based on job role."""
    doc = nlp(text)
    extracted_skills = {token.text.lower() for token in doc if token.is_alpha}

    job_role = job_role.strip().lower().replace('"', '')
    required_skills = JOB_SKILLS.get(job_role, set())
    matched_skills = extracted_skills & required_skills
    score = int((len(matched_skills) / len(required_skills)) * 100) if required_skills else 0

    return list(matched_skills) if matched_skills else ["No skills detected"], score

def detect_weak_phrases(text):
    return [phrase for phrase in WEAK_PHRASES if phrase in text.lower()]

def detect_action_verbs(text):
    bullet_points = re.findall(r"[-•]\s*(.*)", text)
    return [bp for bp in bullet_points if not any(word in bp.lower().split() for word in ACTION_VERBS)]

def detect_passive_voice(text):
    return [sent.text for sent in nlp(text).sents if "was" in sent.text.lower() or "were" in sent.text.lower()][:3]

def detect_personal_pronouns(text):
    doc = nlp(text)
    pronouns = [token.text for token in doc if token.lower_ in ["i", "me", "my"]]
    return len(pronouns) if len(pronouns) > 10 else 0  

def generate_resume_feedback(text, job_role):
    """Provides feedback on resume content and improvements."""
    feedback = []

    missing_sections = [section for section in EXPECTED_SECTIONS if section.lower() not in text.lower()]
    if missing_sections:
        feedback.append(f"Consider adding these missing sections: {', '.join(missing_sections)}.")

    extracted_skills, _ = evaluate_resume(text, job_role)
    required_skills = JOB_SKILLS.get(job_role.lower(), set())

    missing_skills = required_skills - set(extracted_skills)
    if missing_skills:
        feedback.append(f"Consider adding these missing skills relevant to {job_role}: {', '.join(missing_skills)}.")

    word_count = len(re.findall(r'\w+', text))
    if word_count < 150:
        feedback.append("Your resume seems too short. Try adding more details on experience, projects, or skills.")
    elif word_count > 600:
        feedback.append("Your resume seems too long. Keep it concise and limit it to 1-2 pages.")

    weak_phrases = detect_weak_phrases(text)
    if weak_phrases:
        feedback.append(f"Consider replacing generic words like {', '.join(weak_phrases)} with specific achievements.")

    weak_bullets = detect_action_verbs(text)
    if weak_bullets:
        feedback.append("Some bullet points lack strong action verbs. Start each point with words like 'Managed', 'Led', 'Developed'.")

    passive_voice_sentences = detect_passive_voice(text)
    if passive_voice_sentences:
        feedback.append(f"Your resume contains passive voice in these sentences: {', '.join(passive_voice_sentences)}. Use active voice for impact.")

    pronoun_count = detect_personal_pronouns(text)
    if pronoun_count:
        feedback.append("Your resume has too many personal pronouns (I, me, my). Focus on skills and achievements instead.")

    return feedback

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    job_role = request.form.get("job_role", "").strip()
    if not job_role:
        return jsonify({"error": "Job role is required"}), 400

    files = request.files.getlist('resume')  
    results = []

    for file in files:
        if file.filename == '':
            continue

        text = extract_text_from_pdf(file)

        if text == "No text extracted":
            results.append({
                "filename": file.filename,
                "extracted_skills": "No skills detected (PDF may not contain selectable text)",
                "score": 0,
                "job_role": job_role,
                "feedback": ["No text detected in resume. Ensure it is not a scanned image."]
            })
            continue

        extracted_skills, score = evaluate_resume(text, job_role)
        feedback = generate_resume_feedback(text, job_role)

        results.append({
            "filename": file.filename,
            "extracted_skills": extracted_skills,
            "score": score,
            "job_role": job_role,
            "feedback": feedback
        })

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
