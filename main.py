import os
import tempfile
import numpy as np
from dotenv import load_dotenv

import streamlit as st
from web3 import Web3

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI

from config import contract_abi

# --- Load environment ---
load_dotenv()
contract_address = os.getenv("CONTRACT_ADDRESS")

# --- Streamlit setup ---
st.set_page_config(page_title="Constitution AI Assistant")
st.title("🇰🇿 KZ Constitution AI Assistant")

# --- Blockchain setup ---
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
contract = w3.eth.contract(address=contract_address, abi=contract_abi)
w3.eth.default_account = w3.eth.accounts[0]

# --- Helper: send one vector on-chain ---
def send_vector_onchain(vector: list[float]):
    scaled = [int(x * 100) for x in vector]
    tx_hash = contract.functions.storeVector(scaled).transact()
    w3.eth.wait_for_transaction_receipt(tx_hash)

# --- Session init ---
if "chunk_texts" not in st.session_state:
    st.session_state.chunk_texts = []
if "vectors_uploaded" not in st.session_state:
    st.session_state.vectors_uploaded = False
if "vectors_cache" not in st.session_state:
    st.session_state.vectors_cache = []

# --- File Upload ---
uploaded_files = st.file_uploader("Upload Constitution PDF", type=["pdf"], accept_multiple_files=True)

existing_count = contract.functions.getTotalVectors().call()
st.info(f"Currently stored vectors on-chain: {existing_count}")

if uploaded_files:
    documents = []
    for uploaded_file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        loader = PyPDFLoader(tmp_file_path)
        documents.extend(loader.load())

    # --- Chunking ---
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    for chunk in chunks:
        text = chunk.page_content
        st.session_state.chunk_texts.append(text)

        # Store vector only if none on chain
        if existing_count == 0:
            vector = embeddings.embed_query(text)
            send_vector_onchain(vector)

    if existing_count == 0:
        st.success("All vectors uploaded to blockchain successfully!")
    else:
        st.info("Chunk text restored. Vectors already on-chain.")

# --- Ask a question ---
query = st.text_input("Ask a question about the Constitution:")

if query:
    embeddings = OpenAIEmbeddings()
    query_embedding = embeddings.embed_query(query)

    # Fetch on-chain vectors (cached)
    if not st.session_state.vectors_cache:
        total = contract.functions.getTotalVectors().call()
        for i in range(total):
            raw_vector = contract.functions.getVector(i).call()
            float_vector = [val / 100 for val in raw_vector]
            st.session_state.vectors_cache.append(float_vector)

    def cosine_similarity(a, b):
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    scores = [cosine_similarity(query_embedding, vec) for vec in st.session_state.vectors_cache]
    best_index = int(np.argmax(scores))

    if len(st.session_state.chunk_texts) <= best_index:
        st.warning("This session has no chunk text history. Please re-upload the PDF to restore context.")
    else:
        best_text = st.session_state.chunk_texts[best_index]

        # --- AI Answer using LLM ---
        prompt = f"""
Use the following excerpt from the Constitution to answer the user's question.

Excerpt:
\"\"\"{best_text}\"\"\"

Question: {query}
Answer:"""

        llm = ChatOpenAI(temperature=0)
        result = llm.invoke(prompt)

        st.markdown("### 🧠 AI Answer:")
        st.write(result.content)

        st.markdown("### 📜 Source Excerpt:")
        st.write(best_text)
