import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))



# ✅ Set modern UI theme
st.set_page_config(page_title="📄 Chat with PDF", layout="wide", page_icon="📚")

# ✅ Custom CSS for a stylish look
st.markdown("""
    <style>
    body { background-color: #121212; color: white; }
    .main { background: linear-gradient(135deg, #1f1c2c, #928DAB); padding: 20px; border-radius: 10px; }
    .stTextInput, .stButton>button { border-radius: 8px; font-size: 16px; }
    .sidebar .sidebar-content { background: #222; color: white; }
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    </style>
""", unsafe_allow_html=True)


def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader= PdfReader(pdf)
        for page in pdf_reader.pages:
            text+= page.extract_text()
    return  text



def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks


def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")


def get_conversational_chain():

    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                             temperature=0.2)

    prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain



def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    
    response = chain(
        {"input_documents":docs, "question": user_question}
        , return_only_outputs=True)

    print(response)
    st.write("Reply: ", response["output_text"])




def main():
    # st.set_page_config("Chat PDF")
    st.header("PdfTalk.ai - Chat with PDF using Gemini💁")

    user_question = st.text_input("🤖 Ask AI about your PDF")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("📚 Chat with PDF")
        st.subheader("⚡ Options:")
        pdf_docs = st.file_uploader("📂 Upload PDF Files", accept_multiple_files=True, type=["pdf"])
        if st.button("Submit & Process"):
            with st.spinner("🤔 Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")

        st.markdown("---")
        st.subheader("💾 Download Processed Text")
        if st.button("⬇️ Download Text File"):
            st.download_button(label="📥 Click to Download", 
                               data="Sample extracted text from PDFs",
                               file_name="Extracted_Text.pdf",
                               mime="text/plain")

if __name__ == "__main__":
    main()