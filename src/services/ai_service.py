import google.generativeai as genai
import json
import time
import streamlit as st
import io
import base64
from openai import OpenAI
import PyPDF2

SYSTEM_INSTRUCTION = """
Você é um Engenheiro Civil Sênior especialista em Engenharia Legal e Topografia. Sua tarefa é analisar a descrição de uma matrícula de imóvel e extrair os dados técnicos do perímetro.

OBJETIVO:
Identificar a descrição do perímetro (caminhamento) e extrair os dados de cada segmento para formar um polígono fechado.

REGRAS DE EXTRAÇÃO:
1. Ignore preâmbulos e averbações irrelevantes. Foque na descrição das divisas.
2. Identifique se usa "Rumo" ou "Azimute".
3. Converta textos para numérico.

FORMATO DE SAÍDA (OBRIGATÓRIO):
Retorne APENAS um objeto JSON válido.
{
  "tipo_medida": "Rumo" ou "Azimute",
  "segmentos": [
    {
      "ordem": 1,
      "descricao_original": "texto original",
      "distancia_metros": 00.00,
      "angulo": {"graus": 0, "minutos": 0, "segundos": 0, "quadrante": "NE/NW/SE/SW ou null"}
    }
  ]
}
"""

def extract_text_from_pdf(file_content):
    """Extrai texto de um PDF usando PyPDF2."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Erro ao extrair texto do PDF: {str(e)}"

def extract_with_gemini(file_content, mime_type, model_name, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name, system_instruction=SYSTEM_INSTRUCTION)
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        
        response = model.generate_content(
            [{"mime_type": mime_type, "data": file_content}, "Extraia as coordenadas desta matrícula."],
            generation_config=generation_config
        )
        return json.loads(response.text)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            st.error("🚫 Limite de cota do Gemini atingido. Aguarde um momento ou use outro provedor/chave.")
        else:
            st.error(f"Erro no Gemini: {error_str}")
        return None

def extract_with_openai_compatible(file_content, mime_type, model_name, api_key, provider_name, base_url=None):
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    content_list = [{"type": "text", "text": f"{SYSTEM_INSTRUCTION}\n\nAnalise esta matrícula e extraia o JSON conforme o formato."}]
    
    if "pdf" in mime_type:
        text_content = extract_text_from_pdf(file_content)
        content_list.append({"type": "text", "text": f"CONTEÚDO DO PDF:\n{text_content}"})
    else:
        # Se for imagem
        if provider_name == "DeepSeek":
            st.error("⚠️ O DeepSeek não suporta análise direta de imagens nesta versão. Converta para PDF (texto) ou use Gemini/OpenAI.")
            return None
            
        base64_image = base64.b64encode(file_content).decode('utf-8')
        content_list.append({
            "type": "image_url", 
            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
        })
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": content_list}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str:
            st.error(f"🚫 Limite de cota do {provider_name} atingido. Verifique seu plano e saldo.")
        else:
            st.error(f"Erro no {provider_name}: {error_str}")
        return None

@st.cache_data(show_spinner=False)
def extract_coordinates(provider, model_name, api_key, file_content, mime_type):
    """Orquestrador de extração multi-provedor com cache para evitar excesso de requisições."""
    try:
        if provider == "Gemini":
            return extract_with_gemini(file_content, mime_type, model_name, api_key)
        elif provider == "OpenAI":
            return extract_with_openai_compatible(file_content, mime_type, model_name, api_key, "OpenAI")
        elif provider == "DeepSeek":
            return extract_with_openai_compatible(file_content, mime_type, model_name, api_key, "DeepSeek", base_url="https://api.deepseek.com")
    except Exception as e:
        if "429" not in str(e):
            st.error(f"Erro no processamento ({provider}): {str(e)}")
        return None
