import os
import streamlit as st

# On Streamlit Cloud the key comes from "Secrets". Locally it comes from .env
try:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

from agent_core import run_agent

MAX_MESSAGES = 25   # demo limit per visitor, protects the free quota

st.set_page_config(page_title="Mock Interview Agent", page_icon="🎤")
st.title("🎤 Mock Interview Agent")
st.caption("Paste a job link and I'll interview you. Pass, and I'll write your application kit.")

# Each visitor gets their own memory
if "contents" not in st.session_state:
    st.session_state.contents = []                          # what Gemini sees
    st.session_state.messages = []                          # what the page shows
    st.session_state.store = {"answers": [], "interview": 1}  # scores + weak topics
    st.session_state.count = 0                              # messages used

# Sidebar
st.sidebar.header("Your CV (optional)")
cv_text = st.sidebar.text_area(
    "Paste your CV here. It's only used to write your application kit if you pass.",
    height=250,
)

if st.sidebar.button("🔄 New interview"):
    st.session_state.contents = []
    st.session_state.messages = []
    st.session_state.store["interview"] += 1   # keeps old scores as "past progress"
    st.rerun()

st.sidebar.caption(f"Messages left in this demo: {max(0, MAX_MESSAGES - st.session_state.count)}")

# Show the chat so far
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        for t in m.get("tools", []):
            st.caption(f"🔧 Used tool: {t}")
        st.markdown(m["text"])

# Demo limit
if st.session_state.count >= MAX_MESSAGES:
    st.warning("Demo limit reached for this session. Refresh the page to start over.")
    st.stop()

# Chat input box
if prompt := st.chat_input("Paste a job link, or type your answer..."):
    st.session_state.count += 1
    st.session_state.messages.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply, tools_used = run_agent(
                st.session_state.contents, prompt, st.session_state.store, cv_text
            )
        for t in tools_used:
            st.caption(f"🔧 Used tool: {t}")
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "text": reply, "tools": tools_used})