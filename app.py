# =============================================================================
# AskAnything — Chat with PDFs and YouTube Videos
# =============================================================================
#
# HOW THIS APP WORKS (step by step):
#
#   1. User uploads PDF files and/or pastes YouTube video URLs
#   2. We extract text from PDFs using pypdf
#   3. We fetch transcripts from YouTube using youtube-transcript-api
#   4. All that text is split into small chunks (1000 characters each)
#   5. Each chunk is converted into a vector (a list of numbers) using
#      a HuggingFace embedding model — this captures the "meaning" of text
#   6. All vectors are stored in ChromaDB (an in-memory vector database)
#   7. When the user asks a question:
#        a. The question is also converted to a vector
#        b. ChromaDB finds the 5 most similar chunks (semantic search)
#        c. Those chunks are sent to the Groq LLM as context
#        d. The LLM reads the context and answers the question
#
# =============================================================================

import os
import re
import streamlit as st
from dotenv import load_dotenv

from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from htmlTemplates import css, page_css, bot_template, user_template


# =============================================================================
# LANGUAGE OPTIONS
# Maps the language name shown in the dropdown to its YouTube language code
# =============================================================================

LANGUAGE_CODES = {
    "English":    "en",
    "Hindi":      "hi",
    "Spanish":    "es",
    "French":     "fr",
    "German":     "de",
    "Portuguese": "pt",
    "Arabic":     "ar",
    "Chinese":    "zh",
    "Japanese":   "ja",
    "Korean":     "ko",
    "Italian":    "it",
    "Russian":    "ru",
    "Turkish":    "tr",
}


# =============================================================================
# STEP 1 — EXTRACT TEXT FROM PDFs
# =============================================================================

def get_pdf_text(pdf_docs):
    # Start with an empty string — we will keep adding text to it
    all_text = ""

    # Loop through each uploaded PDF file
    for pdf in pdf_docs:
        try:
            reader = PdfReader(pdf)

            # Loop through every page in this PDF
            for page in reader.pages:
                page_text = page.extract_text()

                # Only add the text if the page actually has text
                # (some pages are image-only and return nothing)
                if page_text:
                    all_text = all_text + page_text

        except Exception as e:
            st.warning("Could not read " + pdf.name + ": " + str(e))

    return all_text


# =============================================================================
# STEP 2A — FIND THE VIDEO ID INSIDE A YOUTUBE URL
# =============================================================================

def extract_youtube_id(url):
    # YouTube video IDs are always 11 characters long
    # Examples:
    #   https://www.youtube.com/watch?v=dQw4w9WgXcQ  →  dQw4w9WgXcQ
    #   https://youtu.be/dQw4w9WgXcQ                 →  dQw4w9WgXcQ

    # Pattern 1: standard URL  (youtube.com/watch?v=ID)
    match = re.search(r"v=([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)

    # Pattern 2: short URL  (youtu.be/ID)
    match = re.search(r"youtu\.be/([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)

    # Pattern 3: embedded URL  (youtube.com/embed/ID)
    match = re.search(r"embed/([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)

    # Could not find a video ID in this URL
    return None


# =============================================================================
# STEP 2B — FETCH THE TRANSCRIPT FROM YOUTUBE
# =============================================================================

def get_youtube_transcript(url, language_code):
    # First, get the video ID from the URL
    video_id = extract_youtube_id(url)

    # If we couldn't find an ID, stop here with a clear error message
    if not video_id:
        raise ValueError("Could not find a video ID in this URL: " + url)

    # Try to fetch the transcript in the chosen language
    # If that language is not available, also try English as a backup
    try:
        transcript_segments = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=[language_code, "en"]
        )
    except (NoTranscriptFound, TranscriptsDisabled):
        # If neither the chosen language nor English worked,
        # try YouTube's auto-generated English captions as a last resort
        transcript_segments = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=["en-auto", "en"]
        )

    # transcript_segments is a list that looks like this:
    # [
    #   {"text": "Hello everyone",  "start": 0.0,  "duration": 2.0},
    #   {"text": "welcome back",    "start": 2.0,  "duration": 1.5},
    #   ...
    # ]
    # We only need the "text" part, so we collect all text and join with spaces

    all_text_parts = []
    for segment in transcript_segments:
        all_text_parts.append(segment["text"])

    full_transcript = " ".join(all_text_parts)

    # Split the full transcript into smaller chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        
    )
    chunks = splitter.split_text(full_transcript)

    # Wrap each chunk in a Document object
    # Document just pairs the text with some extra info (metadata)
    # so we can later tell whether a chunk came from YouTube or a PDF
    docs = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk,
            metadata={
                "source":    "youtube",
                "video_id":  video_id,
                "video_url": url,
                "language":  language_code,
            }
        )
        docs.append(doc)

    return docs


# =============================================================================
# STEP 3 — SPLIT PDF TEXT INTO CHUNKS
# =============================================================================

def get_text_chunks(text):
    # We can't feed the entire PDF text to the AI at once —
    # it's too long. So we split it into smaller 1000-character pieces.
    # chunk_overlap=200 means each chunk shares 200 characters with
    # the next one, so no information is lost at the boundaries.

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_text(text)

    # Wrap each chunk in a Document object (same as we did for YouTube)
    docs = []
    for chunk in chunks:
        doc = Document(
            page_content=chunk,
            metadata={"source": "pdf"}
        )
        docs.append(doc)

    return docs


# =============================================================================
# STEP 4 — STORE ALL CHUNKS IN A VECTOR DATABASE
# =============================================================================

def get_vectorstore(all_docs):
    # Convert every text chunk into a vector (list of numbers)
    # using a free HuggingFace model that runs locally on your machine.
    # Similar text = similar vectors, which enables semantic search.
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
   
    # Store all vectors in ChromaDB (kept in memory, not saved to disk)
    vectorstore = Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=None,
    )

    return vectorstore


# =============================================================================
# STEP 5 — BUILD THE RAG CHAIN (the AI question-answering pipeline)
# =============================================================================

def get_conversation_chain(vectorstore):
    # Load the Groq API key from the .env file
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Please add it to your .env file.")

    # Set up the Groq LLM
    # temperature=0 means the AI gives consistent, factual answers (not creative)
    llm = ChatGroq(
        groq_api_key=api_key,
        model_name="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=1024,
    )

    # The retriever will search ChromaDB and return the 5 most relevant chunks
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # This is the prompt we send to the AI
    # {context} and {question} are placeholders that get filled in at runtime
    prompt_template = """You are a helpful assistant.
Use the context below to answer the question.
The context may include text from PDF documents and YouTube video transcripts.
If the answer is not in the context, say "I don't know based on the provided sources."
Keep your answer clear and concise.

Context:
{context}

Question: {question}

Answer:"""

    prompt = ChatPromptTemplate.from_template(prompt_template)

    # This function formats the retrieved chunks into a readable context string
    # It also labels each chunk so the AI knows where it came from
    def format_docs(docs):
        parts = []
        for doc in docs:
            source = doc.metadata.get("source", "unknown")

            if source == "youtube":
                video_id = doc.metadata.get("video_id", "unknown")
                label = "[Source: YouTube video '" + video_id + "']"
            else:
                label = "[Source: PDF document]"

            parts.append(label + "\n" + doc.page_content)

        return "\n\n".join(parts)

    # Build the chain — each step flows into the next using the | symbol
    # Step 1: retriever finds relevant chunks, format_docs formats them
    # Step 2: prompt fills in {context} and {question}
    # Step 3: llm reads the prompt and generates an answer
    # Step 4: StrOutputParser extracts the plain text from the response
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


# =============================================================================
# STEP 6 — HANDLE THE USER'S QUESTION AND SHOW THE ANSWER
# =============================================================================

def handle_userinput(user_question):
    # Send the question through the RAG chain and get an answer
    try:
        answer = st.session_state.conversation.invoke(user_question)

        # Save the question and answer to chat history
        st.session_state.chat_history.append(("human", user_question))
        st.session_state.chat_history.append(("ai", answer))

    except Exception as e:
        st.error("Something went wrong: " + str(e))
        return

    # Display the full chat history on screen
    # chat_history alternates between human and ai messages like:
    # [ ("human", "question1"), ("ai", "answer1"), ("human", "question2"), ... ]
    # So we loop in steps of 2 to get each human+ai pair together
    i = 0
    while i < len(st.session_state.chat_history):

        # Show the user message
        user_msg = st.session_state.chat_history[i][1]
        st.write(
            user_template.replace("{{MSG}}", user_msg),
            unsafe_allow_html=True,
        )

        # Show the AI response (if it exists)
        if i + 1 < len(st.session_state.chat_history):
            ai_msg = st.session_state.chat_history[i + 1][1]
            st.write(
                bot_template.replace("{{MSG}}", ai_msg),
                unsafe_allow_html=True,
            )

        i = i + 2  # move to the next human+ai pair


# =============================================================================
# MAIN — STREAMLIT PAGE LAYOUT
# =============================================================================

def main():
    # Load the GROQ_API_KEY from the .env file
    load_dotenv()

    # Set the browser tab title and icon
    st.set_page_config(
        page_title="AskAnything — PDF & Video RAG",
        page_icon="◈",
        layout="wide",
    )

    # Apply custom CSS styling to the page
    st.write(page_css, unsafe_allow_html=True)
    st.write(css, unsafe_allow_html=True)

    # Session state stores values that need to survive page reruns
    # (Streamlit reruns the whole script on every interaction)
    if "conversation" not in st.session_state:
        st.session_state.conversation = None  # the RAG chain

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []    # list of messages

    if "pdf_count" not in st.session_state:
        st.session_state.pdf_count = 0        # number of PDFs processed

    if "video_count" not in st.session_state:
        st.session_state.video_count = 0      # number of videos processed

    if "chunk_count" not in st.session_state:
        st.session_state.chunk_count = 0      # total chunks indexed

    # Page header
    st.markdown(
        '<div class="main-header">Open<span>    Notebook</span></div>'
        '<div class="main-sub">PDF documents · YouTube videos</div>',
        unsafe_allow_html=True,
    )

    # Show stats bar only after sources have been processed
    if st.session_state.conversation:
        st.markdown(
            f"""
            <div class="stat-row">
                <div class="stat-chip">
                    <span class="dot dot-green"></span>
                    {st.session_state.pdf_count} PDF(s)
                </div>
                <div class="stat-chip">
                    <span class="dot dot-red"></span>
                    {st.session_state.video_count} Video(s)
                </div>
                <div class="stat-chip">
                    <span class="dot dot-yellow"></span>
                    {st.session_state.chunk_count} chunks indexed
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Question input box and Ask button side by side
    col1, col2 = st.columns([5, 1])  # col1 is 5x wider than col2

    with col1:
     user_question = st.text_input(
        "",
        placeholder="Ask a question about your PDFs or videos...",
        label_visibility="collapsed",
      )

     with col2:
      ask_clicked = st.button("Ask ➜")

      # Only run when Ask button is clicked AND question is not empty
    if ask_clicked and user_question:
      if st.session_state.conversation:
        handle_userinput(user_question)
      else:
        st.warning("Please upload and process your sources first using the sidebar →")

    # If button clicked but no question typed
    if ask_clicked and not user_question:
       st.warning("Please type a question first.")

   

    # =========================================================================
    # SIDEBAR
    # =========================================================================
    with st.sidebar:

        st.markdown(

            '<div class="sidebar-title">Open   Notebook</div>'
            '<div class="sidebar-sub">Your Knowledge Base</div>',
            unsafe_allow_html=True,
        )

        # PDF upload section
        st.markdown('<div class="section-header">📄 PDF Documents</div>', unsafe_allow_html=True)

        pdf_docs = st.file_uploader(
            "Upload PDFs",
            accept_multiple_files=True,
            type=["pdf"],
            label_visibility="collapsed",
        )

        # Show the name of each uploaded file
        if pdf_docs:
            for f in pdf_docs:
                st.caption("📎 " + f.name)

        # YouTube section
        st.markdown('<div class="section-header">▶ YouTube Videos</div>', unsafe_allow_html=True)

        num_videos = st.selectbox("Number of videos", options=[1, 2, 3])

        # Show URL + language inputs for each video
        video_inputs = []

        for i in range(num_videos):
            st.markdown("**Video " + str(i + 1) + "**")

            url = st.text_input(
                "YouTube URL",
                placeholder="https://youtube.com/watch?v=...",
                key="yt_url_" + str(i),
                label_visibility="collapsed",
            )

            lang = st.selectbox(
                "Language",
                options=list(LANGUAGE_CODES.keys()),
                key="yt_lang_" + str(i),
            )

            # Only add this video if the user actually typed a URL
            if url.strip():
                video_inputs.append({"url": url.strip(), "language": lang})

        st.markdown("---")

        # Process button
        if st.button("⚡ Process All Sources"):

            # Make sure at least one source was provided
            if not pdf_docs and not video_inputs:
                st.warning("Please add at least one PDF or YouTube URL.")
                return

            # Make sure the API key is set
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                st.error("GROQ_API_KEY not found. Add it to your .env file.")
                return

            # This list will collect all chunks from all sources
            all_docs = []

            # Process PDFs
            if pdf_docs:
                with st.spinner("Extracting text from PDFs..."):
                    raw_text = get_pdf_text(pdf_docs)

                    if raw_text.strip():
                        text_docs = get_text_chunks(raw_text)
                        all_docs.extend(text_docs)
                        st.caption("✓ " + str(len(text_docs)) + " chunks from " + str(len(pdf_docs)) + " PDF(s)")
                    else:
                        st.warning("No text could be extracted from the PDFs.")

            # Process YouTube videos
            for video in video_inputs:
                lang_code = LANGUAGE_CODES[video["language"]]
                video_id  = extract_youtube_id(video["url"])

                with st.spinner("Fetching transcript for: " + str(video_id) + "..."):
                    try:
                        yt_docs = get_youtube_transcript(video["url"], lang_code)
                        all_docs.extend(yt_docs)
                        st.caption("✓ " + str(len(yt_docs)) + " chunks from video '" + str(video_id) + "'")

                    except TranscriptsDisabled:
                        st.error("Transcripts are disabled for this video: " + str(video_id))

                    except NoTranscriptFound:
                        st.error("No " + video["language"] + " transcript found for '" + str(video_id) + "'. Try English.")

                    except Exception as e:
                        st.error("Error fetching transcript: " + str(e))

            # Stop if nothing was collected
            if not all_docs:
                st.error("No content could be indexed. Please check your sources.")
                return

            # Build the vector store and conversation chain
            with st.spinner("Building knowledge base and preparing AI..."):
                vectorstore = get_vectorstore(all_docs)
                st.session_state.conversation = get_conversation_chain(vectorstore)
                st.session_state.chat_history = []
                st.session_state.pdf_count    = len(pdf_docs) if pdf_docs else 0
                st.session_state.video_count  = len(video_inputs)
                st.session_state.chunk_count  = len(all_docs)

            st.success("✓ Ready! " + str(len(all_docs)) + " chunks indexed. Ask your first question!")

        # Show reset button only after processing
        if st.session_state.conversation:
            st.markdown("---")
            if st.button("Clear & Reset"):
                st.session_state.conversation = None
                st.session_state.chat_history = []
                st.session_state.pdf_count    = 0
                st.session_state.video_count  = 0
                st.session_state.chunk_count  = 0
                st.rerun()


# This is the entry point — Python starts running from here
if __name__ == "__main__":
    main()