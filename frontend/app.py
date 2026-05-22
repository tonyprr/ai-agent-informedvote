import streamlit as st
import requests
import uuid

# Backend configuration
BACKEND_URL = "http://127.0.0.1:8000"

# Inject Tailwind CSS via CDN and Premium Custom Styles
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<style>
    /* Custom adjustments for Streamlit with Tailwind */
    .stApp {
        background-color: #000000;
    }
    .source-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        background-color: #e2e8f0;
        color: #475569;
        margin-right: 0.5rem;
        margin-top: 0.5rem;
    }
    
    /* Assistant Chat Message styling: Celeste minimalista muy claro con texto negro */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]),
    div[data-testid="stChatMessage"]:has(img[alt="assistant avatar"]),
    div[data-testid="stChatMessage"][aria-label="Chat message from assistant"] {
        background-color: #f0f9ff !important; /* Celeste muy claro */
        border: 1px solid #bae6fd !important; /* Borde celeste suave */
        border-radius: 12px !important;
        margin-bottom: 12px;
        padding: 12px !important;
    }
    
    /* Force black text for assistant messages */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) *,
    div[data-testid="stChatMessage"]:has(img[alt="assistant avatar"]) *,
    div[data-testid="stChatMessage"][aria-label="Chat message from assistant"] * {
        color: #0f172a !important;
    }
    
    /* User Chat Message Avatar: Fondo rojo minimalista y claro */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageAvatar"],
    div[data-testid="stChatMessage"]:has(img[alt="user avatar"]) div[data-testid="stChatMessageAvatar"],
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] div[data-testid="stChatMessageAvatar"] {
        background-color: #fee2e2 !important; /* Rojo claro */
        border: 1px solid #fca5a5 !important; /* Borde rojo suave */
        border-radius: 8px !important; /* Cuadrado minimalista redondeado */
        padding: 6px !important;
    }
    
    /* metrics-badge styling: small font, slate-400 color for black/dark theme */
    .metrics-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        font-size: 0.72rem;
        color: #94a3b8; /* Slate-400 */
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px dashed rgba(255, 255, 255, 0.1);
        opacity: 0.85;
    }
</style>
""", unsafe_allow_html=True)

st.title("Agente IA - Voto informado 📖")
st.markdown("¡Hola! Soy tu asistente virtual para informarte sobre los planes de gobierno de los candidatos a la presidencia del Perú.")

# Initialize session state for session_id and messages
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar removed as per requirements to avoid manual ingestion from web interface

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            sources_html = "".join([f"<span class='source-badge'>📄 {source}</span>" for source in message["sources"]])
            st.markdown(sources_html, unsafe_allow_html=True)
            
        # Display execution metrics if assistant and available
        if message["role"] == "assistant" and "metrics" in message:
            m = message["metrics"]
            metrics_html = f"""
            <div class='metrics-container'>
                <span>⚡ <b>Tiempo:</b> {m['duration']:.2f}s</span>
                <span>•</span>
                <span>📥 <b>Tokens Entrada:</b> {m['input_tokens']}</span>
                <span>•</span>
                <span>📤 <b>Tokens Salida:</b> {m['output_tokens']}</span>
                <span>•</span>
                <span>📊 <b>Total:</b> {m['total_tokens']}</span>
            </div>
            """
            st.markdown(metrics_html, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from backend
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Pensando...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/query",
                json={"prompt": prompt, "session_id": st.session_state.session_id}
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                
                # Metrics dict
                metrics = {
                    "duration": data.get("duration", 0.0),
                    "input_tokens": data.get("input_tokens", 0),
                    "output_tokens": data.get("output_tokens", 0),
                    "total_tokens": data.get("total_tokens", 0)
                }
                
                message_placeholder.markdown(answer)
                
                if sources:
                    sources_html = "".join([f"<span class='source-badge'>📄 {source}</span>" for source in sources])
                    st.markdown(sources_html, unsafe_allow_html=True)
                
                # Render metrics dynamically
                metrics_html = f"""
                <div class='metrics-container'>
                    <span>⚡ <b>Tiempo:</b> {metrics['duration']:.2f}s</span>
                    <span>•</span>
                    <span>📥 <b>Tokens Entrada:</b> {metrics['input_tokens']}</span>
                    <span>•</span>
                    <span>📤 <b>Tokens Salida:</b> {metrics['output_tokens']}</span>
                    <span>•</span>
                    <span>📊 <b>Total:</b> {metrics['total_tokens']}</span>
                </div>
                """
                st.markdown(metrics_html, unsafe_allow_html=True)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources,
                    "metrics": metrics
                })
            else:
                message_placeholder.error(f"Error: {response.text}")
        except requests.exceptions.ConnectionError:
            message_placeholder.error("No se pudo conectar al backend. Asegúrate de que FastAPI esté en ejecución.")
