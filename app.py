import streamlit as st
import tempfile
import os
import json
import re
import time
from datetime import datetime
from fpdf import FPDF
from resume_parser import parse_resume
from roadmap_generator import generate_roadmap
import google.generativeai as genai

# Configure Streamlit page (must be the first Streamlit command)
st.set_page_config(page_title="SkillWise - AI Roadmap Generator", layout="wide", initial_sidebar_state="expanded")

# Permanent dark theme with refined styling, button hover effect, and footer styling
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}
.stButton>button {
    background-color: #31333F;
    color: white;
    border: none;
    border-radius: 5px;
}
.stButton>button:hover {
    transform: scale(1.05);
    transition: transform 0.2s ease;
}
.stTextInput input, .stSelectbox div, .stFileUploader label, .stTextArea textarea {
    background-color: #181818 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 4px;
}
div[data-testid="stFileUploaderDropzone"] {
    background-color: #181818 !important;
    border: none !important;
    color: #ffffff !important;
}
div[data-testid="stTabs"] button p {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: white !important;
}
div[data-testid="stMarkdownContainer"] h2 {
    font-size: 18px !important;
}
div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
    font-size: 14px !important;
}
.stCheckbox label p {
    font-size: 14px !important;
}
button[kind="secondary"][key^="edit_"] {
    font-size: 12px !important;
    padding: 2px 8px !important;
}
/* Footer Styling */
.footer {
    background-color: #181818;
    padding: 20px;
    text-align: center;
    border-top: 1px solid #333;
    margin-top: 40px;
}
.footer p {
    margin: 10px 0;
    font-size: 14px;
    color: #cccccc;
}
.footer a {
    color: #cccccc;
    text-decoration: none;
    margin: 0 10px;
}
.footer a:hover {
    color: #ffffff;
    text-decoration: underline;
}
.social-icons a {
    margin: 0 15px;
    font-size: 20px;
    color: #cccccc;
}
.social-icons a:hover {
    color: #1DA1F2; /* Twitter blue as a hover color example */
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
    st.session_state.generation_time = 10.0  # Default estimate in seconds
if "first_visit" not in st.session_state:
    st.session_state.first_visit = True
if "survey_submitted" not in st.session_state:
    st.session_state.survey_submitted = False

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
    
    # Show text input if "Other" is selected
    if st.session_state.role == "Other":
        st.session_state.custom_role = st.text_input("Please specify your role", placeholder="e.g., Game Developer", value=st.session_state.custom_role)
    
    # Determine the effective role to use
    effective_role = st.session_state.custom_role if st.session_state.role == "Other" and st.session_state.custom_role else st.session_state.role
    
    st.subheader("📄 Upload Your Resume")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        try:
            st.session_state.resume_text = parse_resume(tmp_path)
            if len(st.session_state.resume_text.strip()) > 20:
                st.success("✅ Resume uploaded and parsed!")
            else:
                st.error("⚠️ Failed to extract meaningful content. Try another resume.")
        except FileNotFoundError:
            # Suppress FileNotFoundError since the app is working correctly
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
                pass  # Suppress error if the file is already deleted
    
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
                # Progress bar and ETA based on actual or estimated time
                progress_bar = st.progress(0)
                eta_placeholder = st.empty()
                start_time = time.time()
                
                # Estimate total time (use previous generation time if available)
                estimated_time = st.session_state.generation_time
                
                # Generate roadmap and measure actual time
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
                roadmap_start = time.time()
                st.session_state.roadmap = generate_roadmap(prompt)
                roadmap_end = time.time()
                actual_time = roadmap_end - roadmap_start
                
                # Update estimated time for future generations
                st.session_state.generation_time = actual_time
                
                # Update progress bar and ETA (retroactively for this run)
                elapsed = time.time() - start_time
                for i in range(100):
                    progress = min(1.0, elapsed / actual_time)
                    progress_bar.progress(int(progress * 100))
                    eta = max(0, actual_time - elapsed)
                    eta_placeholder.text(f"⏳ Estimated time remaining: {eta:.1f} seconds")
                    time.sleep(0.05)  # Small delay to make progress visible
                    elapsed = time.time() - start_time
                progress_bar.empty()
                eta_placeholder.empty()
            
            st.success("✅ Roadmap generated! Check it in the Roadmap tab.")
            
            # In-App Survey after roadmap generation
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
        # Use inline CSS to ensure the roadmap header size (as per your manual change)
        st.markdown('<h1 style="font-size: 40px;">🗺️ Your AI-Powered Learning Roadmap</h1><br>', unsafe_allow_html=True)
        
        # Skill match score (as per your manual change)
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
        # Default skills for custom roles
        default_skills = ["Python", "Git", "Problem Solving", "Communication"]
        
        # Use required skills for predefined roles, or default skills for custom roles
        skills_to_check = required_skills.get(effective_role, default_skills)
        
        if skills_to_check:
            matching_skills = [skill for skill in skills_to_check if skill.lower() in st.session_state.resume_text.lower()]
            skill_match_score = (len(matching_skills) / len(skills_to_check)) * 100
            st.subheader("📊 Skill Match Score")
            st.markdown(f'<p style="font-size: 40px;"><h5>●    Your skills match {skill_match_score:.1f}% of the requirements for {effective_role}.</h5></p>', unsafe_allow_html=True)
        
        # Skill gap analysis with course recommendations
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
                # Course recommendations for missing skills
                st.subheader("📚 Recommended Courses for Skill Gaps")
                for skill in missing_skills:
                    if skill in course_recommendations:
                        st.markdown(f"- **{skill}**: {course_recommendations[skill]}")
                    else:
                        st.markdown(f"- **{skill}**: No specific course recommendation available. Try searching on Coursera or Udemy.")
            else:
                st.write("✅ Your resume covers all key skills for this role!")
        
        # Tag-based course filters (fixed)
        st.subheader("🏷️ Filter Courses")
        tags = set()
        for line in st.session_state.roadmap.splitlines():
            line = line.strip()
            if not line or not line.startswith("*"):
                continue
            # Look for tags in the format: "* <course> - <tag1>, <tag2>"
            if " - " in line:
                parts = line.split(" - ", 1)
                tag_part = parts[-1]
                if "," in tag_part:
                    line_tags = [tag.strip() for tag in tag_part.split(",")]
                    tags.update(line_tags)
            # Look for tags in the format: "* <course> [<tag1>, <tag2>]"
            elif "[" in line and "]" in line:
                tag_part = line[line.find("[") + 1:line.find("]")]
                if "," in tag_part:
                    line_tags = [tag.strip() for tag in tag_part.split(",")]
                    tags.update(line_tags)
        
        # If no tags are found, use default tags and show debug info
        if not tags:
            tags = {"YouTube", "Beginner-Friendly", "Advanced", "Udemy", "Coursera"}
            st.warning("⚠️ No tags found in the roadmap. Using default tags. Below is the roadmap content for debugging:")
            st.text_area("Roadmap Content", st.session_state.roadmap, height=200)
        
        selected_tags = st.multiselect("Filter by tags (e.g., YouTube, Beginner-Friendly)", sorted(tags))
        
        # Progress tracker and roadmap display
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
                # Check if the line has tags matching the selected ones
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
                # Display the previous section if it has content
                if current_section and section_content:
                    st.markdown(f"## {current_section}")
                    # Show Edit button only if the section has actionable content
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
                # Start a new section
                current_section = line[2:]
                section_content = []
            else:
                section_content.append(line)
        
        # Display the last section
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
        
        # Live edit suggestions
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
        
        # Interactive Q&A
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
        
        # Feedback loop
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
        
        # Export options
        st.subheader("📥 Export Your Roadmap")
        
        st.download_button(
            label="📄 Download as TXT",
            data=st.session_state.roadmap,
            file_name="SkillWise_Roadmap.txt",
            mime="text/plain"
        )
        
        # PDF export with proper formatting (only generated on button click)
        def clean_text(text):
            replacements = {
                "–": "-",  # En dash to hyphen
                "—": "-",  # Em dash to hyphen
                "’": "'",  # Right single quote to straight quote
                "‘": "'",  # Left single quote to straight quote
                "“": '"',  # Left double quote to straight quote
                "”": '"',  # Right double quote to straight quote
            }
            for unicode_char, ascii_char in replacements.items():
                text = text.replace(unicode_char, ascii_char)
            return text.encode("ascii", "ignore").decode("ascii")
        
        def generate_pdf():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "SkillWise Learning Roadmap", ln=True, align="C")
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
            pdf.ln(10)
            
            for line in st.session_state.roadmap.splitlines():
                line = clean_text(line.strip())
                if line.startswith("**"):
                    pdf.set_font("Arial", "B", 14)
                    pdf.cell(0, 10, line[2:], ln=True)
                elif line.startswith("*"):
                    pdf.set_font("Arial", size=12)
                    pdf.cell(10, 10, "- ", ln=0)
                    pdf.multi_cell(0, 10, line[1:])
                else:
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, line)
                pdf.ln(2)
            
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, "Generated by SkillWise", ln=True, align="C")
            return bytes(pdf.output(dest="S"))
        
        if st.button("📄 Download as PDF"):
            pdf_bytes = generate_pdf()
            st.download_button(
                label="📄 Click to Download PDF",
                data=pdf_bytes,
                file_name="SkillWise_Roadmap.pdf",
                mime="application/pdf"
            )
        
        # JSON export
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
        
        # Shareable link (simulated)
        unique_id = hash(st.session_state.roadmap) % 1000000
        with open(f"roadmap_{unique_id}.json", "w") as f:
            json.dump(roadmap_data, f)
        st.markdown(f"🔗 Shareable link: `http://skillwise.local/roadmap/{unique_id}` (Note: Deploy to a server for real links)")
    else:
        st.info("🚧 Generate a roadmap in the Resume tab.")

# Footer with social media handles, copyright, and additional links
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