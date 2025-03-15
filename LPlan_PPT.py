import streamlit as st
import os
import openai
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches
import tempfile
import re

# Streamlit app settings
st.set_page_config(page_title="AI Lesson Plan Generator", page_icon="📚")

st.title("AI Lesson Plan Generator")
st.markdown("Generate custom lesson plans using AI models")

# Initialize session state variables
if 'lesson_plan' not in st.session_state:
    st.session_state.lesson_plan = ""
if 'create_ppt' not in st.session_state:
    st.session_state.create_ppt = False
if 'ppt_generated' not in st.session_state:
    st.session_state.ppt_generated = False
if 'ppt_path' not in st.session_state:
    st.session_state.ppt_path = None

# API Selection
ai_choice = st.radio(
    "Choose which AI model to use:",
    ["OpenAI (GPT-4)", "Google Gemini"]
)

# API Key input
api_key = st.text_input("Enter your API Key:", type="password")

# Model selection
if ai_choice == "OpenAI (GPT-4)":
    model_choice = st.selectbox("Select OpenAI model:", ["gpt-4", "gpt-3.5-turbo"])
else:
    model_choice = "gemini-1.5-pro"

# Board selection
board = st.radio("Choose the educational board:", ["CBSE", "IB"])
board_name = "CBSE" if "CBSE" in board else "IB"

# Input fields
col1, col2 = st.columns(2)
with col1:
    grade = st.text_input("Enter the Grade Level:")
    subject = st.text_input("Enter the Subject:")
with col2:
    concept = st.text_input("Enter the Concept:")


# Function to generate lesson plan using OpenAI API
def generate_lesson_plan_openai(grade, subject, concept, board, api_key, model):
    """Generates a lesson plan using OpenAI's latest API version."""
    try:
        client = openai.OpenAI(api_key=api_key)
        prompt = f"""Create a detailed lesson plan for {subject} on {concept} for Grade {grade} following the {board} curriculum.

        Structure your response with clear headings for each section:
        1. Learning Objectives
        2. Key Concepts
        3. Required Materials
        4. Introduction Activity
        5. Main Teaching Points
        6. Student Activities
        7. Assessment Methods
        8. Homework/Extension Activities

        Use proper Markdown formatting with headings (##) for each section.
        """
        messages = [
            {"role": "system", "content": f"You are an expert educator specializing in the {board} curriculum."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"OpenAI Error: {str(e)}"


# Function to generate lesson plan using Google Gemini API
def generate_lesson_plan_gemini(grade, subject, concept, board, api_key):
    """Generates a lesson plan using Google's Gemini model."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        prompt = f"""
        You are an expert educator specializing in the {board} curriculum.
        Create a detailed lesson plan for {subject} on {concept} for Grade {grade}.
        
        Structure your response with clear headings for each section:
        1. Learning Objectives
        2. Key Concepts
        3. Required Materials
        4. Introduction Activity
        5. Main Teaching Points
        6. Student Activities
        7. Assessment Methods
        8. Homework/Extension Activities
        
        Use proper Markdown formatting with headings (##) for each section.
        """
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Gemini Error: {str(e)}"


# Function to create a PowerPoint presentation
def create_ppt_from_lesson_plan(lesson_plan, title, grade, subject, board):
    """Creates a PowerPoint from the lesson plan."""
    prs = Presentation()
    title_slide_layout = prs.slide_layouts[0]
    content_slide_layout = prs.slide_layouts[1]

    slide = prs.slides.add_slide(title_slide_layout)
    slide.shapes.title.text = f"{subject}: {title}"
    slide.placeholders[1].text = f"Grade {grade} - {board} Curriculum"

    sections = re.split(r'(?m)^##\s+(.*?)$', lesson_plan)

    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            heading = sections[i].strip()
            content = sections[i + 1].strip()
            slide = prs.slides.add_slide(content_slide_layout)
            slide.shapes.title.text = heading

            text_frame = slide.placeholders[1].text_frame
            text_frame.text = ""
            lines = content.split("\n")
            for line in lines:
                if not line.strip():
                    continue
                paragraph = text_frame.add_paragraph()
                paragraph.text = line.strip()
                paragraph.level = 1

    slide = prs.slides.add_slide(content_slide_layout)
    slide.shapes.title.text = "Thank You"
    slide.placeholders[1].text = "Any questions?"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pptx")
    prs.save(temp_file.name)
    return temp_file.name


# Generate button
if st.button("Generate Lesson Plan"):
    if not grade or not subject or not concept:
        st.error("Please fill in all fields (Grade, Subject, and Concept).")
    elif not api_key:
        st.error("Please enter your API key.")
    else:
        with st.spinner("Generating lesson plan..."):
            if ai_choice == "OpenAI (GPT-4)":
                st.session_state.lesson_plan = generate_lesson_plan_openai(
                    grade, subject, concept, board_name, api_key, model_choice
                )
            else:
                st.session_state.lesson_plan = generate_lesson_plan_gemini(
                    grade, subject, concept, board_name, api_key
                )

# Display the generated lesson plan
if st.session_state.lesson_plan:
    st.subheader("Generated Lesson Plan")
    st.markdown(st.session_state.lesson_plan)

    filename = f"{board_name}_{subject}_{concept}_Grade{grade}.txt"
    st.download_button("Download Lesson Plan", data=st.session_state.lesson_plan, file_name=filename, mime="text/plain")

    if not st.session_state.create_ppt and not st.session_state.ppt_generated:
        if st.button("Create PowerPoint Presentation"):
            st.session_state.create_ppt = True

    if st.session_state.create_ppt and not st.session_state.ppt_generated:
        with st.spinner("Creating PowerPoint presentation..."):
            try:
                ppt_path = create_ppt_from_lesson_plan(
                    st.session_state.lesson_plan, concept, grade, subject, board_name
                )
                st.session_state.ppt_path = ppt_path
                st.session_state.ppt_generated = True
                st.session_state.create_ppt = False
            except Exception as e:
                st.error(f"Error creating PowerPoint: {str(e)}")

    if st.session_state.ppt_generated and st.session_state.ppt_path:
        with open(st.session_state.ppt_path, "rb") as ppt_file:
            ppt_bytes = ppt_file.read()

        st.download_button("Download PowerPoint", data=ppt_bytes, file_name=f"{board_name}_{subject}_{concept}_Grade{grade}.pptx",
                           mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        st.success("PowerPoint created successfully!")
