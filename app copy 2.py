import openai
import os
from dotenv import load_dotenv
import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
from graphviz import Digraph 

# Carrega a chave da API do OpenAI
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Função principal de geração de resumo e proposições
def gerar_resumo_e_proposicoes(objetivos, referencias, conteudo_arquivos):
    prompt = f"""
Você é um assistente educacional. Com base nos objetivos de estudo, nas referências e no conteúdo fornecido, gere:

1. Um **resumo esquematizado** com os principais tópicos abordados.
2. Uma **lista de proposições hierárquicas** no formato: conceito1 -> conceito2.

---
**Objetivos de Estudo:**  
{objetivos}

---
**Referências:**  
{referencias}

---
**Conteúdo dos Arquivos:**  
{conteudo_arquivos[:3000]}  # Limita tamanho da entrada
"""
    resposta = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    return resposta.choices[0].message.content.strip()

# Função para extrair texto dos arquivos
def extrair_texto(file):
    if file.type == "application/pdf":
        pdf = PdfReader(file)
        return "".join(page.extract_text() or "" for page in pdf.pages)

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif file.type == "text/plain":
        return file.read().decode("utf-8")

    return ""

# Função para gerar grafo a partir das proposições
def gerar_grafo(proposicoes_texto):
    grafo = Digraph()
    linhas = proposicoes_texto.split("\n")
    for linha in linhas:
        if "->" in linha:
            partes = linha.split("->")
            if len(partes) == 2:
                origem = partes[0].strip()
                destino = partes[1].strip()
                grafo.edge(origem, destino)
    return grafo

# Interface com Streamlit
st.set_page_config(page_title="Mapa Conceitual com IA", layout="wide")
st.title("🧠 Gerador de Mapa Conceitual com IA")

st.header("📌 Objetivos de Estudo")
objetivos = st.text_area("Digite ou cole aqui os objetivos de estudo:", height=150)

st.header("📚 Referências Bibliográficas")
referencias = st.text_area("Cole aqui as referências (ex: autor, título, ano)...", height=150)

st.header("📤 Upload de Arquivos")
uploaded_files = st.file_uploader("Você pode fazer upload de arquivos (.pdf, .docx, .txt)", 
                                   type=["pdf", "docx", "txt"], accept_multiple_files=True)

conteudo_arquivos = ""
if uploaded_files:
    st.subheader("📄 Conteúdo extraído dos arquivos:")
    for file in uploaded_files:
        texto = extrair_texto(file)
        conteudo_arquivos += texto + "\n"
        with st.expander(f"Visualizar conteúdo de: {file.name}"):
            st.write(texto[:3000])  # Limita visualização

if st.button("➡️ Processar com IA"):
    with st.spinner("Processando com inteligência artificial..."):
        resposta_ia = gerar_resumo_e_proposicoes(objetivos, referencias, conteudo_arquivos)

    st.success("IA finalizou o processamento!")
    st.subheader("📑 Resultado da IA")
    st.markdown(resposta_ia)

    st.subheader("🗺️ Visualização do Mapa Conceitual")

    if "->" in resposta_ia:
        grafo = gerar_grafo(resposta_ia)
        st.graphviz_chart(grafo)
    else:
        st.info("Nenhuma proposição hierárquica encontrada no formato esperado.")
