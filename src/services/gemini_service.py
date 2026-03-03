import google.generativeai as genai
import json
import time
import streamlit as st

def extract_coordinates_from_gemini(file_content, mime_type, model_name="gemini-flash-latest"):
    """Envia o arquivo para a API do Gemini e retorna os dados extraídos."""
    
    # Configuração da API Key (Deve ser injetada ou pega do Streamlit secrets)
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        else:
            raise ValueError("Chave da API Gemini não encontrada no secrets.toml")
    except Exception as e:
        st.error(f"Erro ao configurar API: {e}")
        return None

    system_instruction = """
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

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction
    )

    generation_config = genai.GenerationConfig(response_mime_type="application/json")
    
    # Retry logic (3 tentativas com espera de 10s)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                [
                    {"mime_type": mime_type, "data": file_content},
                    "Extraia as coordenadas desta matrícula conforme as instruções."
                ],
                generation_config=generation_config
            )
            return json.loads(response.text)
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Quota" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    # Usando st.toast em vez de warning direto na UI principal durante o loop
                    st.toast(f"⏳ Limite atingido. Tentativa {attempt + 1}/{max_retries} em {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            
            # Encapsulando erro de forma amigável
            st.error(f"Não conseguimos processar o arquivo agora. Erro técnico: {error_msg}")
            return None
    return None
