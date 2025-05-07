import streamlit as st
from graphviz import Digraph
import requests
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

# --- Configuração Inicial --- #
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# --- Funções de Processamento de Texto --- #
def extrair_texto(file):
    """Extrai texto de arquivos PDF, DOCX ou TXT."""
    try:
        if file.type == "application/pdf":
            pdf = PdfReader(file)
            return "".join(page.extract_text() or "" for page in pdf.pages)
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif file.type == "text/plain":
            return file.read().decode("utf-8")
        return ""
    except Exception as e:
        st.error(f"Erro ao extrair texto: {str(e)}")
        return ""

def gerar_proposicoes_medicas(objetivos, referencias, conteudo):
    """Gera relações conceituais médicas usando DeepSeek API."""
    if not conteudo.strip():
        return "Erro: Nenhum conteúdo válido para análise"
    
    prompt = f"""
    🩺 VOCÊ É UM ASSISTENTE DE MAPEAMENTO CONCEITUAL MÉDICO. Siga EXATAMENTE estas regras:

    1. ANALISE o conteúdo e IDENTIFIQUE conceitos médicos como:
       - Lesões celulares, hipóxia, apoptose, inflamação, necrose, hipertrofia
       - Termos técnicos: ROS, estresse do RE, metaplasia, quimiotaxina

    2. GERE RELAÇÕES no formato: `origem -> tipo_relacao -> destino` (uma por linha)
       Exemplos obrigatórios:
       lesão celular -> pode_ser -> reversível
       hipóxia -> causa -> estresse oxidativo
       inflamação -> caracteriza_se_por -> vasodilatação

    3. HIERARQUIA: Organize do GERAL para ESPECÍFICO
       Ex: sistema -> contém -> órgão

    4. USE APENAS estes tipos de relações:
       - causa, leva_a, pode_ser, depende_de, caracteriza_se_por, contém

    --- OBJETIVOS ---
    {objetivos[:1000]}

    --- REFERÊNCIAS ---
    {referencias[:1000]}

    --- CONTEÚDO ---
    {conteudo[:5000]}
    """

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            "https://api.deepseek.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"Erro na API (Status {response.status_code}): {response.text[:500]}"
    except requests.exceptions.RequestException as e:
        return f"Erro de conexão: {str(e)}"
    except Exception as e:
        return f"Erro inesperado: {str(e)}"

def gerar_mapa_conceitual(proposicoes):
    """Cria visualização do mapa conceitual com Graphviz."""
    grafo = Digraph(
        graph_attr={
            "rankdir": "TB",
            "bgcolor": "#f0f8ff",
            "fontname": "Arial",
            "compound": "true"
        },
        node_attr={
            "shape": "rectangle",
            "style": "filled,rounded",
            "fillcolor": "#e6f3ff",
            "fontname": "Arial",
            "margin": "0.2,0.1"
        },
        edge_attr={
            "fontname": "Arial",
            "fontsize": "10"
        }
    )

    if not proposicoes or "->" not in proposicoes:
        return grafo

    linhas = [linha.strip() for linha in proposicoes.split("\n") if "->" in linha]
    
    for linha in linhas:
        partes = [p.strip() for p in linha.split("->")]
        if len(partes) >= 2:
            origem = partes[0]
            destino = partes[-1]
            relacao = " ".join(partes[1:-1]) if len(partes) > 2 else "relacionado_a"
            
            # Estilo baseado no tipo de relação
            if "causa" in relacao.lower():
                grafo.edge(origem, destino, label=relacao, color="#d62728", fontcolor="#d62728")
            elif "pode_ser" in relacao.lower():
                grafo.edge(origem, destino, label=relacao, color="#2ca02c", fontcolor="#2ca02c")
            else:
                grafo.edge(origem, destino, label=relacao, color="#2b5876", fontcolor="#2b5876")
    
    return grafo

# --- Interface Streamlit --- #
def main():
    st.set_page_config(
        page_title="Mapa Conceitual Médico",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar com configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        api_key = st.text_input("Chave API DeepSeek (opcional)", type="password", value=DEEPSEEK_API_KEY or "")
        if api_key:
            os.environ["DEEPSEEK_API_KEY"] = api_key
        st.markdown("---")
        st.markdown("### Como usar:")
        st.markdown("1. Insira objetivos e referências")
        st.markdown("2. Faça upload de arquivos (PDF/DOCX/TXT)")
        st.markdown("3. Clique em 'Gerar Mapa'")
        st.markdown("---")
        st.markdown("🛠️ [Reportar problema](https://github.com)")

    # Main content
    st.title("🩺 Mapa Conceitual Médico com IA")
    
    # Entradas do usuário
    tab1, tab2 = st.tabs(["📝 Digitar Texto", "📂 Upload de Arquivos"])
    
    with tab1:
        objetivos = st.text_area("Objetivos de Estudo*", height=100, 
                              placeholder="Ex: Compreender os mecanismos de lesão celular")
        referencias = st.text_area("Referências Bibliográficas", height=100,
                                 placeholder="Ex: Robbins, Patologia Básica, 10ed")
        texto_manual = st.text_area("Conteúdo para Análise", height=200,
                                  placeholder="Cole aqui o texto médico...")
    
    with tab2:
        arquivos = st.file_uploader("Selecione arquivos (PDF, DOCX, TXT)", 
                                  type=["pdf", "docx", "txt"], 
                                  accept_multiple_files=True)
    
    # Processamento
    if st.button("🔄 Gerar Mapa Conceitual", type="primary", use_container_width=True):
        if not objetivos.strip():
            st.warning("Por favor, insira pelo menos os objetivos de estudo!")
            st.stop()
        
        conteudo_total = ""
        
        # Processa uploads de arquivos
        if arquivos:
            progress_bar = st.progress(0)
            for i, arquivo in enumerate(arquivos):
                conteudo_total += extrair_texto(arquivo) + "\n\n"
                progress_bar.progress((i + 1) / len(arquivos))
            progress_bar.empty()
        
        # Adiciona texto manual se fornecido
        if texto_manual.strip():
            conteudo_total += texto_manual + "\n\n"
        
        if not conteudo_total.strip():
            st.warning("Nenhum conteúdo válido para análise. Faça upload de arquivos ou insira texto manual.")
            st.stop()
        
        # Mostra pré-visualização do conteúdo
        with st.expander("🔍 Visualizar conteúdo para análise"):
            st.text(conteudo_total[:3000] + ("..." if len(conteudo_total) > 3000 else ""))
        
        # Chama a API
        with st.spinner("🔬 Analisando conteúdo com IA médica..."):
            proposicoes = gerar_proposicoes_medicas(objetivos, referencias, conteudo_total)
        
        # Exibe resultados
        if proposicoes.startswith("Erro"):
            st.error(proposicoes)
        else:
            st.success("✅ Mapa conceitual gerado com sucesso!")
            
            # Exibe as relações em formato de texto
            with st.expander("📝 Relações Conceituais Identificadas"):
                st.code(proposicoes)
            
            # Gera e exibe o mapa
            st.subheader("🗺️ Visualização do Mapa Conceitual")
            grafo = gerar_mapa_conceitual(proposicoes)
            st.graphviz_chart(grafo, use_container_width=True)
            
            # Opções de exportação
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Baixar Mapa (DOT)",
                    data=grafo.source,
                    file_name="mapa_conceitual.dot",
                    mime="text/plain",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    label="📋 Copiar Relações",
                    data=proposicoes,
                    file_name="relacoes.txt",
                    mime="text/plain",
                    use_container_width=True
                )

    # Exemplo médico
    with st.expander("🧪 Exemplo Prático - Lesão Celular"):
        st.markdown("""
        **Objetivo**: Compreender os mecanismos de lesão celular  
        
        **Conteúdo**:  
        Lesões celulares podem ser reversíveis (ex: esteatose) ou irreversíveis (necrose).  
        A hipóxia, causada por isquemia, leva à produção de ROS e dano mitocondrial.  
        A apoptose é uma morte celular programada, diferente da necrose por coagulação.
        
        **Saída Esperada**:  
        ```
        lesão celular -> pode_ser -> reversível  
        lesão celular -> pode_ser -> irreversível  
        hipóxia -> causa -> produção de ROS  
        hipóxia -> leva_a -> dano mitocondrial  
        apoptose -> diferente_de -> necrose  
        ```
        """)

if __name__ == "__main__":
    main()