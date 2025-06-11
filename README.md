SkillWise: AI-Powered Learning Path Generator 🧠
SkillWise is a Streamlit app that generates personalized learning roadmaps based on your resume, career goals, and target tech role. It includes skill gap analysis, course recommendations, and progress tracking.

🚀 Demo
Try the app live: SkillWise on Streamlit Community Cloud (Update this link after deployment)

📋 Features
- Upload your resume (PDF) to analyze your skills.
- Select a tech role (e.g., AI Engineer, Data Scientist) or specify a custom role.
- Generate a tailored learning roadmap with actionable steps.
- Skill match score and gap analysis with course recommendations.
- Progress tracker, interactive Q&A, and export options (TXT, PDF, JSON).
- Footer with social media handles and copyright notice.

🛠️ Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Sahaj33-op/SkillWise.git
   cd SkillWise
   ```
2. **Install Dependencies**:
   Ensure you have Python 3.8+ installed.
   Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Tesseract for OCR**:
   - Download and install Tesseract from [here](https://github.com/UB-Mannheim/tesseract/wiki).
   - Add Tesseract to your system PATH (e.g., `C:\Program Files\Tesseract-OCR`).
4. **Set Up Gemini API Key**:
   - Obtain a Gemini API key from Google AI.
   - Set the environment variable (Windows):
     ```bash
     set GOOGLE_API_KEY=your_api_key
     ```
   Alternatively, enter the API key in the app’s sidebar.
5. **Run the App Locally**:
   ```bash
   streamlit run app.py
   ```
   The app will open in your browser at `http://localhost:8501`.

📦 Project Structure
- `app.py`: Main Streamlit app.
- `resume_parser.py`: Parses PDF resumes.
- `roadmap_generator.py`: Generates learning roadmaps using Gemini API.
- `goal_analyzer.py`: Analyzes career goals by extracting keywords.
- `requirements.txt`: Lists Python dependencies.

📄 Dependencies
- streamlit
- fpdf
- pymupdf
- pytesseract
- google-generativeai
- pillow
- nltk

📜 License
© 2025 SkillWise. All rights reserved.

📱 Connect with Us
- [GitHub](https://github.com/Sahaj33-op/)
For support, email us at support@skillwise.local.