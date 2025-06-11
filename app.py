import streamlit as st
import tempfile
import os
import json
import re
import time
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from resume_parser import parse_resume
from roadmap_generator import generate_roadmap
from goal_analyzer import analyze_goals
import google.generativeai as genai

# Configure Streamlit page
st.set_page_config(page_title="SkillWise - AI Roadmap Generator", layout="wide", initial_sidebar_state="expanded")

# Updated UI/UX with improved hover colors, field styles, tab backgrounds, and smaller edit buttons
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

.stApp {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Roboto', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    color: #ffffff;
    font-weight: 500;
}
.stButton>button {
    background-color: #4a69bd;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}
.stButton>button:hover {
    background-color: #60a5fa; /* Updated hover color to a vibrant light blue */
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}
.stTextInput input, .stSelectbox div, .stTextArea textarea {
    background-color: #2d2d44 !important;
    color: #e0e0e0 !important;
    border: none !important; /* Removed border for a cleaner look */
    border-radius: 8px;
    transition: border-color 0.3s ease;
}
.stTextInput input:focus, .stSelectbox div:focus, .stTextArea textarea:focus {
    border: none !important;
    box-shadow: 0 0 5px rgba(96, 165, 250, 0.5) !important; /* Subtle glow on focus */
}
div[data-testid="stFileUploaderDropzone"] {
    background-color: #3b3b5a !important; /* Lighter background for drag-and-drop */
    border: 2px dashed #60a5fa !important; /* Softer border color */
    color: #e0e0e0 !important;
    border-radius: 8px;
}
div[data-testid="stTabs"] button {
    background-color: #2d2d44;
    color: #e0e0e0;
    border-radius: 8px 8px 0 0;
    transition: background-color 0.3s ease;
}
div[data-testid="stTabs"] button:hover {
    background-color: #4a69bd;
}
div[data-testid="stTabs"] button p {
    font-size: 18px !important;
    font-weight: 500 !important;
}
div[data-testid="stTab"] {
    background-color: rgba(45, 45, 68, 0.8); /* Semi-transparent background for tab content */
    padding: 20px; /* Added padding */
    border-radius: 8px;
}
.stProgress .st-bo {
    background-color: #4a69bd !important;
}
.stProgress .st-bo > div {
    background-color: #60a5fa !important; /* Match progress bar with hover color */
}
.stCheckbox label p {
    font-size: 14px !important;
    color: #e0e0e0;
}
button[kind="secondary"][key^="edit_"] {
    font-size: 10px !important; /* Further reduced size */
    padding: 3px 6px !important; /* Further reduced padding */
    background-color: #4a69bd !important;
    border-radius: 6px !important;
}
.footer {
    background-color: #2d2d44;
    padding: 20px;
    text-align: center;
    border-top: 1px solid #4a69bd;
    margin-top: 40px;
    border-radius: 8px;
}
.footer p {
    margin: 10px 0;
    font-size: 14px;
    color: #b0b0b0;
}
.footer a {
    color: #4a69bd;
    text-decoration: none;
    margin: 0 10px;
    transition: color 0.3s ease;
}
.footer a:hover {
    color: #60a5fa; /* Updated hover color for footer links */
}
.social-icons a {
    margin: 0 15px;
    font-size: 20px;
    color: #b0b0b0;
    transition: color 0.3s ease;
}
.social-icons a:hover {
    color: #60a5fa; /* Updated hover color for social icons */
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.stMarkdown, .stSuccess, .stInfo, .stWarning, .stError {
    animation: fadeIn 0.5s ease-in-out;
}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
""", unsafe_allow_html=True)

# Initialize session state
if "roadmap" not in st.session_state:
    st.session_state.roadmap = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "goal" not in st.session_state:
    st.session_state.goal = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "custom_role" not in st.session_state:
    st.session_state.custom_role = ""
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if "progress" not in st.session_state:
    st.session_state.progress = {}
if "editing_section" not in st.session_state:
    st.session_state.editing_section = None
if "generation_time" not in st.session_state:
    st.session_state.generation_time = 10.0
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
if "survey_submitted" not in st.session_state:
    st.session_state.survey_submitted = False
if "resume_upload_time" not in st.session_state:
    st.session_state.resume_upload_time = 5.0

# Onboarding Walkthrough for first-time users
if st.session_state.first_visit:
    st.info("""
    ### Welcome to SkillWise! 🎉
    Follow these steps to get started:
    1. **Enter your Gemini API Key** in the sidebar (⚙️ Configuration).
    2. **Upload your resume** in the Resume tab (📄 Upload Your Resume).
    3. **Select your career goal and role** (e.g., AI Engineer).
    4. Click **Generate Roadmap** to create your personalized learning path.
    5. Explore your roadmap in the Roadmap tab (🗺️).
    """)
    st.session_state.first_visit = False

# Load progress from file
def load_progress():
    if os.path.exists("progress.json"):
        with open("progress.json", "r") as f:
            st.session_state.progress = json.load(f)

# Save progress to file
def save_progress():
    with open("progress.json", "w") as f:
        json.dump(st.session_state.progress, f)

# Handle Gemini API key with Submit button and Change option
with st.sidebar:
    st.header("⚙️ Configuration")
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Gemini API key not found. Please enter it below.")
        api_key_input = st.text_input("Enter Gemini API Key", type="password")
        if st.button("Submit"):
            if api_key_input:
                st.session_state.gemini_api_key = api_key_input
                genai.configure(api_key=api_key_input)
                st.success("✅ API Key submitted!")
            else:
                st.error("❌ Please enter a valid API key.")
    else:
        st.success("✅ API Key is set!")
        if st.button("🔄 Change API Key"):
            st.session_state.gemini_api_key = ""
            st.rerun()

st.title("🧠 SkillWise: AI-Powered Learning Path Generator")

# Tabs
tab1, tab2 = st.tabs(["Resume", "Roadmap"])

# Resume Tab
with tab1:
    st.subheader("🎯 Select Career Goal")
    st.session_state.goal = st.text_input("What role are you targeting?", placeholder="e.g., AI Developer, Product Manager", value=st.session_state.goal)
    
    if st.session_state.goal.strip():
        goal_analysis = analyze_goals(st.session_state.goal)
        st.markdown(goal_analysis)
    
    st.subheader("📚 Select Tech Role")
    roles = [
        "Select a tech role",
        "AI Engineer",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "Product Manager",
        "Data Analyst",
        "Cybersecurity Expert",
        "DevOps Engineer",
        "UI/UX Designer",
        "Machine Learning Engineer",
        "Blockchain Developer",
        "Cloud Architect",
        "Data Scientist",
        "Software Engineer",
        "Mobile App Developer",
        "Other"
    ]
    st.session_state.role = st.selectbox("Choose a role", roles, index=roles.index(st.session_state.role) if st.session_state.role in roles else 0)
    
    if st.session_state.role == "Other":
        st.session_state.custom_role = st.text_input("Please specify your role", placeholder="e.g., Game Developer", value=st.session_state.custom_role)
    
    effective_role = st.session_state.custom_role if st.session_state.role == "Other" and st.session_state.custom_role else st.session_state.role
    
    st.subheader("📄 Upload Your Resume")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
    
    if uploaded_file is not None:
        progress_bar = st.progress(0)
        eta_placeholder = st.empty()
        start_time = time.time()
        
        # Estimate total time
        estimated_time = st.session_state.resume_upload_time
        
        # Phase 1: Upload (30% of progress)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        for i in range(30):
            time.sleep(0.05)
            progress = (i + 1) / 100
            elapsed = time.time() - start_time
            eta = max(0, estimated_time - elapsed)
            progress_bar.progress(int(progress * 100))
            eta_placeholder.text(f"⏳ Uploading... Estimated time remaining: {eta:.1f} seconds")
        
        # Phase 2: Parsing (70% of progress)
        try:
            parse_start = time.time()
            st.session_state.resume_text = parse_resume(tmp_path)
            parse_end = time.time()
            parse_time = parse_end - parse_start
            
            for i in range(30, 100):
                time.sleep(parse_time / 70)
                progress = (i + 1) / 100
                elapsed = time.time() - start_time
                eta = max(0, estimated_time - elapsed)
                progress_bar.progress(int(progress * 100))
                eta_placeholder.text(f"⏳ Parsing... Estimated time remaining: {eta:.1f} seconds")
            
            if len(st.session_state.resume_text.strip()) > 20:
                st.success("✅ Resume uploaded and parsed successfully!")
            else:
                st.error("⚠️ Failed to extract meaningful content. Try another resume.")
        except FileNotFoundError:
            if len(st.session_state.resume_text.strip()) > 20:
                st.success("✅ Resume uploaded and parsed!")
            else:
                st.error("⚠️ Failed to extract meaningful content. Try another resume.")
        except Exception as e:
            st.error(f"❌ Error parsing resume: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass
        
        # Update estimated time for future uploads
        total_time = time.time() - start_time
        st.session_state.resume_upload_time = total_time
        progress_bar.empty()
        eta_placeholder.empty()
    
    if st.button("🚀 Generate Roadmap"):
        if not st.session_state.resume_text.strip():
            st.warning("⚠️ Please upload a resume.")
        elif effective_role == "Select a tech role":
            st.warning("⚠️ Please select a valid role.")
        elif st.session_state.role == "Other" and not st.session_state.custom_role.strip():
            st.warning("⚠️ Please specify a role in the text field.")
        elif not st.session_state.gemini_api_key:
            st.error("❌ Please enter a Gemini API key in the sidebar.")
        else:
            with st.spinner("Generating roadmap..."):
                progress_bar = st.progress(0)
                eta_placeholder = st.empty()
                start_time = time.time()
                
                stages = {
                    "Analyzing Resume": 30,
                    "Generating Prompt": 20,
                    "API Call & Response": 50
                }
                total_stages = sum(stages.values())
                current_progress = 0
                
                for i in range(stages["Analyzing Resume"]):
                    time.sleep(0.05)
                    current_progress += 1
                    progress = (current_progress / total_stages) * 100
                    elapsed = time.time() - start_time
                    eta = max(0, st.session_state.generation_time - elapsed)
                    progress_bar.progress(int(progress))
                    eta_placeholder.text(f"⏳ Analyzing Resume... Estimated time remaining: {eta:.1f} seconds")
                
                genai.configure(api_key=st.session_state.gemini_api_key)
                prompt = (
                    f"Create a personalized learning roadmap to help the user achieve their career goal of becoming a {effective_role} "
                    f"with the specific aspiration: '{st.session_state.goal}'. "
                    f"Here is the user's resume: {st.session_state.resume_text}. "
                    f"Analyze the resume to identify current skills and experience. "
                    f"Based on the role of {effective_role}, identify the key skills and knowledge areas required, "
                    f"and focus on bridging the gaps between the user's current skills and the role's requirements. "
                    f"Provide a step-by-step roadmap with actionable learning steps, including specific resources (e.g., courses, tutorials) "
                    f"and tag each resource with relevant labels (e.g., 'YouTube', 'Beginner-Friendly', 'Coursera') in the format: "
                    f"'* <step> - <tag1>, <tag2>'. Ensure the roadmap is practical and tailored to the user's goal and role."
                )
                for i in range(stages["Generating Prompt"]):
                    time.sleep(0.03)
                    current_progress += 1
                    progress = (current_progress / total_stages) * 100
                    elapsed = time.time() - start_time
                    eta = max(0, st.session_state.generation_time - elapsed)
                    progress_bar.progress(int(progress))
                    eta_placeholder.text(f"⏳ Generating Prompt... Estimated time remaining: {eta:.1f} seconds")
                
                roadmap_start = time.time()
                st.session_state.roadmap = generate_roadmap(prompt)
                roadmap_end = time.time()
                api_time = roadmap_end - roadmap_start
                
                for i in range(stages["API Call & Response"]):
                    time.sleep(api_time / 50)
                    current_progress += 1
                    progress = (current_progress / total_stages) * 100
                    elapsed = time.time() - start_time
                    eta = max(0, st.session_state.generation_time - elapsed)
                    progress_bar.progress(int(progress))
                    eta_placeholder.text(f"⏳ Fetching Roadmap... Estimated time remaining: {eta:.1f} seconds")
                
                actual_time = time.time() - start_time
                st.session_state.generation_time = actual_time
                
                progress_bar.empty()
                eta_placeholder.empty()
            
            st.success("✅ Roadmap generated! Check it in the Roadmap tab.")
            
            if not st.session_state.survey_submitted:
                st.subheader("📋 Quick Feedback")
                ease_rating = st.slider(
                    "How easy was it to generate your roadmap?",
                    min_value=1,
                    max_value=5,
                    value=3,
                    step=1,
                    format="%d",
                    help="1 = Very Difficult, 5 = Very Easy"
                )
                if st.button("Submit Feedback"):
                    feedback_data = {
                        "rating": ease_rating,
                        "timestamp": datetime.now().isoformat()
                    }
                    with open("survey_feedback.json", "a") as f:
                        json.dump(feedback_data, f)
                        f.write("\n")
                    st.success("✅ Thank you for your feedback!")
                    st.session_state.survey_submitted = True

# Roadmap Tab
with tab2:
    if st.session_state.roadmap:
        st.markdown('<h1 style="font-size: 40px;">🗺️ Your AI-Powered Learning Roadmap</h1><br>', unsafe_allow_html=True)
        
        required_skills = {
            "AI Engineer": ["Python", "Machine Learning", "TensorFlow", "NLP"],
            "Frontend Developer": ["HTML", "CSS", "JavaScript", "React"],
            "Backend Developer": ["Python", "Node.js", "SQL", "REST APIs"],
            "Full Stack Developer": ["HTML", "JavaScript", "Node.js", "SQL"],
            "Product Manager": ["Agile", "SQL", "Figma", "Jira"],
            "Data Analyst": ["SQL", "Excel", "Tableau", "Python"],
            "Cybersecurity Expert": ["Networking", "Penetration Testing", "Cryptography", "Linux"],
            "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "UI/UX Designer": ["Figma", "Adobe XD", "User Research", "Prototyping"],
            "Machine Learning Engineer": ["Python", "TensorFlow", "Scikit-learn", "Deep Learning"],
            "Blockchain Developer": ["Solidity", "Ethereum", "Smart Contracts", "Cryptography"],
            "Cloud Architect": ["AWS", "Azure", "GCP", "Terraform"],
            "Data Scientist": ["Python", "R", "Machine Learning", "Statistics"],
            "Software Engineer": ["Java", "Python", "Git", "Algorithms"],
            "Mobile App Developer": ["Swift", "Kotlin", "React Native", "Flutter"]
        }
        default_skills = ["Python", "Git", "Problem Solving", "Communication"]
        skills_to_check = required_skills.get(effective_role, default_skills)
        
        if skills_to_check:
            matching_skills = [skill for skill in skills_to_check if skill.lower() in st.session_state.resume_text.lower()]
            skill_match_score = (len(matching_skills) / len(skills_to_check)) * 100
            st.subheader("📊 Skill Match Score")
            st.markdown(f'<p style="font-size: 40px;"><h5>●    Your skills match {skill_match_score:.1f}% of the requirements for {effective_role}.</h5></p>', unsafe_allow_html=True)
        
        course_recommendations = {
            "Python": "Python for Everybody - Coursera",
            "Machine Learning": "Machine Learning by Andrew Ng - Coursera",
            "TensorFlow": "TensorFlow Developer Certificate - Coursera",
            "NLP": "Natural Language Processing Specialization - Coursera",
            "HTML": "HTML, CSS, and Javascript for Web Developers - Coursera",
            "CSS": "HTML, CSS, and Javascript for Web Developers - Coursera",
            "JavaScript": "JavaScript: The Complete Guide - Udemy",
            "React": "React - The Complete Guide - Udemy",
            "Node.js": "Node.js, Express, MongoDB & More - Udemy",
            "SQL": "SQL for Data Science - Coursera",
            "REST APIs": "REST API Design, Development & Management - Udemy",
            "Agile": "Agile Project Management - Udemy",
            "Figma": "Figma for UI/UX Design - Udemy",
            "Jira": "Mastering Jira - Udemy",
            "Excel": "Excel Skills for Business - Coursera",
            "Tableau": "Data Visualization with Tableau - Coursera",
            "Networking": "Networking Fundamentals - Cisco Networking Academy",
            "Penetration Testing": "Penetration Testing with Kali Linux - Udemy",
            "Cryptography": "Cryptography I - Coursera",
            "Linux": "Linux Mastery: Master the Linux Command Line - Udemy",
            "Docker": "Docker Mastery: The Complete Guide - Udemy",
            "Kubernetes": "Kubernetes for the Absolute Beginners - Udemy",
            "AWS": "AWS Certified Solutions Architect - Udemy",
            "CI/CD": "CI/CD with Jenkins and GitLab - Coursera",
            "Adobe XD": "Adobe XD for Beginners - Udemy",
            "User Research": "User Research and Design - Coursera",
            "Prototyping": "Prototyping with Figma - Udemy",
            "Scikit-learn": "Machine Learning with Python - Coursera",
            "Deep Learning": "Deep Learning Specialization - Coursera",
            "Solidity": "Solidity and Ethereum Smart Contracts - Udemy",
            "Ethereum": "Blockchain and Ethereum Development - Coursera",
            "Smart Contracts": "Smart Contracts with Solidity - Udemy",
            "Azure": "Microsoft Azure Fundamentals - Coursera",
            "GCP": "Google Cloud Platform Fundamentals - Coursera",
            "Terraform": "Terraform for Beginners - Udemy",
            "R": "R Programming - Coursera",
            "Statistics": "Statistics with R - Coursera",
            "Java": "Java Programming: Complete Beginner to Advanced - Udemy",
            "Git": "Git Complete: The Definitive Guide - Udemy",
            "Algorithms": "Algorithms and Data Structures - Coursera",
            "Swift": "iOS Development with Swift - Udemy",
            "Kotlin": "Kotlin for Android Development - Udemy",
            "React Native": "React Native - The Practical Guide - Udemy",
            "Flutter": "Flutter & Dart - The Complete Guide - Udemy",
            "Problem Solving": "Problem Solving for Developers - Udemy",
            "Communication": "Effective Communication Skills - Coursera"
        }
        if skills_to_check:
            missing_skills = [skill for skill in skills_to_check if skill.lower() in st.session_state.resume_text.lower()]
            if missing_skills:
                st.subheader("🔍 Skill Gap Analysis")
                st.markdown(f'<p style="font-size: 40px;"><h5>●    Skills missing for {effective_role}: {", ".join(missing_skills)}</h5></p>', unsafe_allow_html=True)
                st.subheader("📚 Recommended Courses for Skill Gaps")
                for skill in missing_skills:
                    if skill in course_recommendations:
                        st.markdown(f"- **{skill}**: {course_recommendations[skill]}")
                    else:
                        st.markdown(f"- **{skill}**: No specific course recommendation available. Try searching on Coursera or Udemy.")
            else:
                st.markdown(f'<p style="font-size: 40px;"><h5>✅ Your resume covers all key skills for this role!</h5></p>', unsafe_allow_html=True)
        
        st.subheader("🏷️ Filter Courses")
        tags = set()
        for line in st.session_state.roadmap.splitlines():
            line = line.strip()
            if not line or not line.startswith("*"):
                continue
            if " - " in line:
                parts = line.split(" - ", 1)
                tag_part = parts[-1]
                if "," in tag_part:
                    line_tags = [tag.strip() for tag in tag_part.split(",")]
                    tags.update(line_tags)
            elif "[" in line and "]" in line:
                tag_part = line[line.find("[") + 1:line.find("]")]
                if "," in tag_part:
                    line_tags = [tag.strip() for tag in tag_part.split(",")]
                    tags.update(line_tags)
        
        if not tags:
            tags = {"YouTube", "Beginner-Friendly", "Advanced", "Udemy", "Coursera"}
            st.warning("⚠️ No tags found in the roadmap. Using default tags. Below is the roadmap content for debugging:")
            st.text_area("Roadmap Content", st.session_state.roadmap, height=200)
        
        selected_tags = st.multiselect("Filter by tags (e.g., YouTube, Beginner-Friendly)", sorted(tags))
        
        st.subheader("📈 Progress Tracker")
        load_progress()
        roadmap_lines = st.session_state.roadmap.splitlines()
        current_section = None
        section_content = []
        for i, line in enumerate(roadmap_lines):
            line = line.strip()
            if not line:
                continue
            display_line = line
            if selected_tags:
                line_tags = []
                if " - " in line:
                    tag_part = line.split(" - ", 1)[-1]
                    if "," in tag_part:
                        line_tags = [tag.strip() for tag in tag_part.split(",")]
                elif "[" in line and "]" in line:
                    tag_part = line[line.find("[") + 1:line.find("]")]
                    if "," in tag_part:
                        line_tags = [tag.strip() for tag in tag_part.split(",")]
                if not all(tag in line_tags for tag in selected_tags):
                    continue
            
            if line.startswith("**"):
                if current_section and section_content:
                    st.markdown(f"## {current_section}")
                    if any(item.startswith("*") for item in section_content):
                        if st.button("Edit Section", key=f"edit_{i-len(section_content)}"):
                            st.session_state.editing_section = i - len(section_content)
                    for content_line in section_content:
                        if content_line.startswith("*"):
                            item_key = f"{current_section}_{content_line}"
                            if item_key not in st.session_state.progress:
                                st.session_state.progress[item_key] = False
                            completed = st.checkbox(f"{content_line[1:]}", value=st.session_state.progress[item_key], key=f"check_{i}_{content_line}")
                            if completed != st.session_state.progress[item_key]:
                                st.session_state.progress[item_key] = completed
                                save_progress()
                        else:
                            st.markdown(content_line)
                current_section = line[2:]
                section_content = []
            else:
                section_content.append(line)
        
        if current_section and section_content:
            st.markdown(f"## {current_section}")
            if any(item.startswith("*") for item in section_content):
                if st.button("Edit Section", key=f"edit_{len(roadmap_lines)-1}"):
                    st.session_state.editing_section = len(roadmap_lines) - len(section_content)
            for content_line in section_content:
                if content_line.startswith("*"):
                    item_key = f"{current_section}_{content_line}"
                    if item_key not in st.session_state.progress:
                        st.session_state.progress[item_key] = False
                    completed = st.checkbox(f"{content_line[1:]}", value=st.session_state.progress[item_key], key=f"check_{len(roadmap_lines)}_{content_line}")
                    if completed != st.session_state.progress[item_key]:
                        st.session_state.progress[item_key] = completed
                        save_progress()
                else:
                    st.markdown(content_line)
        
        if st.session_state.editing_section is not None:
            edit_index = st.session_state.editing_section
            section_line = roadmap_lines[edit_index]
            st.subheader(f"Editing Section: {section_line[2:]}")
            new_text = st.text_area("Reword this section:", value=section_line[2:])
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Save Changes"):
                    roadmap_lines[edit_index] = f"**{new_text}"
                    st.session_state.roadmap = "\n".join(roadmap_lines)
                    st.session_state.editing_section = None
                    st.rerun()
            with col2:
                if st.button("Regenerate Section"):
                    if st.session_state.gemini_api_key:
                        with st.spinner("Regenerating section..."):
                            genai.configure(api_key=st.session_state.gemini_api_key)
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            prompt = f"Rewrite this roadmap section for {effective_role}: {section_line[2:]}"
                            response = model.generate_content(prompt)
                            roadmap_lines[edit_index] = f"**{response.text.strip()}"
                            st.session_state.roadmap = "\n".join(roadmap_lines)
                            st.session_state.editing_section = None
                            st.rerun()
                    else:
                        st.error("❌ Please enter a Gemini API key in the sidebar.")
            with col3:
                if st.button("Cancel"):
                    st.session_state.editing_section = None
                    st.rerun()
        
        st.subheader("❓ Ask About Your Roadmap")
        question = st.text_input("Enter your question (e.g., 'How long will SQL take?')")
        if st.button("Get Answer"):
            if question:
                if not st.session_state.gemini_api_key:
                    st.error("❌ Please enter a Gemini API key in the sidebar.")
                else:
                    try:
                        with st.spinner("Fetching answer..."):
                            genai.configure(api_key=st.session_state.gemini_api_key)
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            response = model.generate_content(f"Roadmap: {st.session_state.roadmap}\nQuestion: {question}")
                            st.markdown(response.text)
                    except Exception as e:
                        st.error(f"❌ Error fetching answer: {e}")
            else:
                st.warning("⚠️ Please enter a question.")
        
        st.subheader("💬 Was this helpful?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Yes"):
                with open("feedback.json", "a") as f:
                    json.dump({"roadmap": st.session_state.roadmap, "feedback": "positive", "timestamp": datetime.now().isoformat()}, f)
                    f.write("\n")
                st.success("✅ Thank you for your feedback!")
        with col2:
            if st.button("👎 No"):
                with open("feedback.json", "a") as f:
                    json.dump({"roadmap": st.session_state.roadmap, "feedback": "negative", "timestamp": datetime.now().isoformat()}, f)
                    f.write("\n")
                st.success("✅ Thank you for your feedback! We'll work on improving.")
        
        st.subheader("📥 Export Your Roadmap")
        
        st.download_button(
            label="📄 Download as TXT",
            data=st.session_state.roadmap,
            file_name="SkillWise_Roadmap.txt",
            mime="text/plain"
        )
        
        # PDF export with fixed formatting
        def clean_text(text):
            replacements = {
                "–": "-",  # En dash to hyphen
                "—": "-",  # Em dash to hyphen
                "’": "'",  # Right single quote to straight quote
                "‘": "'",  # Left single quote to straight quote
                "“": '"',  # Left double quote to straight quote
                "”": '"',  # Right double quote to straight quote
                "*": "",  # Remove residual Markdown stars
                ". ": "- ",  # Standardize bullet points
            }
            for unicode_char, ascii_char in replacements.items():
                text = text.replace(unicode_char, ascii_char)
            return text.encode("ascii", "ignore").decode("ascii")

        def wrap_text(c, text, x, y, max_width, font_name, font_size, line_spacing=12):
            c.setFont(font_name, font_size)
            words = text.split()
            lines = []
            current_line = []
            current_width = 0

            for word in words:
                word_width = c.stringWidth(word + " ", font_name, font_size)
                if current_width + word_width <= max_width:
                    current_line.append(word)
                    current_width += word_width
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
            if current_line:
                lines.append(" ".join(current_line))

            for line in lines:
                c.drawString(x, y, line)
                y -= line_spacing
            return y

        def generate_pdf():
            from io import BytesIO
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Margins
            left_margin = inch
            right_margin = inch
            top_margin = inch
            bottom_margin = 0.5 * inch
            content_width = width - left_margin - right_margin

            # Colors
            header_color = HexColor("#2E2E2E")
            text_color = HexColor("#000000")
            accent_color = HexColor("#4682B4")
            bg_color = HexColor("#E6F0FA")

            def draw_header():
                c.setFont("Helvetica-Bold", 12)
                c.setFillColor(accent_color)
                c.drawString(left_margin, height - 0.5 * inch, "SkillWise Learning Roadmap")
                c.setFillColor(text_color)

            def draw_footer(page_num):
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColor(header_color)
                c.drawCentredString(width / 2, bottom_margin, f"Generated by SkillWise | Page {page_num}")
                c.setFillColor(text_color)

            # Initialize variables
            y_position = height - top_margin
            page_num = 1

            # Draw first page header and logo
            draw_header()
            # Add logo from the provided path
            c.drawImage(r"F:\Sahaj\Python\SkillWise\logo.png", left_margin, height - 0.8 * inch, width=1.5*inch, height=0.5*inch)

            # Title (ensure no duplication)
            c.setFont("Helvetica-Bold", 16)
            c.setFillColor(header_color)
            y_position -= 20  # Extra spacing to account for logo
            y_position = wrap_text(
                c, "SkillWise Learning Roadmap", left_margin, y_position, content_width,
                "Helvetica-Bold", 16, line_spacing=20
            )
            c.setFillColor(text_color)

            # Generation date
            c.setFont("Helvetica", 10)
            y_position -= 10
            y_position = wrap_text(
                c, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", left_margin, y_position,
                content_width, "Helvetica", 10, line_spacing=14
            )

            # Process roadmap content
            lines = st.session_state.roadmap.splitlines()
            current_phase = None
            indent = left_margin
            bullet_indent = left_margin + 0.3 * inch

            for line in lines:
                line = clean_text(line.strip())
                if not line:
                    continue

                if y_position < bottom_margin + 1.5 * inch:
                    draw_footer(page_num)
                    c.showPage()
                    page_num += 1
                    draw_header()
                    y_position = height - top_margin

                if line.startswith("##"):
                    text = line[2:].strip()
                    c.setFont("Helvetica-Bold", 14)
                    c.setFillColor(header_color)
                    y_position -= 10
                    y_position = wrap_text(
                        c, text, left_margin, y_position, content_width,
                        "Helvetica-Bold", 14, line_spacing=16
                    )
                    c.setFillColor(text_color)
                    y_position -= 10
                    indent = left_margin

                elif line.startswith("**") and line.endswith("**"):
                    text = line[2:-2].strip()
                    if y_position < bottom_margin + 3 * inch:
                        draw_footer(page_num)
                        c.showPage()
                        page_num += 1
                        draw_header()
                        y_position = height - top_margin

                    c.setFillColor(bg_color)
                    c.rect(left_margin - 10, y_position - 5, content_width + 20, 20, fill=True, stroke=False)
                    c.setFillColor(accent_color)
                    c.setFont("Helvetica-Bold", 12)
                    y_position -= 10
                    y_position = wrap_text(
                        c, text, left_margin, y_position, content_width,
                        "Helvetica-Bold", 12, line_spacing=14
                    )
                    c.setFillColor(text_color)
                    y_position -= 5
                    indent = left_margin
                    current_phase = text

                elif line.startswith("-"):
                    text = line[1:].strip()
                    c.setFont("Helvetica", 10)
                    y_position = wrap_text(
                        c, f"- {text}", bullet_indent, y_position, content_width - 0.3 * inch,
                        "Helvetica", 10, line_spacing=12
                    )
                    indent = bullet_indent

                elif line.startswith("  •"):
                    text = line[3:].strip()
                    c.setFont("Helvetica", 10)
                    y_position = wrap_text(
                        c, f"  • {text}", bullet_indent + 0.2 * inch, y_position, content_width - 0.5 * inch,
                        "Helvetica", 10, line_spacing=12
                    )
                    indent = bullet_indent + 0.2 * inch

                else:
                    c.setFont("Helvetica", 10)
                    y_position = wrap_text(
                        c, line, indent, y_position, content_width - (indent - left_margin),
                        "Helvetica", 10, line_spacing=12
                    )

            draw_footer(page_num)
            c.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes

        if st.button("📄 Download as PDF"):
            try:
                pdf_bytes = generate_pdf()
                st.download_button(
                    label="📄 Click to Download PDF",
                    data=pdf_bytes,
                    file_name="SkillWise_Roadmap.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"❌ Error generating PDF: {str(e)}")
        
        roadmap_data = {
            "resume": st.session_state.resume_text,
            "goal": st.session_state.goal,
            "role": effective_role,
            "roadmap": st.session_state.roadmap,
            "timestamp": datetime.now().isoformat()
        }
        st.download_button(
            label="💾 Download as JSON",
            data=json.dumps(roadmap_data, indent=2),
            file_name="SkillWise_Roadmap.json",
            mime="application/json"
        )
        
        unique_id = hash(st.session_state.roadmap) % 1000000
        with open(f"roadmap_{unique_id}.json", "w") as f:
            json.dump(roadmap_data, f)
        st.markdown(f"🔗 Shareable link: `http://skillwise.local/roadmap/{unique_id}` (Note: Deploy to a server for real links)")
    else:
        st.info("🚧 Generate a roadmap in the Resume tab.")

# Footer
st.markdown("""
<div class="footer">
    <div class="social-icons">
        <a href="https://github.com/Sahaj33-op/" target="_blank"><i class="fab fa-github"></i></a>
    </div>
    <p>© 2025 SkillWise. All rights reserved.</p>
    <p>
        <a href="mailto:support@skillwise.local">Contact Us</a> | 
        <a href="http://skillwise.local/terms.html" target="_blank">Terms of Service</a>
    </p>
</div>
""", unsafe_allow_html=True)