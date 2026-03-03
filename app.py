import streamlit as st
from PIL import Image
import io
from src.services.gemini_service import extract_coordinates_from_gemini
from src.utils.geometry_utils import calculate_polygon, plot_polygon
from src.utils.cad_utils import generate_cad_script

# Configuração da Página
st.set_page_config(
    page_title="Gerador de Matrícula - ForAll Engenharia",
    page_icon="📐",
    layout="wide"
)

# Estilização Personalizada
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #22C55E;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #16a34a;
        border-color: #16a34a;
    }
    .main-header {
        background-color: #f8fafc;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #4A6FA5;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Layout do Cabeçalho
with st.container():
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.image("https://www.forallengenharia.com.br/images/logo_original.svg", width=160)
    with col_title:
        st.title("Calculadora de Perímetro")
        st.subheader("ForAll Engenharia - Inteligência Legal")

st.info("💡 Carregue a matrícula (PDF ou Imagem) para gerar automaticamente o script de desenho CAD.")

# Sidebar com Informações
with st.sidebar:
    st.header("⚙️ Configurações")
    model_options = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-flash-latest"]
    selected_model = st.selectbox("Modelo de IA", model_options, help="Modelos mais novos costumam ser mais precisos.")
    
    st.markdown("---")
    st.markdown("### 📞 Suporte Técnico")
    st.markdown("""
    **Eng. Germano Jorge**
    [Falar no WhatsApp](https://wa.me/5519996243591)
    """)
    st.caption("v1.1 - Orchestrated Build")

# Área Principal
uploaded_file = st.file_uploader("Selecione o arquivo da matrícula", type=['png', 'jpg', 'jpeg', 'pdf'])

if uploaded_file:
    col_preview, col_action = st.columns([1, 1])
    
    with col_preview:
        st.markdown("### 📄 Visualização")
        if "image" in uploaded_file.type:
            st.image(uploaded_file, use_container_width=True)
        else:
            st.success(f"PDF carregado: {uploaded_file.name}")
            st.caption("O conteúdo será processado pela IA para extração de dados.")

    with col_action:
        st.markdown("### ⚡ Ações")
        if st.button("🚀 Iniciar Processamento", use_container_width=True):
            with st.spinner("Analisando matrícula... Aguarde."):
                processed_content = uploaded_file.getvalue()
                result_json = extract_coordinates_from_gemini(
                    processed_content, 
                    uploaded_file.type, 
                    selected_model
                )
                
                if result_json:
                    st.session_state['extracted_data'] = result_json
                    st.toast("✅ Dados extraídos com sucesso!", icon='🎉')
                else:
                    st.error("Ops! Não conseguimos extrair os dados. Tente novamente ou verifique a qualidade do arquivo.")

# Resultados
if 'extracted_data' in st.session_state:
    data = st.session_state['extracted_data']
    st.markdown("---")
    st.header("📊 Resultados da Análise")
    
    tab1, tab2, tab3 = st.tabs(["🗺️ Geometria", "📜 Dados Extraídos", "💻 AutoCAD / Ares"])
    
    with tab1:
        points = calculate_polygon(data)
        fig = plot_polygon(points)
        if fig:
            st.pyplot(fig)
            st.caption("Representação visual simplificada do perímetro.")
        else:
            st.warning("Não foi possível gerar a geometria com os dados fornecidos.")

    with tab2:
        st.json(data)
        
    with tab3:
        st.subheader("Script de Desenho")
        st.markdown("Copie o código abaixo ou baixe o arquivo `.scr` e arraste para dentro do seu CAD.")
        
        # Gerar scripts para ambos (podemos futuramente diferenciar se necessário)
        script_content = generate_cad_script(points)
        
        st.code(script_content, language="bash")
        
        st.download_button(
            label="📥 Baixar Script (.scr)",
            data=script_content,
            file_name=f"matricula_{uploaded_file.name if uploaded_file else 'lote'}.scr",
            mime="text/plain",
            use_container_width=True
        )

