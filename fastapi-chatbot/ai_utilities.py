import os
import asyncio
from fastapi import WebSocket
from dotenv import load_dotenv
from typing import List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_cohere import ChatCohere
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Load environment variables
load_dotenv()

# Initialize API keys securely
def get_cohere_api_key():
    return os.getenv('COHERE_API_KEY')

COHERE_API_KEY = get_cohere_api_key()
model = ChatCohere(model="command-r-plus", cohere_api_key=COHERE_API_KEY)

# Utility functions and classes
def get_session_history(session_id: str):
    return SQLChatMessageHistory(session_id, "sqlite:///memory.db")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You're an assistant who is genius."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

runnable = prompt | model

runnable_with_history = RunnableWithMessageHistory(
    runnable,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

async def async_generator_wrapper(synchronous_generator):
    for item in synchronous_generator:
        await asyncio.sleep(0)  # Allow other tasks to run
        yield item

# Track active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
