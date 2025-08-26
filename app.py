import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from rag_processor import RAGProcessor
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
import humanize

# Carrega variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Configuração da Autenticação (JWT) ---
# Chave secreta para assinar os tokens. Mude isso para algo seguro em produção!
app.config["JWT_SECRET_KEY"] = "super-secret-key-change-me" 
jwt = JWTManager(app)

# --- Usuário de Exemplo (Em um projeto real, isso viria de um banco de dados) ---
# Para este exemplo, o login é: admin | senha: admin123
users = {
    "admin": "admin123",
    "igorAM":"2257108"
}

# Verifica se a chave da API Google está configurada
if not os.getenv('GOOGLE_API_KEY'):
    raise ValueError("GOOGLE_API_KEY não encontrada no arquivo .env")

# Inicializa o processador RAG
rag_processor = RAGProcessor()

# --- Endpoint de Login ---
@app.route('/login', methods=['POST'])
def login():
    """
    Endpoint para autenticar o usuário e retornar um token de acesso.
    """
    data = request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)

    # Verifica se o usuário e senha correspondem ao nosso usuário de exemplo
    if username in users and users[username] == password:
        # Cria um token de acesso que expira em 1 dia
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)

    return jsonify({"msg": "Usuário ou senha inválidos"}), 401

# --- Endpoints Protegidos ---

@app.route('/upload', methods=['POST'])
@jwt_required() # Protege esta rota
def upload_files():
    # O código desta função permanece o mesmo
    try:
        if 'files' not in request.files:
            return jsonify({"status": "erro", "message": "Nenhum arquivo enviado"}), 400
        files = request.files.getlist('files')
        rag_processor.process_files(files)
        return jsonify({"status": "sucesso", "message": f"{len(files)} arquivo(s) processado(s)."}), 200
    except Exception as e:
        return jsonify({"status": "erro", "message": str(e)}), 500

@app.route('/ask', methods=['POST'])
@jwt_required() # Protege esta rota
def ask_question():
    # O código desta função permanece o mesmo
    try:
        data = request.get_json()
        query = data.get('query')
        if not query:
            return jsonify({"status": "erro", "message": "'query' é obrigatório"}), 400
        answer = rag_processor.generate_answer(query)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"status": "erro", "message": str(e)}), 500

@app.route('/docs/<path:filename>')
@jwt_required() # Protege esta rota
def serve_doc(filename):
    return send_from_directory('docs', filename)

@app.route('/api/documents')
@jwt_required() # Protege esta rota
def list_documents():
    # O código desta função permanece o mesmo
    try:
        docs_path = 'docs'
        # Garante que a pasta 'docs' exista antes de tentar listar os arquivos
        if not os.path.exists(docs_path):
             os.makedirs(docs_path)
        
        files = os.listdir(docs_path)
        document_list = []
        for file in files:
            file_path = os.path.join(docs_path, file)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                file_ext = os.path.splitext(file)[1].replace('.', '').upper()
                document_list.append({
                    "name": os.path.splitext(file)[0].replace('_', ' ').replace('-', ' ').title(),
                    "filename": file,
                    "size": humanize.naturalsize(file_size),
                    "type": file_ext
                })
        return jsonify(document_list)
    except Exception as e:
        return jsonify({"status": "erro", "message": str(e)}), 500

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('vector_store', exist_ok=True)
    os.makedirs('docs', exist_ok=True)
    #app.run(host='0.0.0.0', port=5000, debug=True)