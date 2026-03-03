import streamlit as st
from PIL import Image
import io
from src.services.ai_service import extract_coordinates
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

# Sidebar com Informações e chaves
with st.sidebar:
    st.header("⚙️ Configurações de IA")
    
    ai_provider = st.selectbox("Provedor de IA", ["Gemini", "OpenAI", "DeepSeek"])
    
    if ai_provider == "Gemini":
        model_options = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        default_key = st.secrets.get("GEMINI_API_KEY", "")
    elif ai_provider == "OpenAI":
        model_options = ["gpt-4o", "gpt-4o-mini"]
        default_key = st.secrets.get("OPENAI_API_KEY", "")
    else:
        model_options = ["deepseek-chat", "deepseek-reasoner"]
        default_key = st.secrets.get("DEEPSEEK_API_KEY", "")
        
    selected_model = st.selectbox("Modelo", model_options)
    
    custom_key = st.text_input(
        f"Chave API {ai_provider}", 
        type="password", 
        placeholder="Deixe vazio para usar a chave do sistema",
        help="Sua chave não será salva no servidor."
    )
    
    final_api_key = custom_key if custom_key else default_key
    
    if not final_api_key:
        st.warning(f"⚠️ Nenhuma chave {ai_provider} configurada.")

    st.markdown("---")
    if st.button("🗑️ Limpar Cache da IA", help="Use isso se quiser re-processar o mesmo arquivo."):
        st.cache_data.clear()
        st.toast("Cache limpo!")
        
    st.markdown("---")
    st.markdown("### 📞 Suporte Técnico")
    st.markdown("""
    **Eng. Germano Jorge**
    [Falar no WhatsApp](https://wa.me/5519996243591)
    """)
    st.caption("v1.2 - Multi-AI Support")

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
            st.caption("Nota: Para OpenAI/DeepSeek, PDFs serão processados melhor se convertidos em imagens.")

    with col_action:
        st.markdown("### ⚡ Ações")
        
        if st.button("🚀 Iniciar Processamento", use_container_width=True):
            if not final_api_key:
                st.error("Por favor, informe uma chave API na barra lateral ou configure os segredos do Streamlit.")
            else:
                with st.spinner(f"Analisando com {ai_provider} ({selected_model})..."):
                    processed_content = uploaded_file.getvalue()
                    result_json = extract_coordinates(
                        ai_provider,
                        selected_model,
                        final_api_key,
                        processed_content, 
                        uploaded_file.type
                    )
                    
                    if result_json:
                        st.session_state['extracted_data'] = result_json
                        st.toast("✅ Dados extraídos com sucesso!", icon='🎉')

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

