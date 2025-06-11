import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def ensure_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

def analyze_goals(text):
    ensure_nltk_data()  # Ensure NLTK data is available
    try:
        text = text.lower()
        words = word_tokenize(text)
        filtered_words = [
            word for word in words
            if word.isalnum() and word not in stopwords.words('english')
        ]
        keywords = set(filtered_words)
        if not keywords:
            return "⚠️ No meaningful keywords extracted from your goal."
        return f"🔍 Keywords extracted from your goal:\n{', '.join(keywords)}"
    except Exception as e:
        return f"⚠️ Error analyzing goal: {str(e)}"