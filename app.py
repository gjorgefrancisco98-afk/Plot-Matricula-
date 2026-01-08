import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2
import io
import json
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuração da Página
st.set_page_config(
    page_title="AutoCAD Plot Generator - ForAll Engenharia",
    page_icon="📐",
    layout="wide"
)

# Estilização Personalizada (ForAll Engenharia Theme)
st.markdown("""
    <style>
    /* Cores da Marca: Azul #4A6FA5, Verde #22C55E */
    
    /* Alterar cor principal (botões e destaques) */
    div.stButton > button {
        background-color: #22C55E;
        color: white;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #16a34a; /* Verde mais escuro */
        color: white;
    }
    
    /* Header Customizado */
    .header-container {
        display: flex;
        align-items: center;
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #4A6FA5;
    }
    .logo-img {
        max-height: 80px;
        margin-right: 20px;
    }
    .main-title {
        color: #1e293b;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header com Logo da ForAll
col_logo, col_title = st.columns([1, 4])
with col_logo:
    # Usando o logo extraído do site
    st.image("https://www.forallengenharia.com.br/images/logo_original.svg", width=150)
with col_title:
    st.title("Gerador de Matrículas")
    st.markdown("**Soluções ForAll Engenharia**")

st.markdown("---")
st.markdown("Faça upload da matrícula (Imagem ou PDF) para extrair o perímetro e gerar o script do AutoCAD.")

# Configuração da API Key
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("ERRO: Chave da API Gemini não encontrada no secrets.toml")
except Exception as e:
    st.error(f"Erro ao configurar API: {e}")

# Área de Upload
uploaded_file = st.file_uploader("Carregar Matrícula", type=['png', 'jpg', 'jpeg', 'pdf'])

def load_image(uploaded_file):
    """Carrega imagem do upload."""
    if uploaded_file is not None:
        image_data = uploaded_file.getvalue()
        return Image.open(io.BytesIO(image_data))
    return None

import time

def extract_coordinates_from_gemini(file_content, mime_type, model_name="gemini-flash-latest"):
    """Envia o arquivo para a API do Gemini e retorna os dados extraídos."""
    
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
                    st.warning(f"Limite de API atingido. Tentando novamente em {wait_time} segundos... (Tentativa {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            
            st.error(f"Erro na comunicação com a API Gemini: {error_msg}")
            return None
    return None

if uploaded_file:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pré-visualização do Arquivo")
        file_type = uploaded_file.type
        
        # Preparar o arquivo para envio
        processed_file_content = None
        processed_mime_type = None

        if "image" in file_type:
            image = load_image(uploaded_file)
            st.image(image, caption="Matrícula Carregada", use_container_width=True)
            processed_file_content = uploaded_file.getvalue()
            processed_mime_type = file_type
            
        elif "pdf" in file_type:
            st.info("Arquivo PDF carregado. O processamento será feito enviando o arquivo para a IA.")
            # Para PDFs, mandamos o blob direto para o Gemini
            processed_file_content = uploaded_file.getvalue()
            processed_mime_type = "application/pdf"

        process_clicked = st.button("Processar Matrícula", type="primary")

    with col2:
        # Seleção de Modelo (Avançado)
        with st.expander("Gerações e Modelos"):
            model_options = ["gemini-flash-latest", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
            selected_model = st.selectbox("Modelo de IA", model_options, index=0)
    
        if process_clicked:
            if not processed_file_content:
                st.error("ERRO: Nenhum arquivo válido processado.")
            else:
                with st.spinner(f"Analisando documento com IA ({selected_model})..."):
                    result_json = extract_coordinates_from_gemini(processed_file_content, processed_mime_type, selected_model)
                    
                    if result_json:
                        st.success("Dados extraídos com sucesso!")
                        st.subheader("Dados Brutos (JSON)")
                        st.json(result_json)
                        
                        # Guardar no session state para usar nos próximos passos (cálculo e plot)
                        st.session_state['extracted_data'] = result_json


def calculate_polygon(data):
    """Calcula as coordenadas X,Y do polígono a partir dos dados extraídos."""
    points = [(0, 0)] # Começa na origem
    current_x = 0
    current_y = 0
    
    tipo_medida = data.get("tipo_medida", "Azimute")
    
    for segmento in data.get("segmentos", []):
        dist = segmento.get("distancia_metros", 0)
        angulo_obj = segmento.get("angulo", {})
        
        graus = angulo_obj.get("graus", 0)
        minutos = angulo_obj.get("minutos", 0)
        segundos = angulo_obj.get("segundos", 0)
        quadrante = angulo_obj.get("quadrante")
        
        # 1. Converter tudo para graus decimais
        dec = graus + (minutos / 60) + (segundos / 3600)
        
        # 2. Converter para Azimute Universal (0-360) se for Rumo
        azimute_dec = dec
        if tipo_medida == "Rumo" and quadrante:
            q = quadrante.upper().strip()
            if q == 'NE':
                azimute_dec = dec
            elif q == 'SE':
                azimute_dec = 180 - dec
            elif q == 'SW':
                azimute_dec = 180 + dec
            elif q == 'NW':
                azimute_dec = 360 - dec
        
        # 3. Converter Azimute (Norte=0, Horário) para Trigonométrico Python (Leste=0, Anti-horário)
        # Matematica: Trig_Angle = 90 - Azimute
        # Ex: Azimute 90 (Leste) -> 90 - 90 = 0 (Leste Trig)
        # Ex: Azimute 0 (Norte) -> 90 - 0 = 90 (Norte Trig)
        # Ex: Azimute 270 (Oeste) -> 90 - 270 = -180 = 180 (Oeste Trig)
        trig_angle_deg = 90 - azimute_dec
        trig_angle_rad = math.radians(trig_angle_deg)
        
        # Calcular deslocamento
        dx = dist * math.cos(trig_angle_rad)
        dy = dist * math.sin(trig_angle_rad)
        
        current_x += dx
        current_y += dy
        
        points.append((current_x, current_y))
        
    return points

def plot_polygon(points):
    """Gera gráfico do polígono."""
    if not points:
        return None
        
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    
    # Fechar o polígono para o desenho
    x.append(x[0])
    y.append(y[0])
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(x, y, 'b-', linewidth=2)
    ax.fill(x, y, alpha=0.3)
    
    # Ajustar aspecto para não distorcer o terreno
    ax.set_aspect('equal', adjustable='box')
    ax.set_title("Pré-visualização da Geometria")
    ax.grid(True)
    
    return fig

def generate_autocad_script(points):
    """Gera script .scr para o AutoCAD."""
    script = []
    
    # Configurar Unidades
    # UNITS: 2 (Decimal), 2 (Precisão), 1 (Graus/Min/Seg - para input manual seria util, mas aqui mandamos coordenadas), 
    # 2 (Precisão ang), 1 (Clockwise), 90 (Direction North)
def generate_autocad_script(points):
    """Gera script .scr para o AutoCAD com Layers, Cotas e Identificadores (Versão Robusta)."""
    script = []
    
    # Função auxiliar para adicionar comandos seguros
    def add_cmd(cmd):
        script.append(cmd)
    
    # Configuração Inicial (Prefixos _ para universalidade)
    # UNITS
    add_cmd("_UNITS")
    add_cmd("2") # Decimal
    add_cmd("2") # Precision
    add_cmd("1") # Decimal Degrees
    add_cmd("2") # Precision
    add_cmd("0") # East (Default) - Como usamos Coordenadas X,Y calculadas, não importa a base angular do CAD
    add_cmd("N") # No clockwise
    
    # OSMODE
    add_cmd("_OSMODE")
    add_cmd("0")
    
    # STYLE (Estilo de Texto) e.g. "Standard"
    add_cmd("_-STYLE")
    add_cmd("Standard")
    add_cmd("Arial")
    add_cmd("0") # Altura 0 (para definir no comando text)
    add_cmd("1") # Width factor
    add_cmd("0") # Obliquing
    add_cmd("_N") # Backwards No
    add_cmd("_N") # Upside down No
    
    # LAYER PONTOS
    # Formato seguro: Entra no comando, Nova, Nome, Cor, Num, Nome, Set, Nome, Enter para sair
    add_cmd("_-LAYER")
    add_cmd("_N")
    add_cmd("ARQ_PONTOS")
    add_cmd("_C")
    add_cmd("1") # Red
    add_cmd("ARQ_PONTOS")
    add_cmd("_S") # Set current
    add_cmd("ARQ_PONTOS")
    add_cmd("") # Enter para finalizar comando LAYER
    
    # Identificadores de Pontos
    dists = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        d = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        dists.append(d)
    
    avg_dist = sum(dists) / len(dists) if dists else 10
    text_height = max(0.5, avg_dist * 0.02)
    
    for i, p in enumerate(points[:-1]): 
        label = f"P{i+1}"
        add_cmd(f"_TEXT {p[0]:.4f},{p[1]:.4f} {text_height:.4f} 0 {label}")
        add_cmd(f"_POINT {p[0]:.4f},{p[1]:.4f}")

    # LAYER PERIMETRO
    add_cmd("_-LAYER")
    add_cmd("_N")
    add_cmd("ARQ_PERIMETRO")
    add_cmd("_C")
    add_cmd("4") # Cyan
    add_cmd("ARQ_PERIMETRO")
    add_cmd("_S")
    add_cmd("ARQ_PERIMETRO")
    add_cmd("") # Sair do Layer
    
    # Desenhar Polígono
    add_cmd("_PLINE")
    for p in points:
        add_cmd(f"{p[0]:.4f},{p[1]:.4f}")
    add_cmd("C") # Close
    
    # LAYER COTAS
    add_cmd("_-LAYER")
    add_cmd("_N")
    add_cmd("ARQ_COTAS")
    add_cmd("_C")
    add_cmd("2") # Yellow
    add_cmd("ARQ_COTAS")
    add_cmd("_S")
    add_cmd("ARQ_COTAS")
    add_cmd("") # Sair do Layer
    
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2
        
        dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        if 90 < angle_deg <= 270 or -270 <= angle_deg < -90:
             angle_deg += 180
        
        label_dist = f"{dist:.2f}m"
        add_cmd(f"_TEXT {mid_x:.4f},{mid_y:.4f} {text_height:.4f} {angle_deg:.4f} {label_dist}")

    add_cmd("_ZOOM _E") 
    
    return "\n".join(script)

# ... (código anterior da UI até st.session_state['extracted_data'] = result_json)

if 'extracted_data' in st.session_state:
    data = st.session_state['extracted_data']
    
    st.markdown("---")
    st.header("Resultados Processados")
    
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("Geometria Calculada")
        points = calculate_polygon(data)
        fig = plot_polygon(points)
        if fig:
            st.pyplot(fig)
            
    with col_b:
        st.subheader("Script AutoCAD (.scr)")
        script_content = generate_autocad_script(points)
        st.text_area("Copie o código abaixo e cole na linha de comando do AutoCAD:", value=script_content, height=300)
        
        # Botão de download
        st.download_button(
            label="Baixar Script (.scr)",
            data=script_content,
            file_name="desenho_lote.scr",
            mime="text/plain"
        )
# Footer / Sidebar Info
with st.sidebar:
    st.markdown("---")
    st.image("https://www.forallengenharia.com.br/images/logo_original.svg", width=200)
    st.markdown("### Sobre o Desenvolvedor")
    st.markdown("""
    **Eng. Civil Germano Jorge Francisco**
    
    🆔 **CREA:** 506.968.487-8
    
    📱 **WhatsApp:** [(19) 99624 3591](https://wa.me/5519996243591)
    
    📧 **Email:** [contato@forallengenharia.com.br](mailto:contato@forallengenharia.com.br)
    
    🌐 **Site:** [www.forallengenharia.com.br](https://www.forallengenharia.com.br)
    """)
    st.markdown("---")
    st.caption("© 2026 ForAll Engenharia. Todos os direitos reservados.")

