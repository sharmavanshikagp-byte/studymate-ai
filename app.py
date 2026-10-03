import streamlit as st
from pypdf import PdfReader
import fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import json
import re
from groq import Groq
from datetime import datetime


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="StudyMate AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "llama-3.1-8b-instant"
MAX_TEXT_LENGTH = 18000


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "extracted_text": "",
    "current_file_id": None,
    "used_ocr": False,
    "summary": "",
    "questions": "",
    "chat_history": [],
    "quiz": None,
    "quiz_answers": {},
    "quiz_submitted": False,
    "quiz_score": 0,
    "quiz_history": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# CUSTOM HTML RENDERER
# ============================================================

def render_html(html):
    st.html(html)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       MAIN BACKGROUND
       ======================================================== */

    .stApp {
        background:
            radial-gradient(
                circle at 10% 10%,
                rgba(255, 220, 238, 0.55),
                transparent 28%
            ),
            radial-gradient(
                circle at 90% 10%,
                rgba(222, 215, 255, 0.55),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #fffaff 0%,
                #f8f6ff 50%,
                #fffafc 100%
            );
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #fff4fa 0%,
                #f7f2ff 100%
            );

        border-right: 1px solid #eee4f3;
    }


    /* ========================================================
       MAIN CONTENT
       ======================================================== */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }


    /* ========================================================
       HERO
       ======================================================== */

    .hero {
        background:
            linear-gradient(
                135deg,
                #ffffff,
                #fff6fb 55%,
                #f5f1ff
            );

        border: 1px solid #eadff0;
        border-radius: 28px;

        padding: 38px 35px;
        margin-bottom: 28px;

        box-shadow:
            0 10px 35px rgba(80, 55, 90, 0.08);

        text-align: center;
    }

    .hero-title {
        font-size: 48px;
        font-weight: 800;
        color: #3c3150;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        font-size: 19px;
        color: #75697f;
        margin-bottom: 18px;
    }

    .hero-badge {
        display: inline-block;

        padding: 8px 18px;

        border-radius: 30px;

        background: #f2e8ff;
        color: #76539a;

        font-size: 14px;
        font-weight: 600;
    }


    /* ========================================================
       SECTION TITLE
       ======================================================== */

    .section-title {
        font-size: 27px;
        font-weight: 750;

        color: #40334f;

        margin-top: 10px;
        margin-bottom: 16px;
    }


    /* ========================================================
       FEATURE CARDS
       ======================================================== */

    .feature-card {
        background: rgba(255, 255, 255, 0.92);

        border: 1px solid #eadff0;
        border-radius: 20px;

        padding: 23px;

        min-height: 145px;

        box-shadow:
            0 7px 25px rgba(80, 55, 90, 0.06);
    }

    .feature-icon {
        font-size: 29px;
        margin-bottom: 8px;
    }

    .feature-title {
        font-size: 18px;
        font-weight: 750;

        color: #463653;

        margin-bottom: 7px;
    }

    .feature-text {
        color: #75697f;

        font-size: 14px;

        line-height: 1.55;
    }


    /* ========================================================
       UPLOAD AREA
       ======================================================== */

    .upload-card {
        background: rgba(255, 255, 255, 0.9);

        border: 1px solid #eadff0;
        border-radius: 22px;

        padding: 24px;

        margin-top: 22px;

        box-shadow:
            0 7px 25px rgba(80, 55, 90, 0.05);
    }


    /* ========================================================
       STATUS CARDS
       ======================================================== */

    .status-card {
        background: #ffffff;

        border: 1px solid #eadff0;
        border-radius: 17px;

        padding: 18px;

        margin-top: 15px;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        border-radius: 12px;

        border: 1px solid #ded1e9;

        font-weight: 650;

        min-height: 42px;

        transition: 0.2s ease;
    }

    .stButton > button:hover {
        border-color: #b999d0;

        transform: translateY(-1px);

        box-shadow:
            0 5px 15px rgba(100, 70, 120, 0.10);
    }


    /* ========================================================
       TABS
       ======================================================== */

    button[data-baseweb="tab"] {
        font-weight: 650;
    }


    /* ========================================================
       TEXT AREAS
       ======================================================== */

    textarea {
        border-radius: 12px !important;
    }


    /* ========================================================
       INPUTS
       ======================================================== */

    input {
        border-radius: 12px !important;
    }


    /* ========================================================
       EXPANDERS
       ======================================================== */

    div[data-testid="stExpander"] {
        border: 1px solid #eadff0;

        border-radius: 15px;

        background: rgba(
            255,
            255,
            255,
            0.75
        );
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    .footer {
        text-align: center;

        color: #8a7d94;

        padding: 20px;

        font-size: 13px;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    .sidebar-title {
        font-size: 25px;

        font-weight: 800;

        color: #493858;

        margin-bottom: 4px;
    }

    .sidebar-subtitle {
        color: #7c7085;

        font-size: 13px;

        line-height: 1.5;
    }


    /* ========================================================
       AI BADGE
       ======================================================== */

    .ai-badge {
        background: #f3eaff;

        border: 1px solid #e2d2f2;

        color: #76529a;

        border-radius: 12px;

        padding: 10px 13px;

        font-weight: 650;

        text-align: center;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    render_html(
        """
        <div class="sidebar-title">
            🌸 StudyMate AI
        </div>
        """
    )

    render_html(
        """
        <div class="sidebar-subtitle">
            Your personal AI-powered study companion.
        </div>
        """
    )

    st.divider()

    st.markdown("### ✨ Features")

    st.write("📄  PDF Notes")
    st.write("✍️  OCR Support")
    st.write("🧠  Smart Summary")
    st.write("💬  Ask My Notes")
    st.write("❓  Exam Questions")
    st.write("🎯  Quiz Mode")
    st.write("📊  Quiz History")

    st.divider()

    st.markdown("### 🤖 AI Model")

    render_html(
        f"""
        <div class="ai-badge">
            {MODEL_NAME}
        </div>
        """
    )

    st.caption(
        "Runs locally through Ollama."
    )

    st.divider()

    st.markdown("### 💡 StudyMate Tip")

    st.caption(
        "Upload clear lecture notes or PDFs "
        "for better summaries and questions."
    )


# ============================================================
# HERO HEADER
# ============================================================

render_html(
    """
    <div class="hero">

        <div class="hero-title">
            📚 StudyMate AI
        </div>

        <div class="hero-subtitle">
            Your smart little study companion ✨
        </div>

        <div class="hero-badge">
            Learn smarter • Revise faster • Prepare better
        </div>

    </div>
    """
)


# ============================================================
# FEATURE SECTION
# ============================================================

render_html(
    """
    <div class="section-title">
        ✨ Everything you need to study
    </div>
    """
)

col1, col2, col3 = st.columns(3)


with col1:

    render_html(
        """
        <div class="feature-card">

            <div class="feature-icon">
                📚
            </div>

            <div class="feature-title">
                Smart Summary
            </div>

            <div class="feature-text">
                Convert lengthy study material into
                simple, structured and exam-ready notes.
            </div>

        </div>
        """
    )


with col2:

    render_html(
        """
        <div class="feature-card">

            <div class="feature-icon">
                💬
            </div>

            <div class="feature-title">
                Ask My Notes
            </div>

            <div class="feature-text">
                Ask questions directly from your
                uploaded notes and get clear answers.
            </div>

        </div>
        """
    )


with col3:

    render_html(
        """
        <div class="feature-card">

            <div class="feature-icon">
                🎯
            </div>

            <div class="feature-title">
                Quiz Yourself
            </div>

            <div class="feature-text">
                Generate MCQs from your material
                and test your preparation instantly.
            </div>

        </div>
        """
    )


# ============================================================
# OLLAMA AI FUNCTION
# ============================================================

def ask_ai(prompt):

    try:

        client = Groq(
            api_key=st.secrets["GROQ_API_KEY"]
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=4096
        )

        content = response.choices[0].message.content

        if not content:
            st.error("⚠️ Groq did not return an answer.")
            return ""

        content = str(content).strip()

        return content

    except Exception as e:

        st.error(
            f"❌ AI generation failed: {e}"
        )

        st.info(
            "Please check your Groq API key and Streamlit Secrets."
        )

        return ""


# ============================================================
# PREPARE NOTES
# ============================================================

def prepare_notes(text):

    if not text:

        return ""

    text = text.strip()

    if len(text) <= MAX_TEXT_LENGTH:

        return text

    half = MAX_TEXT_LENGTH // 2

    return (
        text[:half]
        + "\n\n[...middle of document omitted...]\n\n"
        + text[-half:]
    )


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    pdf_bytes = uploaded_file.getvalue()

    normal_text = ""

    # --------------------------------------------------------
    # NORMAL PDF TEXT EXTRACTION
    # --------------------------------------------------------

    try:

        reader = PdfReader(
            io.BytesIO(pdf_bytes)
        )

        for page in reader.pages:

            text = page.extract_text()

            if text:

                normal_text += (
                    text + "\n"
                )

    except Exception:

        normal_text = ""

    normal_text = normal_text.strip()

    # If enough text was extracted,
    # OCR is unnecessary.

    if len(normal_text) >= 100:

        return normal_text, False


    # --------------------------------------------------------
    # OCR FALLBACK
    # --------------------------------------------------------

    ocr_text = ""

    try:

        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        for page in document:

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            # Grayscale
            image = ImageOps.grayscale(
                image
            )

            # Improve contrast
            image = ImageEnhance.Contrast(
                image
            ).enhance(1.5)

            # Sharpen
            image = image.filter(
                ImageFilter.SHARPEN
            )

            # OCR
            text = pytesseract.image_to_string(
                image
            )

            if text:

                ocr_text += (
                    text + "\n"
                )

        document.close()

    except Exception as e:

        st.warning(
            f"OCR could not be completed: {e}"
        )

    return (
        ocr_text.strip(),
        True
    )


# ============================================================
# UPLOAD SECTION
# ============================================================

render_html(
    """
    <div class="section-title">
        📄 Upload your study material
    </div>
    """
)

uploaded_file = st.file_uploader(
    "Choose a PDF containing your study material",
    type=["pdf"],
    label_visibility="collapsed"
)


# ============================================================
# PROCESS UPLOADED FILE
# ============================================================

if uploaded_file is not None:

    file_id = (
        uploaded_file.name,
        uploaded_file.size
    )

    if st.session_state.current_file_id != file_id:

        with st.spinner(
            "📖 Reading your notes..."
        ):

            text, used_ocr = extract_pdf_text(
                uploaded_file
            )

        st.session_state.current_file_id = file_id

        st.session_state.extracted_text = text

        st.session_state.used_ocr = used_ocr

        # Reset old study results

        st.session_state.summary = ""

        st.session_state.questions = ""

        st.session_state.chat_history = []

        st.session_state.quiz = None

        st.session_state.quiz_answers = {}

        st.session_state.quiz_submitted = False

        st.session_state.quiz_score = 0

    notes = st.session_state.extracted_text

    if notes:

        st.success(
            f"✅ {uploaded_file.name} loaded successfully!"
        )

        if st.session_state.used_ocr:

            st.info(
                "✍️ OCR was used because the PDF "
                "appears to contain scanned pages."
            )

        with st.expander(
            "👀 Preview extracted notes"
        ):

            st.text_area(
                "Extracted text",
                notes[:6000],
                height=300
            )

    else:

        st.error(
            "❌ No readable text could be extracted."
        )


# ============================================================
# STUDY TOOLS
# ============================================================

if st.session_state.extracted_text:

    notes = prepare_notes(
        st.session_state.extracted_text
    )

    st.divider()

    render_html(
        """
        <div class="section-title">
            🧠 Study Tools
        </div>
        """
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📚 Smart Summary",
            "💬 Ask My Notes",
            "❓ Exam Questions",
            "🎯 Quiz Mode",
            "📊 Quiz History"
        ]
    )


    # ========================================================
    # SMART SUMMARY
    # ========================================================

    with tab1:

        st.markdown(
            "### 📚 Smart Summary"
        )

        st.write(
            "Turn your lengthy notes into "
            "simple, exam-ready revision material."
        )

        summary_style = st.selectbox(
            "Choose summary style",
            [
                "Exam-ready notes",
                "Short revision notes",
                "Detailed explanation",
                "Key points only"
            ],
            key="summary_style"
        )

        if st.button(
            "✨ Generate Smart Summary",
            key="summary_button",
            use_container_width=True
        ):

            prompt = f"""
You are StudyMate AI, a helpful university
study assistant.

Create {summary_style.lower()} from the
study material below.

IMPORTANT RULES:

- Use ONLY information from the supplied notes.
- Do NOT invent facts.
- Use simple student-friendly language.
- Use clear headings.
- Use bullet points where appropriate.
- Include important definitions.
- Include important concepts.
- Include formulas if they appear in the notes.
- Include examples if they appear in the notes.
- Make the result useful for university exams.
- Do NOT show your reasoning.
- Do NOT show a thinking process.
- Do NOT explain how you created the summary.
- Do NOT write a plan before the summary.
- Start directly with the final study notes.
- Give ONLY the final summary.

STUDY MATERIAL:

{notes}
"""

            with st.spinner(
                "🧠 Creating your summary..."
            ):

                result = ask_ai(
                    prompt
                )

            if result:

                st.session_state.summary = result

                st.success(
                    "✅ Summary generated successfully!"
                )

            else:

                st.session_state.summary = ""

        if st.session_state.summary:

            st.markdown(
                "### ✨ Your Summary"
            )

            st.markdown(
                st.session_state.summary
            )

            st.download_button(
                "📥 Download Summary",
                st.session_state.summary,
                "StudyMate_Summary.txt",
                "text/plain",
                key="download_summary",
                use_container_width=True
            )


    # ========================================================
    # ASK MY NOTES
    # ========================================================

    with tab2:

        st.markdown(
            "### 💬 Ask My Notes"
        )

        st.write(
            "Ask anything related to your uploaded notes."
        )

        question = st.text_input(
            "Your question",
            placeholder=(
                "Example: Explain normalization in DBMS."
            ),
            key="notes_question"
        )

        if st.button(
            "💬 Ask StudyMate",
            key="ask_button",
            use_container_width=True
        ):

            if question.strip():

                prompt = f"""
You are StudyMate AI.

Answer the student's question using
the uploaded study material.

RULES:

- Use the supplied notes as your main source.
- Use simple and clear language.
- Give a direct answer.
- Do not show reasoning.
- Do not show a thinking process.
- If the answer is not present in the notes,
  clearly say that it is not present.

QUESTION:

{question}

STUDY MATERIAL:

{notes}
"""

                with st.spinner(
                    "🤔 Finding the answer..."
                ):

                    answer = ask_ai(
                        prompt
                    )

                if answer:

                    st.session_state.chat_history.append(
                        {
                            "question": question,
                            "answer": answer
                        }
                    )

            else:

                st.warning(
                    "Please enter a question."
                )

        if st.session_state.chat_history:

            st.markdown(
                "### 💡 Previous Questions"
            )

            for item in reversed(
                st.session_state.chat_history
            ):

                with st.expander(
                    f"❓ {item['question']}"
                ):

                    st.write(
                        item["answer"]
                    )


    # ========================================================
    # EXAM QUESTIONS
    # ========================================================

    with tab3:

        st.markdown(
            "### ❓ Exam Question Generator"
        )

        st.write(
            "Generate important university-style "
            "questions from your notes."
        )

        question_type = st.selectbox(
            "Question type",
            [
                "Important theory questions",
                "Short-answer questions",
                "Long-answer questions",
                "Mixed exam questions"
            ],
            key="question_type"
        )

        number_questions = st.slider(
            "Number of questions",
            5,
            20,
            10,
            key="number_questions"
        )

        if st.button(
            "📝 Generate Exam Questions",
            key="generate_questions",
            use_container_width=True
        ):

            prompt = f"""
You are a university exam preparation assistant.

Generate exactly {number_questions}
{question_type.lower()} from the study material.

RULES:

- Use only the supplied notes.
- Do not invent information.
- Avoid duplicate questions.
- Cover different important concepts.
- Number every question.
- Do not show reasoning.
- Give only the final questions.

STUDY MATERIAL:

{notes}
"""

            with st.spinner(
                "📝 Preparing questions..."
            ):

                result = ask_ai(
                    prompt
                )

            if result:

                st.session_state.questions = result

                st.success(
                    "✅ Questions generated successfully!"
                )

        if st.session_state.questions:

            st.markdown(
                "### 📋 Generated Questions"
            )

            st.markdown(
                st.session_state.questions
            )

            st.download_button(
                "📥 Download Questions",
                st.session_state.questions,
                "StudyMate_Exam_Questions.txt",
                "text/plain",
                key="download_questions",
                use_container_width=True
            )


    # ========================================================
    # QUIZ MODE
    # ========================================================

    with tab4:

        st.markdown(
            "### 🎯 Quiz Mode"
        )

        st.write(
            "Test your understanding with "
            "AI-generated multiple-choice questions."
        )

        quiz_count = st.slider(
            "Number of MCQs",
            5,
            15,
            5,
            key="quiz_count"
        )

        if st.button(
            "🎯 Generate New Quiz",
            key="generate_quiz",
            use_container_width=True
        ):

            prompt = f"""
Create exactly {quiz_count} multiple-choice
questions from the study material.

Return ONLY valid JSON.

Use exactly this format:

[
  {{
    "question": "Question",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "Option A",
    "explanation": "Short explanation"
  }}
]

RULES:

- Exactly four options per question.
- Only one correct answer.
- Questions must come from the notes.
- Do not invent information.
- Do not include markdown.
- Do not include ```json.
- Do not show reasoning.
- Return only the JSON array.

STUDY MATERIAL:

{notes}
"""

            with st.spinner(
                "🎯 Creating your quiz..."
            ):

                raw_quiz = ask_ai(
                    prompt
                )

            if raw_quiz:

                try:

                    cleaned = raw_quiz.strip()

                    # Remove markdown fences

                    cleaned = re.sub(
                        r"```json",
                        "",
                        cleaned,
                        flags=re.IGNORECASE
                    )

                    cleaned = cleaned.replace(
                        "```",
                        ""
                    )

                    # Find JSON array

                    start = cleaned.find("[")

                    end = cleaned.rfind("]")

                    if start != -1 and end != -1:

                        cleaned = cleaned[
                            start:end + 1
                        ]

                    quiz_data = json.loads(
                        cleaned
                    )

                    if not isinstance(
                        quiz_data,
                        list
                    ):

                        raise ValueError(
                            "Invalid quiz format."
                        )

                    # Validate questions

                    for q in quiz_data:

                        if not isinstance(
                            q,
                            dict
                        ):

                            raise ValueError(
                                "Invalid question format."
                            )

                        if not q.get(
                            "question"
                        ):

                            raise ValueError(
                                "A question is missing."
                            )

                        options = q.get(
                            "options",
                            []
                        )

                        if len(options) != 4:

                            raise ValueError(
                                "Each question must have exactly four options."
                            )

                        if q.get(
                            "answer"
                        ) not in options:

                            raise ValueError(
                                "Correct answer is not one of the options."
                            )

                    st.session_state.quiz = quiz_data

                    st.session_state.quiz_answers = {}

                    st.session_state.quiz_submitted = False

                    st.session_state.quiz_score = 0

                    st.success(
                        "✅ Quiz generated successfully!"
                    )

                except Exception as e:

                    st.error(
                        "❌ Could not process the quiz response."
                    )

                    st.write(
                        str(e)
                    )

                    with st.expander(
                        "View AI response"
                    ):

                        st.code(
                            raw_quiz
                        )

        quiz = st.session_state.quiz

        if quiz:

            if not st.session_state.quiz_submitted:

                for i, q in enumerate(
                    quiz
                ):

                    st.markdown(
                        f"**Q{i + 1}. "
                        f"{q.get('question', '')}**"
                    )

                    options = q.get(
                        "options",
                        []
                    )

                    selected = st.radio(
                        "Choose your answer:",
                        options,
                        index=None,
                        key=f"quiz_option_{i}"
                    )

                    st.session_state.quiz_answers[
                        str(i)
                    ] = selected

                st.write("")

                if st.button(
                    "✅ Submit Quiz",
                    key="submit_quiz",
                    use_container_width=True
                ):

                    score = 0

                    for i, q in enumerate(
                        quiz
                    ):

                        selected = (
                            st.session_state
                            .quiz_answers
                            .get(str(i))
                        )

                        correct = q.get(
                            "answer",
                            ""
                        )

                        if selected == correct:

                            score += 1

                    st.session_state.quiz_score = score

                    st.session_state.quiz_submitted = True

                    st.session_state.quiz_history.append(
                        {
                            "date": datetime.now().strftime(
                                "%d %b %Y, %I:%M %p"
                            ),
                            "score": score,
                            "total": len(quiz)
                        }
                    )

                    st.rerun()

            else:

                score = st.session_state.quiz_score

                total = len(quiz)

                percentage = (
                    round(
                        score / total * 100
                    )
                    if total
                    else 0
                )

                st.success(
                    f"🎉 You scored {score}/{total} "
                    f"({percentage}%)"
                )

                st.markdown(
                    "### 📖 Answer Review"
                )

                for i, q in enumerate(
                    quiz
                ):

                    selected = (
                        st.session_state
                        .quiz_answers
                        .get(str(i))
                    )

                    correct = q.get(
                        "answer",
                        ""
                    )

                    explanation = q.get(
                        "explanation",
                        ""
                    )

                    if selected == correct:

                        st.success(
                            f"Q{i + 1}: Correct ✓\n\n"
                            f"Your answer: {selected}\n\n"
                            f"Explanation: {explanation}"
                        )

                    else:

                        st.error(
                            f"Q{i + 1}: Incorrect ✗\n\n"
                            f"Your answer: "
                            f"{selected or 'Not answered'}\n\n"
                            f"Correct answer: {correct}\n\n"
                            f"Explanation: {explanation}"
                        )

                if st.button(
                    "🔄 Try Another Quiz",
                    key="another_quiz",
                    use_container_width=True
                ):

                    st.session_state.quiz = None

                    st.session_state.quiz_answers = {}

                    st.session_state.quiz_submitted = False

                    st.session_state.quiz_score = 0

                    st.rerun()


    # ========================================================
    # QUIZ HISTORY
    # ========================================================

    with tab5:

        st.markdown(
            "### 📊 Quiz History"
        )

        if st.session_state.quiz_history:

            for item in reversed(
                st.session_state.quiz_history
            ):

                percentage = round(
                    item["score"]
                    /
                    item["total"]
                    *
                    100
                )

                st.write(
                    f"📅 **{item['date']}**  |  "
                    f"🎯 **{item['score']}/{item['total']}**  |  "
                    f"**{percentage}%**"
                )

                st.divider()

        else:

            st.info(
                "No quiz attempts yet. "
                "Complete your first quiz and "
                "your result will appear here."
            )


# ============================================================
# NO PDF SCREEN
# ============================================================

else:

    st.info(
        "🦉 Upload a PDF above to start using StudyMate AI."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

render_html(
    """
    <div class="footer">
        📚 StudyMate AI &nbsp;•&nbsp;
        Learn smarter, revise faster ✨
    </div>
    """
)
