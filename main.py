import os
import openai
from dotenv import load_dotenv
import fitz  # PyMuPDF
import streamlit as st
import tempfile
import shutil

load_dotenv()

openai.api_key = os.getenv("API_KEY")

v1_path = r'v1.pdf'
v2_path = r'v2.pdf'

def convert_pdf_to_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def split_text_into_chunks(text, max_tokens=2000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1  # +1 for the space
        if current_length > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def query_gpt4(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.1
    )
    return response.choices[0].message["content"].strip()

def compare_and_highlight(v1_text, v2_text, new_text):
    v1_chunks = split_text_into_chunks(v1_text)
    v2_chunks = split_text_into_chunks(v2_text)
    new_chunks = split_text_into_chunks(new_text)
    
    results = []
    for v1_chunk, v2_chunk, new_chunk in zip(v1_chunks, v2_chunks, new_chunks):
        prompt = f"""
        Compare the following two versions of a document:

        V1:
        {v1_chunk}

        V2:
        {v2_chunk}

        Highlight the differences and corrections made in V2 compared to V1.

        Now, based on the corrections highlighted, evaluate the following new document and suggest corrections:

        New Document:
        {new_chunk}
        """
        result = query_gpt4(prompt)
        results.append(result)
    
    return "\n".join(results)

def main():
    st.title("Document Comparison Tool")

    uploaded_file = st.file_uploader("Upload a new document", type="pdf")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(uploaded_file, tmp_file)
            tmp_file_path = tmp_file.name

        v1_text = convert_pdf_to_text(v1_path)
        v2_text = convert_pdf_to_text(v2_path)
        new_text = convert_pdf_to_text(tmp_file_path)

        comparison_result = compare_and_highlight(v1_text, v2_text, new_text)

        st.subheader("Comparison Result")
        st.write(comparison_result)

        os.remove(tmp_file_path)

if __name__ == "__main__":
    main()
