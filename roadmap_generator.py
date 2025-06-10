# roadmap_generator.py
import google.generativeai as genai
import os

def generate_roadmap(resume_text):
    genai.configure(api_key="AIzaSyCMkR67rQb6Q1VN0il5lv9RWReUMTOXk9o")
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
You are an expert AI career coach.
Given this resume:
{resume_text}
Generate a detailed 6-month tech learning roadmap for transitioning into a Product Manager role.
Include:
1. Tailored tech stack
2. Free course links
3. 3 personalized project ideas
4. Month-by-month timeline
Ensure accuracy and alignment with the resume.
"""
    response = model.generate_content(prompt)
    return response.text