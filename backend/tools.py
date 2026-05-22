from langchain_core.tools import tool
from .rag import get_vectorstore

@tool(response_format="content_and_artifact")
def search_pdfs(query: str):
    """Busca en los documentos PDF cargados para obtener información relevante sobre la consulta.
    Útil para responder preguntas basándose en la documentación local proporcionada (como planes de gobierno).
    """
    vectorstore = get_vectorstore()
    docs = vectorstore.similarity_search(query, k=4)
    
    results = []
    sources = []
    for doc in docs:
        source_path = doc.metadata.get("source", "Unknown Source")
        filename = source_path.split("/")[-1]
        sources.append(filename)
        results.append(f"[Fuente: {filename}]\n{doc.page_content}")
        
    content = "\n\n---\n\n".join(results) if results else "No se encontró información relevante en los PDFs sobre esta consulta."
    
    # El artifact es ideal para enviar metadatos puros (como las fuentes) al flujo superior
    artifact = {"sources": list(set(sources))}
    return content, artifact

@tool
def search_web(query: str) -> str:
    """Busca en internet información actualizada. Útil para obtener datos en tiempo real, eventos recientes, o información que no está explícitamente en los PDFs locales."""
    # En el futuro aquí puedes integrar Tavily, DuckDuckGo o Serper API.
    # Por ahora retorna un mensaje indicando que la función es un placeholder.
    return "Nota del sistema: La herramienta de búsqueda web está simulada y en desarrollo. Indícale al usuario que esta característica de expansión llegará en el futuro."
