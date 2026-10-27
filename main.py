import os
from urllib.parse import quote_plus
import pymongo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="EduGestão IA API")

# Libera o acesso CORS para o Netlify/Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# String de Conexão com tratamento de caracteres especiais
MONGO_URI = os.getenv("MONGO_URI", "")

if not MONGO_URI:
    usuario = "mr_gama_jr"
    senha_trata = quote_plus("6348Seg@")
    MONGO_URI = f"mongodb+srv://{usuario}:{senha_trata}@gama.vfnpqze.mongodb.net/edugestao_db?retryWrites=true&w=majority"

client = pymongo.MongoClient(MONGO_URI)
db = client["edugestao_db"]
collection = db["alunos"]

# Lista de alunos para carga inicial caso o banco esteja vazio
ALUNOS_INICIAIS = [
    {"id": "1", "name": "Marcos Henrique Higashi", "subject": "Engenharia da Computação", "media": 8.5, "freq": 92.0, "atrasos": 1, "ocorrencias": 0, "risk": "Baixo", "status": "Pendente", "note": ""},
    {"id": "2", "name": "Reginaldo Egashira", "subject": "Sistemas de Informação", "media": 7.2, "freq": 85.0, "atrasos": 2, "ocorrencias": 0, "risk": "Baixo", "status": "Pendente", "note": ""},
    {"id": "3", "name": "Pedro Henrique Faria Cruz", "subject": "Algoritmos e Estrutura de Dados", "media": 4.2, "freq": 65.0, "atrasos": 8, "ocorrencias": 3, "risk": "Alto", "status": "Pendente", "note": ""},
    {"id": "4", "name": "Danilo Felix Portugal", "subject": "Matemática Discreta", "media": 5.9, "freq": 78.0, "atrasos": 3, "ocorrencias": 1, "risk": "Médio", "status": "Pendente", "note": ""},
    {"id": "5", "name": "Edson Luiz Nascimento", "subject": "Engenharia da Computação", "media": 7.8, "freq": 88.0, "atrasos": 2, "ocorrencias": 0, "risk": "Baixo", "status": "Pendente", "note": ""},
    {"id": "6", "name": "João Veríssimo Ferreira Silva", "subject": "Sistemas de Informação", "media": 3.8, "freq": 58.0, "atrasos": 12, "ocorrencias": 4, "risk": "Alto", "status": "Pendente", "note": ""},
    {"id": "7", "name": "Luiz Silva Gama Júnior", "subject": "Algoritmos e Estrutura de Dados", "media": 9.1, "freq": 96.0, "atrasos": 0, "ocorrencias": 0, "risk": "Baixo", "status": "Pendente", "note": ""},
    {"id": "8", "name": "Pedro Henrique Mendes dos Santos", "subject": "Matemática Discreta", "media": 4.8, "freq": 71.0, "atrasos": 6, "ocorrencias": 2, "risk": "Alto", "status": "Pendente", "note": ""}
]

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

@app.get("/alunos")
def listar_alunos():
    # Se a coleção estiver vazia no MongoDB, insere os 8 alunos de exemplo
    if collection.count_documents({}) == 0:
        collection.insert_many(ALUNOS_INICIAIS)
    alunos = list(collection.find({}, {"_id": 0}))
    return alunos

@app.post("/alunos")
def criar_aluno(aluno: Aluno):
    aluno_dict = aluno.model_dump() if hasattr(aluno, "model_dump") else aluno.dict()
    aluno_dict["risk"] = calcular_risco(aluno.freq, aluno.media, aluno.atrasos, aluno.ocorrencias)
    aluno_dict["id"] = str(collection.count_documents({}) + 1)
    collection.insert_one(aluno_dict)
    if "_id" in aluno_dict:
        del aluno_dict["_id"]
    return {"status": "sucesso", "aluno": aluno_dict}

@app.put("/alunos/{aluno_id}")
def atualizar_intervencao(aluno_id: str, dados: dict):
    collection.update_one(
        {"id": aluno_id},
        {"$set": {"note": dados.get("note", ""), "status": "Em Acompanhamento"}}
    )
    return {"status": "atualizado"}