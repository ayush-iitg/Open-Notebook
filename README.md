# 📓 OpenNotebook

> An open source alternative to Google's NotebookLM — chat with your PDF documents and YouTube videos using RAG, LangChain, and LLaMA 3.3.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?style=flat-square&logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-0.2+-green?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 🔗 Live Demo

**[opennotebook.streamlit.app](https://opennotebook.streamlit.app)**

---

## 📌 What is OpenNotebook?

OpenNotebook lets you upload PDF documents and paste YouTube video URLs, then ask questions about them in plain English. The AI answers based strictly on your content — not from the internet or its training data.

It uses **RAG (Retrieval-Augmented Generation)** — which means:
1. Your content is broken into chunks and stored in a vector database
2. When you ask a question, the most relevant chunks are retrieved
3. Those chunks are sent to the LLM as context to generate a grounded answer

---

## ✨ Features

- 📄 **Multiple PDF support** — upload and query several PDFs at once
- ▶ **YouTube video support** — paste video URLs and chat with transcripts
- 🌍 **13 languages** — fetch transcripts in English, Hindi, Spanish, French and more
- 🔍 **Semantic search** — finds relevant content by meaning, not just keywords
- 💬 **Chat interface** — clean conversation UI with message history
- 📊 **Source stats** — see how many PDFs, videos and chunks are indexed
- 🔒 **Private** — your data never leaves your machine (runs locally)
- 🔄 **Clear & Reset** — wipe the knowledge base and start fresh anytime

---

## 🏗️ How It Works

```
Upload PDFs + YouTube URLs
         ↓
Extract text (pypdf + youtube-transcript-api)
         ↓
Split into 1000-character chunks (LangChain)
         ↓
Convert chunks to vectors (HuggingFace all-MiniLM-L6-v2)
         ↓
Store vectors in ChromaDB (in-memory)
         ↓
User asks a question
         ↓
Find top 5 most relevant chunks (semantic search)
         ↓
Send chunks + question to LLaMA 3.3 via Groq API
         ↓
Display grounded answer in chat UI
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | LLaMA 3.3 70B via Groq API |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Vector Store | ChromaDB (in-memory) |
| RAG Framework | LangChain |
| PDF Parsing | pypdf |
| YouTube Transcripts | youtube-transcript-api |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/opennotebook.git
cd opennotebook
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# .\venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a Groq API key

1. Go to [console.groq.com](https://console.groq.com) and sign up for free
2. Navigate to **API Keys** → click **Create API Key**
3. Copy the key

### 5. Add your API key

Create a `.env` file in the project root:

```ini
GROQ_API_KEY="your_api_key_here"
```

### 6. Run the app

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📖 How to Use

1. **Upload PDFs** — drag and drop PDF files in the sidebar
2. **Add YouTube URLs** — paste video links and select the video language
3. **Click Process** — wait for the knowledge base to build
4. **Ask questions** — type your question and click Ask

---

## 📁 Project Structure

```
opennotebook/
├── app.py              # Main application logic
├── htmlTemplates.py    # Chat UI styling (HTML/CSS)
├── requirements.txt    # Python dependencies
├── .env                # API keys (never commit this)
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

### Increase PDF upload size limit

Create `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 1000
```

### Support more YouTube videos

In `app.py`, change:
```python
num_videos = st.selectbox("Number of videos", options=[1, 2, 3])
# to
num_videos = st.selectbox("Number of videos", options=[1, 2, 3, 4, 5])
```

---

## 🗺️ Roadmap

- [ ] PDF page number references in answers
- [ ] YouTube timestamp references in answers
- [ ] Web URL support
- [ ] Google Docs / Slides support
- [ ] Persistent vector store (save and reload sessions)
- [ ] Multiple LLM support (OpenAI, Gemini, Ollama)
- [ ] Docker support

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- Inspired by [Google NotebookLM](https://notebooklm.google.com)
- Built with [LangChain](https://langchain.com), [Groq](https://groq.com), and [Streamlit](https://streamlit.io)

---

<p align="center">Built with ❤️ as an open source alternative to NotebookLM</p>
