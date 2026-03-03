import google.generativeai as genai
import json
import time
import streamlit as st
from openai import OpenAI

SYSTEM_INSTRUCTION = """
Você é um Engenheiro Civil Sênior especialista em Engenharia Legal e Topografia. Sua tarefa é analisar imagens ou PDFs de matrículas de imóveis e transcreverções (títulos de propriedade) para extrair os dados técnicos do perímetro do imóvel.

OBJETIVO:
Identificar a descrição do perímetro (caminhamento) e extrair os dados de cada segmento para formar um polígono fechado.

REGRAS DE EXTRAÇÃO:
1. Ignore preâmbulos, históricos de proprietários e averbações que não se refiram às medidas atuais do terreno. Foque apenas na descrição das divisas.
2. Identifique se a descrição utiliza "Rumo" (com quadrantes: NE, NW, SE, SW) ou "Azimute" (0° a 360°).
3. Identifique a unidade de medida (geralmente metros).
4. Se houver menção a raio ou curva, tente aproximar para uma corda (linha reta) ou indique que é uma curva nos comentários, mas priorize a extração da corda se disponível.
5. ATENÇÃO: Textos de cartório frequentemente escrevem números por extenso ou usam abreviações. Converta tudo para numérico.

FORMATO DE SAÍDA (OBRIGATÓRIO):
Retorne APENAS um objeto JSON válido contendo uma lista de segmentos. Não adicione texto antes ou depois do JSON.

O JSON deve seguir esta estrutura estrita:
{
  "tipo_medida": "Rumo" ou "Azimute",
  "segmentos": [
    {
      "ordem": 1,
      "descricao_original": "trecho do texto original para conferencia",
      "distancia_metros": 00.00,
      "angulo": {
        "graus": 0,
        "minutos": 0,
        "segundos": 0,
        "quadrante": "NE/NW/SE/SW ou null se for azimute"
      },
      "confrontante": "Nome do vizinho ou rua (opcional)"
    }
  ]
}
"""

def extract_with_gemini(file_content, mime_type, model_name, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model_name, system_instruction=SYSTEM_INSTRUCTION)
    generation_config = genai.GenerationConfig(response_mime_type="application/json")
    
    response = model.generate_content(
        [{"mime_type": mime_type, "data": file_content}, "Extraia as coordenadas desta matrícula."],
        generation_config=generation_config
    )
    return json.loads(response.text)

def extract_with_openai_compatible(file_content, mime_type, model_name, api_key, base_url=None):
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # Nota: OpenAI requer passar imagem em base64 se for imagem, ou processar PDF via Assistants/Files se for PDF.
    # Para simplicidade e compatibilidade direta (DeepSeek não processa arquivos nativamente via API simples de chat sem vision),
    # assumiremos que o usuário enviará imagens. PDFs terão que ser convertidos ou extraídos como texto se possível.
    # No entanto, o Gemini Flash 2.0 é disparado superior para OCR de PDF.
    
    # Implementação simplificada para demonstração de suporte a múltiplos provedores
    # Idealmente, converteríamos PDF para imagem aqui se o provedor não suportar PDF nativo.
    
    import base64
    base64_image = base64.b64encode(file_content).decode('utf-8')
    
    prompt = f"{SYSTEM_INSTRUCTION}\n\nExtraia as coordenadas desta matrícula de imóvel enviada em anexo."
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def extract_coordinates(provider, model_name, api_key, file_content, mime_type):
    """Orquestrador de extração multi-provedor."""
    try:
        if provider == "Gemini":
            return extract_with_gemini(file_content, mime_type, model_name, api_key)
        elif provider == "OpenAI":
            return extract_with_openai_compatible(file_content, mime_type, model_name, api_key)
        elif provider == "DeepSeek":
            # DeepSeek usa a API compatível da OpenAI
            return extract_with_openai_compatible(file_content, mime_type, model_name, api_key, base_url="https://api.deepseek.com")
    except Exception as e:
        st.error(f"Erro no provedor {provider}: {str(e)}")
        return None
