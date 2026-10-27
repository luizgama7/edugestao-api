import os
import pymongo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="EduGestão IA API")

# Libera o acesso para que o aplicativo no Netlify/Telemóvel consulte esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# String de Conexão com a sua conta do MongoDB Atlas
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://mr_gama_jr:SUA_SENHA_AQUI@gama.vfnpqze.mongodb.net/edugestao_db?retryWrites=true&w=majority",
)

client = pymongo.MongoClient(MONGO_URI)
db = client["edugestao_db"]
collection = db["alunos"]


# Estrutura do Aluno compatível com Pydantic v2
class Aluno(BaseModel):
    name: str
    subject: str
    media: float
    freq: float
    atrasos: int
    ocorrencias: int
    risk: str = "Pendente"
    status: str = "Pendente"
    note: str = ""


# Algoritmo de Inteligência Artificial do TCC UNIVESP
def calcular_risco(freq: float, media: float, atrasos: int, ocorrencias: int) -> str:
    score = 0
    if freq < 70:
        score += 40
    elif freq < 75:
        score += 20

    if media < 5.0:
        score += 35
    elif media < 6.5:
        score += 15

    if ocorrencias >= 3:
        score += 20
    elif ocorrencias >= 1:
        score += 10

    if atrasos > 5:
        score += 10

    if score >= 45:
        return "Alto"
    if score >= 20:
        return "Médio"
    return "Baixo"


# Rota 1: Listar todos os alunos cadastrados no banco de dados
@app.get("/alunos")
def listar_alunos():
    alunos = list(collection.find({}, {"_id": 0}))
    return alunos


# Rota 2: Cadastrar um novo aluno no MongoDB Atlas
@app.post("/alunos")
def criar_aluno(aluno: Aluno):
    # Compatibilidade com Pydantic v2
    aluno_dict = (
        aluno.model_dump() if hasattr(aluno, "model_dump") else aluno.dict()
    )
    aluno_dict["risk"] = calcular_risco(
        aluno.freq, aluno.media, aluno.atrasos, aluno.ocorrencias
    )
    aluno_dict["id"] = str(collection.count_documents({}) + 1)
    collection.insert_one(aluno_dict)
    # Remove _id para envio na resposta JSON
    if "_id" in aluno_dict:
        del aluno_dict["_id"]
    return {"status": "sucesso", "aluno": aluno_dict}


# Rota 3: Registrar parecer pedagógico e atualizar status
@app.put("/alunos/{aluno_id}")
def atualizar_intervencao(aluno_id: str, dados: dict):
    collection.update_one(
        {"id": aluno_id},
        {
            "$set": {
                "note": dados.get("note", ""),
                "status": "Em Acompanhamento",
            }
        },
    )
    return {"status": "atualizado"}