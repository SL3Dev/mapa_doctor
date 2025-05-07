import openai
import os
from dotenv import load_dotenv
from google.cloud import aiplatform

load_dotenv()

def gerar_resumo_e_proposicoes(objetivos, referencias, conteudo_arquivos):
    client = aiplatform.gapic.PredictionServiceClient()
    project_id = "your_project_id"
    endpoint_id = "your_endpoint_id"
    location = "us-central1"
    api_key = os.getenv("GOOGLE_API_KEY")

    prompt = f"""
    Você é um assistente educacional. Com base nos objetivos de estudo, nas referências e no conteúdo fornecido, gere:

    1. Um **resumo esquematizado** com os principais tópicos abordados.
    2. Uma **lista de proposições hierárquicas** para construção de um mapa conceitual.

    ---  
    **Objetivos de Estudo:**  
    {objetivos}

    ---  
    **Referências:**  
    {referencias}

    ---  
    **Conteúdo dos Arquivos:**  
    {conteudo_arquivos[:3000]}
    """

    response = client.predict(
        endpoint=f"projects/{project_id}/locations/{location}/endpoints/{endpoint_id}",
        instances=[{"content": prompt}],
        parameters={"temperature": 0.7, "max_tokens": 1000},
        api_key=api_key
    )

    return response.predictions[0]['content']
