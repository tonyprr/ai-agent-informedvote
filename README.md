# Agente IA - Voto Informado 📖 (MultiPDF RAG Engine)

Este proyecto es una plataforma de análisis de planes de gobierno y documentos presidenciales diseñada para ayudar a los ciudadanos a informarse. Está estructurado como un motor **RAG (Retrieval-Augmented Generation)** avanzado y profesional que utiliza un agente inteligente de toma de decisiones construido sobre **LangGraph** (StateGraph), **FastAPI** como backend serverless, y una interfaz de usuario premium desarrollada en **Streamlit**.

---

## 🚀 Características Clave

1. **Agente Inteligente con LangGraph:**
   * Implementado mediante un grafo de estados (`StateGraph`) que decide dinámicamente si consultar la base de datos de documentos locales o recurrir a búsquedas externas.
   * Totalmente modular y preparado para escalar con más herramientas en el futuro (ej. búsquedas en la web, plugins o integraciones de APIs externas).

2. **Optimización de Tokens y Memoria Avanzada:**
   * **Sliding Window:** Ajusta automáticamente el historial de chat al límite configurado sin romper secuencias críticas de llamadas a herramientas.
   * **Tool Filtering:** Reemplaza el contexto pesado y largo de búsquedas pasadas en PDFs en el historial, manteniendo las conversaciones y la memoria coherente con un gasto de tokens ínfimo.
   * **MemorySaver Checkpointer:** Almacena y recupera automáticamente el contexto de múltiples sesiones utilizando un identificador de hilo (`thread_id` / `session_id`).

3. **Métricas en Tiempo Real:**
   * Mide con precisión el tiempo de procesamiento de cada consulta.
   * Suma y expone el consumo real de tokens (Entrada, Salida y Total) devuelto por la API de Gemini, mostrándolo de forma minimalista en la UI.

4. **Diseño Visual Premium:**
   * Interfaz adaptada a un tema oscuro/negro minimalista.
   * Formato de chat estilizado: burbujas de respuesta del asistente en celeste claro minimalista con texto negro, y avatares del usuario con marcos minimalistas y fondo rojo claro.
   * Visualizador de fuentes integradas para identificar de qué documento PDF se extrajo cada respuesta.

5. **Infraestructura como Código (IaC) en la Nube:**
   * Archivos de configuración de **Terraform** listos para aprovisionar los recursos de Azure en su **capa gratuita (Free Tier)**.
   * Estructura adaptada para correr de forma serverless bajo el modelo de programación Python V2 de **Azure Functions**.

---

## 🛠️ Stack Tecnológico

* **Core & LLM:** Google Gemini (`gemini-3.1-pro-preview` y `gemini-embedding-001`)
* **Framework del Agente:** LangGraph y LangChain Community
* **Vector Store:** Pinecone (Base de datos vectorial en la nube)
* **Backend:** FastAPI (Python)
* **Frontend:** Streamlit + Tailwind CSS
* **Despliegue e Infraestructura:** Terraform y Azure Functions (Serverless Y1)

---

## ⚙️ Estructura del Proyecto

```
demo-langchain/
├── backend/
│   ├── agent.py       # Definición del flujo del agente de LangGraph
│   ├── main.py        # Endpoints FastAPI y recolección de métricas
│   ├── rag.py         # Conectores de base de datos vectorial e ingesta
│   └── tools.py       # Herramientas del agente (PDF Search y Web Search Mock)
├── frontend/
│   └── app.py         # Interfaz de usuario interactiva en Streamlit
├── terraform/
│   ├── main.tf        # Recursos de Azure (Storage, Y1 Plan, Function App)
│   ├── variables.tf   # Parámetros del despliegue
│   └── outputs.tf     # Salidas de configuración de red
├── function_app.py    # Punto de entrada ASGI de Azure Functions (Python V2)
├── host.json          # Configuración del host de Azure Functions
├── .funcignore        # Filtro de subida para optimización en la nube
├── requirements.txt   # Dependencias de Python
└── data/              # Carpeta local para colocar PDFs a indexar
```

---

## 💻 Configuración Local

### 1. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con la siguiente estructura:
```env
GOOGLE_API_KEY=tu_google_api_key
PINECONE_API_KEY=tu_pinecone_api_key
PINECONE_INDEX_NAME=multipdf-rag
```

### 2. Iniciar el Backend
Instala las dependencias y corre el servidor FastAPI:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Iniciar backend localmente en puerto 8000
python -m uvicorn backend.main:app --reload
```

### 3. Iniciar el Frontend
En otra terminal activa, corre el servidor de Streamlit:
```bash
streamlit run frontend/app.py
```

---

## ☁️ Despliegue en Producción

### Backend (Azure Functions en Capa Gratuita)
1. Navega a `terraform/` e inicializa los recursos:
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```
2. Obtén la URL de salida y publica tu código desde la raíz del proyecto usando Azure Functions Core Tools:
   ```bash
   func azure functionapp publish func-rag-backend
   ```

### Frontend (Streamlit Community Cloud)
1. Sube tu código a un repositorio en **GitHub** (asegúrate de no incluir el `.env` en tu commit, usa el `.gitignore` proporcionado).
2. Conéctate a [share.streamlit.io](https://share.streamlit.io) e importa tu repositorio.
3. En la sección **Secrets** de tu aplicación en Streamlit, configura la variable de red apuntando a tu función de Azure:
   ```toml
   BACKEND_URL = "https://tu-function-app-en-azure.azurewebsites.net"
   ```
