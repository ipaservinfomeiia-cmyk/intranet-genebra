import os
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

class RAGProcessor:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=self.api_key)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=self.api_key
        )
        
        self.vector_store_path = "vector_store"
        # Inicializa ou carrega o ChromaDB a partir do diretório
        self.vector_store = Chroma(
            persist_directory=self.vector_store_path,
            embedding_function=self.embeddings
        )
    
    def process_files(self, files: List) -> None:
        saved_files = self._save_uploaded_files(files)
        
        documents = []
        with ThreadPoolExecutor() as executor:
            results = executor.map(self._load_document, saved_files)
            for result in results:
                documents.extend(result)
        
        if not documents:
            self._cleanup_uploaded_files(saved_files)
            return

        chunks = self.text_splitter.split_documents(documents)
        
        # Adiciona os novos documentos e persiste as alterações
        self.vector_store.add_documents(chunks)
        self.vector_store.persist()
        
        self._cleanup_uploaded_files(saved_files)
    
    def generate_answer(self, query: str) -> str:
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 4})
        
        prompt_template = """
        Você é um assistente útil da Escola Genebra. Responda à pergunta do usuário estritamente com base no seguinte contexto. 
        Se o contexto não contiver a resposta, diga que não encontrou a informação na base de conhecimento da escola.
        Não invente informações.
        
        Pergunta: {question}
        
        Contexto: {context}
        
        Resposta:
        """
        
        prompt = PromptTemplate.from_template(prompt_template)
        llm = genai.GenerativeModel('gemini-pro')

        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm.generate_content
        )

        response = rag_chain.invoke(query)
        
        try:
            return response.text
        except AttributeError:
             return "Ocorreu um erro ao formatar a resposta da IA."

    def _save_uploaded_files(self, files: List) -> List[str]:
        saved_paths = []
        os.makedirs('uploads', exist_ok=True)
        for file in files:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            saved_paths.append(file_path)
        return saved_paths
    
    def _load_document(self, file_path: str) -> List[Document]:
        file_ext = Path(file_path).suffix.lower()
        try:
            if file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_ext == '.docx':
                loader = Docx2txtLoader(file_path)
            elif file_ext == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                return []
            return loader.load()
        except Exception as e:
            print(f"Erro ao processar arquivo {file_path}: {str(e)}")
            return []
    
    def _cleanup_uploaded_files(self, file_paths: List[str]) -> None:
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erro ao remover arquivo temporário {file_path}: {str(e)}")