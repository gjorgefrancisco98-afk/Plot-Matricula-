# Gerador de Desenhos AutoCAD com IA

Este aplicativo utiliza Inteligência Artificial (Google Gemini) para processar imagens e PDFs de matrículas de imóveis, extraindo automaticamente as coordenadas e gerando scripts de desenho para o AutoCAD.

## Funcionalidades
- 📤 Upload de imagens (JPG, PNG) e PDF.
- 🧠 Extração inteligente de rumos, distâncias e quadrantes.
- 📐 Pré-visualização do polígono no navegador.
- 🏗️ Geração de script `.scr` para AutoCAD com:
    - Layers separados (Perímetro, Pontos, Cotas/Texto).
    - Unidades configuradas.
    - Identificação de vértices.

## Como Executar Localmente
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o app:
   ```bash
   streamlit run app.py
   ```

## Deploy
Este projeto está pronto para rodar no [Streamlit Cloud](https://streamlit.io/cloud).
Ao configurar, adicione sua chave de API nos "Secrets" do Streamlit Cloud.
