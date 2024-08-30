from fastapi import FastAPI, WebSocket, Form, Request, Response, HTTPException, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from ai_utilities import model, runnable_with_history, async_generator_wrapper, ConnectionManager
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from typing import List, Annotated
import os
import uvicorn
import asyncio
from db_utilities import *

load_dotenv()

app = FastAPI()
# app.add_middleware(SessionMiddleware, secret_key=os.getenv('SECRET_KEY'))

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add session middleware with a secure secret key
app.add_middleware(
    SessionMiddleware, 
    secret_key="my_app_very_secret_key"
)

# Setup templates
templates = Jinja2Templates(directory="./templates")
processing_lock = asyncio.Lock()

# Use a list to store chat responses. Consider using a more scalable storage solution for production.
chat_responses: List[str] = []

# Initialize a chat log with a system message.
chat_log = [{
    'role': 'system',
    'content': 'You are a Helpful assistant, skilled in explaining complex concepts in simple terms.'
}]

manager = ConnectionManager()


@app.on_event("startup")
async def startup():
    initialize_db()

@app.on_event("shutdown")
async def shutdown():
    print("Application shutdown: Close database connections, etc.")

@app.get("/", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/")
async def signup(request: Request, email: str = Form(...), username: str = Form(...), password: str = Form(...)):
    try:
        # Assume create_user function handles user creation and hashing of password
        create_user(email, username, password)
        return RedirectResponse(url="/login?message=User created successfully", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    message = request.query_params.get("message", "")
    return templates.TemplateResponse("login.html", {"request": request, "message": message})


@app.get("/logout", response_class=HTMLResponse)
async def login_page(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login?message=Successfully logged out", status_code=303)

@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if check_user(email, password):
        request.session['user_email'] = email
        request.session['username'] = get_username(email)
        return RedirectResponse(url="/chatbot", status_code=303)
    else:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
@app.get("/chatbot", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve the chat page."""
    if not request.session.get('user_email') or not request.session.get('username'):
            return RedirectResponse(url="/login?message=Login at /login to access this page", status_code=303)

    return templates.TemplateResponse("chatbot.html", {"request": request, "chat_responses": chat_responses})

# Endpoint for chatting through http but not used in frontend as websokcet is main thing and that functionality is preferably shown
@app.post("/chatbot", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    """Handle user input from the chat form."""
    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    bot_response = model.invoke(chat_log).content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse("chatbot.html", {"request": request, "chat_responses": chat_responses})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time AI responses."""
    username = websocket.session.get('username')
    email = websocket.session.get('user_email')
    await manager.connect(websocket)
    try:
        while True:
            user_message = await websocket.receive_text()
            chat_log.append({'role': 'user', 'content': user_message})
            
            # Broadcast the user message as a specially formatted message
            async with processing_lock:
                await manager.broadcast(f"user:: from {username} : {user_message}")
                async for ai_response in get_ai_response(user_message, email):
                    chat_log.append({'role': 'assistant', 'content': ai_response})
                    await manager.broadcast(f"bot::{ai_response}")  # Broadcast bot response
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def get_ai_response(message, email):
    """Generate responses from the AI asynchronously."""
    async for chunk in async_generator_wrapper(runnable_with_history.stream(
        {"input": message},
        config={"configurable": {"session_id": email}}
    )):
        yield chunk.content  # Adjust according to the actual structure of `chunk`

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="debug", reload=True)
