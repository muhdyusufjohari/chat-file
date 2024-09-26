import streamlit as st
import groq
import os
import io

# Initialize Groq client
if 'GROQ_API_KEY' in st.secrets:
    client = groq.Groq(api_key=st.secrets['GROQ_API_KEY'])
elif 'GROQ_API_KEY' in os.environ:
    client = groq.Groq(api_key=os.environ['GROQ_API_KEY'])
else:
    st.error("Groq API key not found. Please set it in Streamlit secrets or as an environment variable.")
    st.stop()

# Streamlit app
st.title("Chatbot using Groq API")

# Model selection
model = st.selectbox("Choose a model:", ["llama2-8b-chat", "mixtral-8x7b-32768"])

# File upload
uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'docx'])
if uploaded_file is not None:
    # Read file content
    if uploaded_file.type == "text/plain":
        file_content = uploaded_file.getvalue().decode("utf-8")
    elif uploaded_file.type == "application/pdf":
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
        file_content = ""
        for page in pdf_reader.pages:
            file_content += page.extract_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import docx
        doc = docx.Document(io.BytesIO(uploaded_file.getvalue()))
        file_content = "\n".join([para.text for para in doc.paragraphs])
    
    st.session_state.file_content = file_content
    st.success(f"File '{uploaded_file.name}' has been uploaded and processed.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What is your question?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare messages including file content if available
    messages = []
    if 'file_content' in st.session_state:
        messages.append({
            "role": "system",
            "content": f"The following is the content of an uploaded file. Please use this information to answer the user's questions:\n\n{st.session_state.file_content}"
        })
    messages.extend(st.session_state.messages)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            for response in client.chat.completions.create(
                messages=messages,
                model=model,
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.stop()
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Clear chat history and uploaded file
if st.button("Clear Chat History and Uploaded File"):
    st.session_state.messages = []
    if 'file_content' in st.session_state:
        del st.session_state.file_content
    st.rerun()

# Debug information
st.sidebar.write("Debug Information:")
st.sidebar.write(f"File uploaded: {'Yes' if 'file_content' in st.session_state else 'No'}")
if 'file_content' in st.session_state:
    st.sidebar.write(f"File content length: {len(st.session_state.file_content)} characters")
st.sidebar.write(f"Number of messages: {len(st.session_state.messages)}")
