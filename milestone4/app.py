import streamlit as st
import json

from planner import PlannerAgent
from researcher import ResearcherAgent
from writer import WriterAgent

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide")

# ---------------- AGENTS ----------------
planner = PlannerAgent()
researcher = ResearcherAgent()
writer = WriterAgent()
# ---------------- RELATION CHECK ----------------
def is_related_query(query, context):
    prompt = f"""
Determine if the new question is related to previous conversation.

Context:
{context}

Question:
{query}

Answer ONLY "YES" or "NO"
"""
    return planner.llm(prompt).strip()
# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sessions" not in st.session_state:
    st.session_state.sessions = {"New Chat": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"

if "retry_query" not in st.session_state:
    st.session_state.retry_query = None

if "last_query" not in st.session_state:
    st.session_state.last_query = None
    
if "processed_query" not in st.session_state:
    st.session_state.processed_query = None


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.image("stock-vector-welcome-poster-with-spectrum-brush-strokes-on-white-background-colorful-gradient-brush-design-1146069941-removebg-preview.png")
    st.write("What would you like to research?")
    st.markdown("### 💬 Previous Chats")

    for chat in list(st.session_state.sessions.keys()):
        if st.button(chat):
            st.session_state.current_chat = chat
            st.session_state.messages = st.session_state.sessions[chat].copy()

    if st.button("+ New Chat"):
        new_chat = f"New Chat {len(st.session_state.sessions)+1}"
        st.session_state.sessions[new_chat] = []
        st.session_state.current_chat = new_chat
        st.session_state.messages = []
        st.session_state.processed_query = None 

# ---------------- STYLE ----------------
st.markdown("""
<style>
div.stButton > button {
    display: inline-flex;
    align-items: center;
    justify-content: center;

    width: auto !important;
    min-width: 250px;
    max-width: 100%;

    padding: 12px 20px;
    font-size: 18px;

    border-radius: 12px;

    white-space: nowrap !important;
    overflow: hidden;
    text-overflow: ellipsis;
}
div.stButton {
    display: inline-block;
}
header {visibility: hidden;}
.top-strip {
    position: fixed;
    top: 0;
    left: 250px;
    right: 0;
    height: 55px;
    background: #0e1117;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid #222;
    font-size: 18px;
    font-weight: 600;
    z-index: 100;
}
.block-container {
    padding-top: 80px;
}
div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: 320px;
    right: 20px;
    z-index: 100;
}
</style>

<div class="top-strip">
    OpenDeep Researcher Agent
</div>
""", unsafe_allow_html=True)

# ---------------- CHAT DISPLAY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- INPUT ----------------
query_input = st.chat_input("Ask anything...")

# Retry logic
if st.session_state.retry_query:
    query = st.session_state.retry_query
    st.session_state.retry_query = None
else:
    query = query_input

is_retry = query_input is None and query is not None
if is_retry:
    st.info("🔄 Retrying previous query...")
# ---------------- PROGRESS UI ----------------
def update_ui(progress, text):
    progress_bar.progress(progress)
    status_placeholder.markdown(f"""
    <div style="
        padding: 12px;
        border-radius: 10px;
        background-color: #1e1e1e;
        border: 1px solid #333;
        margin-bottom: 10px;
    ">
         {text}
    </div>
    """, unsafe_allow_html=True)

# ---------------- MAIN ----------------
if query and (st.session_state.processed_query is None or query != st.session_state.processed_query):
    context = ""
    for msg in st.session_state.messages[-3:]:
        context += f"{msg['role']}: {msg['content']}\n"

    st.session_state.last_query = query

    # ✅ Add user message only once
    if not is_retry:
        user_msg = {'role':'user', 'content': query}
        st.session_state.messages.append(user_msg)


    # Rename chat
    if len(st.session_state.messages) == 1:
        new_name = " ".join(query.strip().split()[:5])
        st.session_state.sessions[new_name] = st.session_state.sessions.pop(
            st.session_state.current_chat
        )
        st.session_state.current_chat = new_name

    # Show user message
    if not is_retry:
        with st.chat_message("user"):
                st.markdown(query)

    with st.chat_message("assistant"):

        status_placeholder = st.empty()
        progress_bar = st.progress(0)

        try:
            update_ui(10, "Planner Agent is generating sub-questions...")
            relation = is_related_query(query, context)

            if relation == "YES":
                final_context = context
            else:
                final_context = ""

            sub_questions = planner.generate_subquestions(query, context=final_context)         
            planner.save_to_json(query, sub_questions)
 
            update_ui(40, "Planner Agent completed ✅")

            update_ui(50, "Researcher Agent is searching the internet...")
            raw_answers, urls, titles = researcher.research(sub_questions)
            researcher.save_answers_to_json(raw_answers, urls, titles)

            update_ui(80, "Researcher Agent completed ✅")

            update_ui(85, "Writer Agent is summarizing results...")
            writer.write_answers()

            update_ui(100, "Writer Agent completed ✅")

            with open("research_data.json", "r") as f:
                data = json.load(f)

            response = ""

            for i, item in enumerate(data["sub_questions"], start=1):
                q = item.get("question", "")
                a = item.get("answer", "")

                url_block = item.get("url", "")
                title_block = item.get("title", "")

                split_urls = [u.strip() for u in url_block.split("\n") if u.strip()]
                split_titles = [t.strip() for t in title_block.split("\n") if t.strip()]

                response += f"### Q{i}: {q}\n{a}\n\n"

                if split_urls:
                    response += "**Sources:**\n"
                    for j, (t, u) in enumerate(zip(split_titles, split_urls), start=1):
                        response += f"{j}. **{t}**\n{u}\n\n"

            progress_bar.empty()
            status_placeholder.empty()

            # ✅ FIX: Append BEFORE display (only once)
            assistant_msg = {"role": "assistant", "content": response}

            # duplicate guard (STRONG)
            if not st.session_state.messages or st.session_state.messages[-1].get("content") != response:
                st.session_state.messages.append(assistant_msg)

            # st.markdown(response)

            # mark as processed
            st.session_state.processed_query = query
            st.rerun() 
 

        except Exception as e:
            progress_bar.empty()
            status_placeholder.empty()

            error_msg = str(e)

            if "LM_STUDIO_NOT_RUNNING" in error_msg:
                st.error("⚠️ LM Studio not running.")
            elif "TAVILY_API_MISSING" in error_msg:
                st.error("⚠️ Tavily API key missing.")
            elif "NO_INTERNET" in error_msg:
                st.error("⚠️ Internet required.")
            else:
                st.error(f"⚠️ Error: {error_msg}")

            st.session_state.retry_query = st.session_state.last_query

            st.session_state.processed_query = None

            col1, col2 = st.columns([1,9])
            with col1:
                if st.button("🔄 Reload", key=f"retry_{len(st.session_state.messages)}"):
                    st.rerun()

            st.stop()

    # Save chat
    st.session_state.sessions[st.session_state.current_chat] = st.session_state.messages.copy()