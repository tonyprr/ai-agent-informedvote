from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver

from .tools import search_pdfs, search_web
from .rag import LLM_MODEL

def create_rag_graph():
    # Inicializamos el modelo (ahora usa Gemini 3.1 Pro via backend/rag.py)
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.1)
    
    # Herramientas modulares escalables (aquí puedes añadir herramientas MCP futuras)
    tools = [search_pdfs, search_web]
    llm_with_tools = llm.bind_tools(tools)
    
    system_prompt = """Eres un asistente experto y profesional para el análisis de planes de gobierno y documentos presidenciales.
Tu objetivo principal es ayudar a los ciudadanos a informarse.

REGLAS DE ACTUACIÓN:
1. Usa las herramientas proporcionadas ('search_pdfs') para buscar información en la base de datos local.
2. Si consideras que la información requiere contexto externo o reciente, puedes usar 'search_web'.
3. DEBES basar tus respuestas en la evidencia encontrada por las herramientas.
4. Si no encuentras la respuesta en los documentos o en la web, dilo claramente.
5. SIEMPRE cita explícitamente el nombre del archivo PDF fuente en tu respuesta final, basándote en la información devuelta por la herramienta [Fuente: nombre_archivo]."""

def optimize_messages(messages, max_messages=12):
    """Aplica optimizaciones de memoria:
    1. Tool Filtering: Vacía el contenido de los ToolMessages de turnos pasados.
    2. Sliding Window: Mantiene solo los últimos N mensajes sin romper secuencias de herramientas.
    """
    optimized = []
    n = len(messages)
    
    # 1. Tool Filtering: Limpiar contenido pesado de herramientas de turnos pasados
    for i, msg in enumerate(messages):
        # Copiamos el mensaje para no mutar el estado de LangGraph directamente
        msg_copy = msg.copy()
        
        if msg_copy.type == "tool":
            # Si hay algún mensaje AI o Humano después de este ToolMessage, pertenece a un turno anterior
            is_past_tool = False
            for post_msg in messages[i+1:]:
                if post_msg.type in ("ai", "human"):
                    is_past_tool = True
                    break
            
            if is_past_tool:
                # Omitimos el texto largo del PDF, conservando los IDs de la llamada para que el historial sea válido
                msg_copy.content = "[Búsqueda en PDFs completada - Detalle omitido para optimizar tokens]"
                if hasattr(msg_copy, "artifact"):
                    msg_copy.artifact = None
                    
        optimized.append(msg_copy)
        
    # 2. Sliding Window: Recorte inteligente de mensajes
    if len(optimized) > max_messages:
        start_idx = len(optimized) - max_messages
        
        # Evitamos iniciar a mitad de una secuencia de herramientas (ej. empezar con un ToolMessage huérfano)
        # Retrocedemos en el índice hasta encontrar un HumanMessage para iniciar la ventana de forma limpia
        while start_idx > 0:
            if optimized[start_idx].type == "human":
                break
            start_idx -= 1
            
        optimized = optimized[start_idx:]
        
    return optimized

def create_rag_graph():
    # Inicializamos el modelo (ahora usa Gemini 3.1 Pro via backend/rag.py)
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.1)
    
    # Herramientas modulares escalables (aquí puedes añadir herramientas MCP futuras)
    tools = [search_pdfs, search_web]
    llm_with_tools = llm.bind_tools(tools)
    
    system_prompt = """Eres un asistente experto y profesional para el análisis de planes de gobierno y documentos presidenciales.
Tu objetivo principal es ayudar a los ciudadanos a informarse.

REGLAS DE ACTUACIÓN:
1. Usa las herramientas proporcionadas ('search_pdfs') para buscar información en la base de datos local.
2. Si consideras que la información requiere contexto externo o reciente, puedes usar 'search_web'.
3. DEBES basar tus respuestas en la evidencia encontrada por las herramientas.
4. Si no encuentras la respuesta en los documentos o en la web, dilo claramente.
5. SIEMPRE cita explícitamente el nombre del archivo PDF fuente en tu respuesta final, basándote en la información devuelta por la herramienta [Fuente: nombre_archivo]."""

    def call_model(state: MessagesState):
        messages = state["messages"]
        
        # Aplicamos la optimización de memoria antes de invocar al LLM
        optimized_history = optimize_messages(messages, max_messages=10)
        
        # En LangGraph, inyectamos el prompt del sistema al inicio de los mensajes en cada ejecución
        sys_msg = SystemMessage(content=system_prompt)
        response = llm_with_tools.invoke([sys_msg] + optimized_history)
        return {"messages": [response]}
        
    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        
        # Si el modelo decide hacer una llamada a función (tool call), enviamos el flujo al ToolNode
        if last_message.tool_calls:
            return "tools"
        # Si no, significa que la respuesta está lista y terminamos el grafo
        return END

    # Construcción profesional del Grafo de Estados (StateGraph)
    workflow = StateGraph(MessagesState)
    
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent") # Las herramientas devuelven el control al agente
    
    # Implementación de MemorySaver (Checkpointer) para la persistencia automática de las conversaciones
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

# Instanciamos el grafo de forma global para usarlo en FastAPI
rag_graph = create_rag_graph()
