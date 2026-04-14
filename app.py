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


def get_unique_chat_name(base_name):
    name = base_name.strip() or "New Chat"
    if name not in st.session_state.sessions:
        return name

    suffix = 2
    while f"{name} ({suffix})" in st.session_state.sessions:
        suffix += 1

    return f"{name} ({suffix})"


# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sessions" not in st.session_state:
    st.session_state.sessions = {"New Chat": []}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = "New Chat"

if st.session_state.current_chat not in st.session_state.sessions:
    st.session_state.sessions[st.session_state.current_chat] = []

st.session_state.messages = st.session_state.sessions[st.session_state.current_chat].copy()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("### Welcome 👋")
    st.write("What would you like to research?")
    st.markdown("---")
    st.markdown("### 💬Previous Chats")

    # Show chats
    for chat in list(st.session_state.sessions.keys()):
        if st.button(chat, key=f"chat_{chat}"):
            st.session_state.current_chat = chat
            st.session_state.messages = st.session_state.sessions[chat].copy()
            st.rerun()

    # New Chat button
    if st.button("+ New Chat"):
        new_chat = get_unique_chat_name(f"Chat {len(st.session_state.sessions)+1}")
        st.session_state.sessions[new_chat] = []
        st.session_state.current_chat = new_chat
        st.session_state.messages = []
        st.rerun()

    if st.button("Reload Chat", key="reload_chat"):
        st.session_state.messages = st.session_state.sessions.get(
            st.session_state.current_chat, []
        ).copy()
        st.rerun()

# ---------------- FIXED TOP BAR ----------------
st.markdown("""
<style>
header {visibility: hidden;}

section[data-testid="stSidebar"] {
    z-index: 200;
}

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

@media (max-width: 768px) {
    .top-strip {
        left: 0;
    }
}

.block-container {
    padding-top: 80px;
}

div[data-testid="stChatInput"] {
    position: fixed;
    bottom: 20px;
    left: 260px;
    right: 20px;
    z-index: 100;
}

@media (max-width: 768px) {
    div[data-testid="stChatInput"] {
        left: 20px;
    }
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
query = st.chat_input("Ask anything...")

# ---------------- LOGIC ----------------
if query:

    # Save user message
    user_msg = {"role": "user", "content": query}
    st.session_state.messages.append(user_msg)

    # Rename chat using FIRST question
    if len(st.session_state.messages) == 1:
        new_name = get_unique_chat_name(" ".join(query.strip().split()[:5]))

        st.session_state.sessions[new_name] = st.session_state.sessions.pop(
            st.session_state.current_chat
        )
        st.session_state.current_chat = new_name

    # Show user message
    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Researching... 🚀"):

            # Step 1: Planning
            sub_questions = planner.generate_subquestions(query)
            planner.save_to_json(query, sub_questions)

            # Step 2: Research
            raw_answers, urls = researcher.research(sub_questions)
            researcher.save_answers_to_json(raw_answers, urls)

            # Step 3: Writing
            writer.write_answers()

            # Load final data
            with open("research_data.json", "r") as f:
                data = json.load(f)

            # ---------------- FORMAT RESPONSE ----------------
            response = ""

            for i, item in enumerate(data["sub_questions"], start=1):
                q = item.get("question", "")
                a = item.get("answer", "")

                # Get URLs for THIS question
                url_block = urls[i-1] if i-1 < len(urls) else ""

                # Handle multiple URLs separated by '\n'
                if isinstance(url_block, list):
                    split_urls = url_block
                else:
                    split_urls = [u.strip() for u in url_block.split("\n") if u.strip()]

                # Question + Answer
                response += f"### Q{i}: {q}\n{a}\n\n"

                # Sources for this question
                if split_urls:
                    response += "**Sources:**\n"
                    for j, u in enumerate(split_urls, start=1):
                        response += f"{j}. [{u}]({u})\n"

                    response += "\n---\n\n"

            # Display response
            st.markdown(response)

    # Save assistant message
    assistant_msg = {"role": "assistant", "content": response}
    st.session_state.messages.append(assistant_msg)

    # Save safely
    st.session_state.sessions[st.session_state.current_chat] = st.session_state.messages.copy()
