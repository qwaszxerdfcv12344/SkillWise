# roadmap_generator.py
import google.generativeai as genai
import os

def generate_roadmap(prompt):  # Change parameter to accept the prompt directly
    # API key should already be configured in app.py
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text