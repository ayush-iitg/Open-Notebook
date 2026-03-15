css = '''
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --accent:  #f0a500;
    --accent2: #e05c5c;
    --text:    #e8e8f0;
    --border:  #1e1e2e;
    --radius:  14px;
}

.chat-message {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 18px 20px;
    border-radius: var(--radius);
    margin-bottom: 14px;
    border: 1px solid var(--border);
    animation: slideUp 0.3s ease forwards;
    font-family: 'DM Mono', monospace;
    font-size: 0.88rem;
    line-height: 1.7;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.chat-message.user {
    background: #161622;
    border-left: 3px solid var(--accent);
}

.chat-message.bot {
    background: #12121c;
    border-left: 3px solid var(--accent2);
}

.chat-message .avatar {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 0.75rem;
}

.chat-message.user .avatar { background: var(--accent);  color: #000; }
.chat-message.bot  .avatar { background: var(--accent2); color: #fff; }

.chat-message .message {
    flex: 1;
    color: var(--text);
    padding-top: 2px;
}
</style>
'''

page_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

.stApp { background-color: #0a0a0f !important; font-family: 'DM Mono', monospace; }

[data-testid="stSidebar"] {
    background-color: #0d0d15 !important;
    border-right: 1px solid #1e1e2e !important;
}

.sidebar-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 800;
    color: #f0a500;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}
.sidebar-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #6b6b80;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 18px;
}
.section-header {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6b6b80;
    border-bottom: 1px solid #1e1e2e;
    padding-bottom: 6px;
    margin: 18px 0 10px;
}
.main-header {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    color: #e8e8f0;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin-bottom: 4px;
}
.main-header span { color: #f0a500; }
.main-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.73rem;
    color: #6b6b80;
    letter-spacing: 0.05em;
    margin-bottom: 24px;
}
.stat-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
.stat-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #111118;
    border: 1px solid #1e1e2e;
    border-radius: 6px;
    padding: 4px 10px;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #e8e8f0;
}
.stat-chip .dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-green  { background: #4caf7d; }
.dot-red    { background: #e05c5c; }
.dot-yellow { background: #f0a500; }

.stTextInput input {
    background: #111118 !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.88rem !important;
    padding: 12px 16px !important;
}
.stTextInput input:focus {
    border-color: #f0a500 !important;
    box-shadow: 0 0 0 2px rgba(240,165,0,0.12) !important;
}

.stSelectbox > div > div {
    background: #111118 !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e8e8f0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}

[data-testid="stFileUploader"] {
    background: #111118 !important;
    border: 1px dashed #2a2a3e !important;
    border-radius: 10px !important;
}

.stButton button {
    background: #f0a500 !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.03em !important;
    padding: 10px 20px !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}
.stButton button:hover { background: #e09500 !important; }

hr { border-color: #1e1e2e !important; margin: 14px 0 !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0a0f; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 4px; }
</style>
"""

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">AI</div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">You</div>
    <div class="message">{{MSG}}</div>
</div>
'''
