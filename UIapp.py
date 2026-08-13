import streamlit as st
import os
import shutil
import subprocess
import sys
import gc
import time
import uuid

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

# =========================================================
# CONFIG
# =========================================================

load_dotenv()

st.set_page_config(
    page_title="Book RAG Assistant",
    page_icon="📚",
    layout="wide"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #777;
        margin-bottom: 30px;
    }

    .book-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# TITLE
# =========================================================

st.markdown(
    '<div class="main-title">📚 Book RAG Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload a PDF and ask questions about its contents.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "book_processed" not in st.session_state:
    st.session_state["book_processed"] = False

if "book_name" not in st.session_state:
    st.session_state["book_name"] = None

if "messages" not in st.session_state:
    st.session_state["messages"] = []


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📖 About")

    st.write(
        """
        This application uses RAG to answer questions
        from your uploaded book.

        **Pipeline**

        PDF
        ↓
        Text chunks
        ↓
        HuggingFace embeddings
        ↓
        ChromaDB
        ↓
        Retriever
        ↓
        Groq LLM
        """
    )

    st.divider()

    st.subheader("⚙️ Technologies")

    st.write("• Streamlit")
    st.write("• LangChain")
    st.write("• ChromaDB")
    st.write("• HuggingFace")
    st.write("• Groq")

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state["messages"] = []

        st.rerun()


# =========================================================
# UPLOAD
# =========================================================

st.subheader("📤 Upload Your Book")

uploaded_file = st.file_uploader(
    "Choose a PDF book",
    type=["pdf"]
)


if uploaded_file is not None:

    st.markdown(
        f"""
        <div class="book-card">
        📕 <b>Selected Book:</b> {uploaded_file.name}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🚀 Process Book",
        type="primary",
        use_container_width=True
    ):

        # =================================================
        # SAVE PDF FIRST
        # =================================================

        os.makedirs(
            "document_loaders",
            exist_ok=True
        )

        pdf_path = (
            "document_loaders/deeplearning.pdf"
        )

        with open(
            pdf_path,
            "wb"
        ) as f:

            f.write(
                uploaded_file.getbuffer()
            )


        # =================================================
        # DELETE OLD DATABASE
        # =================================================

        if os.path.exists("chroma_db"):

            try:

                # Try normal deletion first
                shutil.rmtree("chroma_db")

                st.success(
                    "🗑️ Old ChromaDB deleted."
                )

            except PermissionError:

                st.warning(
                    "⚠️ Old ChromaDB is currently locked."
                )

                st.info(
                    "The application will try to release "
                    "the old database before replacing it."
                )

                # -------------------------------------------------
                # IMPORTANT:
                # Don't keep trying to delete a locked database.
                # Instead, rename it and create a fresh database.
                # -------------------------------------------------

                old_name = (
                    "chroma_db_old_"
                    + str(uuid.uuid4())[:8]
                )

                try:

                    os.rename(
                        "chroma_db",
                        old_name
                    )

                    st.info(
                        f"Old database moved to {old_name}"
                    )

                except Exception as e:

                    st.error(
                        "❌ Windows is still locking ChromaDB."
                    )

                    st.error(
                        """
                        Please stop any other Python or
                        Streamlit process using this project.
                        """
                    )

                    st.exception(e)

                    st.stop()


        # =================================================
        # CREATE NEW DATABASE
        # =================================================

        with st.spinner(
            "📚 Creating embeddings and database..."
        ):

            result = subprocess.run(
                [
                    sys.executable,
                    "create_database.py"
                ],
                capture_output=True,
                text=True
            )


        # =================================================
        # DATABASE CREATION ERROR
        # =================================================

        if result.returncode != 0:

            st.error(
                "❌ Error while creating ChromaDB."
            )

            st.code(
                result.stderr
            )

            st.stop()


        # =================================================
        # SUCCESS
        # =================================================

        st.session_state[
            "book_processed"
        ] = True

        st.session_state[
            "book_name"
        ] = uploaded_file.name

        st.session_state[
            "messages"
        ] = []

        st.success(
            "✅ Book processed successfully!"
        )

        st.rerun()


# =========================================================
# RAG
# =========================================================

if st.session_state["book_processed"]:

    st.divider()

    st.subheader("📖 Currently Reading")

    st.info(
        f"📕 {st.session_state['book_name']}"
    )


    # =====================================================
    # CHAT HISTORY
    # =====================================================

    for message in st.session_state["messages"]:

        with st.chat_message(
            message["role"]
        ):

            st.write(
                message["content"]
            )


    # =====================================================
    # USER QUESTION
    # =====================================================

    query = st.chat_input(
        "Ask something about the book..."
    )


    if query:

        # =================================================
        # USER MESSAGE
        # =================================================

        st.session_state[
            "messages"
        ].append(
            {
                "role": "user",
                "content": query
            }
        )

        with st.chat_message("user"):

            st.write(query)


        # =================================================
        # EMBEDDINGS
        # =================================================

        with st.spinner(
            "🔎 Searching the book..."
        ):

            embedding_model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-en-v1.5"
            )


            # =============================================
            # LOAD CHROMA ONLY FOR THIS REQUEST
            # =============================================

            vectorstore = Chroma(
                persist_directory="chroma_db",
                embedding_function=embedding_model
            )


            # =============================================
            # RETRIEVER
            # =============================================

            retriever = vectorstore.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 4,
                    "fetch_k": 10,
                    "lambda_mult": 0.5
                }
            )


            # =============================================
            # RETRIEVE
            # =============================================

            docs = retriever.invoke(
                query
            )


        # =================================================
        # CONTEXT
        # =================================================

        context = "\n\n".join(
            [
                doc.page_content
                for doc in docs
            ]
        )


        # =================================================
        # PROMPT
        # =================================================

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
You are a helpful AI assistant.

Use only the provided context to answer the question.

If the answer is not present in the context,
say exactly:

"I could not find the answer."

Do not use outside knowledge.
"""
                ),

                (
                    "human",
                    """
Context:
{Context}

Question:
{question}
"""
                )
            ]
        )


        final_prompt = prompt.invoke(
            {
                "Context": context,
                "question": query
            }
        )


        # =================================================
        # GROQ
        # =================================================

        with st.spinner(
            "🤖 Generating answer..."
        ):

            try:

                llm = ChatGroq(
                    model="llama-3.3-70b-versatile"
                )

                response = llm.invoke(
                    final_prompt
                )

                answer = response.content

            except Exception as e:

                answer = (
                    "❌ Error generating answer."
                )

                st.error(
                    str(e)
                )


        # =================================================
        # ANSWER
        # =================================================

        with st.chat_message(
            "assistant"
        ):

            st.write(answer)


        # =================================================
        # SAVE ANSWER
        # =================================================

        st.session_state[
            "messages"
        ].append(
            {
                "role": "assistant",
                "content": answer
            }
        )


        # =================================================
        # RELEASE CHROMA OBJECT
        # =================================================

        del vectorstore

        del retriever

        del embedding_model

        gc.collect()