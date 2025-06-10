# goal_analyzer.py

import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Run once
nltk.download('punkt')
nltk.download('stopwords')

def analyze_goals(text):
    text = text.lower()
    words = word_tokenize(text)
    filtered_words = [
        word for word in words
        if word.isalnum() and word not in stopwords.words('english')
    ]
    return f"🔍 Keywords extracted from your goal:\n{', '.join(set(filtered_words))}"
