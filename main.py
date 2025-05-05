from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
import os

st.set_page_config(page_title="Constitution AI Assistant")

st.title("🇰🇿 Constitution AI Assistant")

uploaded_files = st.file_uploader("Upload Constitution or other documents", type=["pdf", "txt"], accept_multiple_files=True)

if uploaded_files:
    documents = []
import tempfile

for uploaded_file in uploaded_files:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name
    loader = PyPDFLoader(tmp_file_path)
    documents.extend(loader.load())


    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(chunks, embedding=embeddings, persist_directory="./chroma_db")
    retriever = vectorstore.as_retriever()

    qa = RetrievalQA.from_chain_type(llm=ChatOpenAI(), retriever=retriever)

    query = st.text_input("Ask a question about the Constitution:")
    if query:
        result = qa.run(query)
        st.success(result)
