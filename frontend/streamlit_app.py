import streamlit as st
import requests
from app.agents.langgraph_agent import run_agent
from app.services.image_gen import generate_image
from langchain_core.messages import HumanMessage, AIMessage

st.title("NimbleQueryAI")

tab1, tab2 = st.tabs(["Chat with Tools", "Image Generator"])

def convert_history(ui_history):
    """Convert UI chat history (dicts) to LangChain BaseMessage objects."""
    converted = []
    for msg in ui_history:
        if msg["type"] == "human":
            converted.append(HumanMessage(content=msg["content"]))
        elif msg["type"] == "ai":
            converted.append(AIMessage(content=msg["content"]))
    return converted

with tab1:
    # ----- Chat UI -----
    if "history" not in st.session_state:
        st.session_state.history = []

    user_input = st.text_input("Ask a question:")
    send_btn = st.button("Send")

    if send_btn and user_input:
        # Convert UI history to BaseMessage objects for agent
        agent_history = convert_history(st.session_state.history)
        reply = run_agent(user_input, agent_history)
        st.session_state.history.append({"type": "human", "content": user_input})
        st.session_state.history.append({"type": "ai", "content": reply})

    # Display chat history
    for turn in st.session_state.history:
        who = "User" if turn["type"] == "human" else "Assistant"
        st.write(f"{who}: {turn['content']}")

    st.markdown("---")
    st.subheader("Audio & Video Generation")

    API_BASE = "http://localhost:8000"  # Update if deployed

    text = st.text_area("Enter text to convert into audio or video:", key="audio_video_text")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Audio"):
            with st.spinner("Generating audio..."):
                response = requests.post(f"{API_BASE}/generate-audio", json={"text": text})
                audio_path = response.json().get("audio_path")
                if audio_path:
                    st.audio(audio_path)
                else:
                    st.error("Audio generation failed.")
    with col2:
        if st.button("Generate Video"):
            with st.spinner("Generating video..."):
                response = requests.post(f"{API_BASE}/generate-video", json={"text": text})
                video_path = response.json().get("video_path")
                if video_path:
                    st.video(video_path)
                else:
                    st.error("Video generation failed.")

    st.markdown("---")
    st.subheader("Ask Questions About Your PDF")

    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file is not None and st.button("Index PDF"):
        with st.spinner("Uploading & indexing your PDF..."):
            resp = requests.post(
                f"{API_BASE}/rag/upload",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
            )
            if resp.ok:
                data = resp.json()
                st.session_state.doc_id = data["doc_id"]
                st.success(f"Indexed {data['n_chunks']} chunks. Ask away below.")
            else:
                st.error("PDF indexing failed.")

    pdf_question = st.text_input("Ask a question about your PDF:", key="pdf_question")
    if st.button("Ask PDF Question"):
        doc_id = st.session_state.get("doc_id")
        if not doc_id:
            st.warning("Please upload and index a PDF first.")
        else:
            with st.spinner("Searching your PDF..."):
                resp = requests.post(
                    f"{API_BASE}/rag/ask",
                    json={"doc_id": doc_id, "question": pdf_question},
                )
                if resp.ok:
                    st.write(f"Answer: {resp.json()['answer']}")
                else:
                    st.error("Question failed.")

with tab2:
    img_prompt = st.text_input("Enter a prompt to generate an image:")
    if st.button("Generate Image"):
        with st.spinner("Creating image..."):
            image = generate_image(img_prompt)
            st.image(image, caption="Generated Image", use_column_width=True)