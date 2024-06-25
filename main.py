from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from typing import List, Dict
import random

app = FastAPI()

html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Chat</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        #login, #chat {
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            width: 100%;
            max-width: 400px;
        }
        #chat {
            display: none;
            flex-direction: column;
            height: 500px;
        }
        #messages {
            list-style: none;
            padding: 0;
            margin: 0;
            flex-grow: 1;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            background-color: #f9f9f9;
        }
        #messages li {
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 8px;
            color: white;
            display: inline-block;
            clear: both;
            max-width: 80%;
        }
        .message-incoming {
            float: left;
            background-color: #222;
        }
        .message-outgoing {
            float: right;
            background-color: #444;
        }
        form {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        button {
            padding: 10px 20px;
            border: none;
            background-color: #007bff;
            color: white;
            border-radius: 8px;
            cursor: pointer;
        }
        button:disabled {
            background-color: #cccccc;
        }
    </style>
</head>
<body>
    <div id="login">
        <h1>WebSocket Chat</h1>
        <form onsubmit="connect(event)">
            <input type="text" id="username" placeholder="Enter your username" autocomplete="off" required>
            <button type="submit">Connect</button>
        </form>
    </div>
    <div id="chat">
        <ul id="messages"></ul>
        <form onsubmit="sendMessage(event)">
            <input type="text" id="messageText" placeholder="Enter your message" autocomplete="off" required>
            <button type="submit">Send</button>
        </form>
    </div>
    <script>
        var ws;
        var username;
        var userColors = {};

        function getRandomColor() {
            var letters = '0123456789ABCDEF';
            var color = '#';
            for (var i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        }

        function connect(event) {
            username = document.getElementById("username").value;
            userColors[username] = getRandomColor();
            ws = new WebSocket("ws://localhost:8000/ws?username=" + username);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);

                message.appendChild(content);

                var usernameMatch = event.data.match(/^\[(.+?)\]/);
                if (usernameMatch) {
                    var sender = usernameMatch[1];
                    if (!userColors[sender]) {
                        userColors[sender] = getRandomColor();
                    }
                    message.style.backgroundColor = userColors[sender];
                }

                if (event.data.startsWith("[" + username + "]")) {
                    message.classList.add('message-outgoing');
                } else {
                    message.classList.add('message-incoming');
                }

                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;
            };
            document.getElementById("login").style.display = "none";
            document.getElementById("chat").style.display = "flex";
            event.preventDefault();
        }

        function sendMessage(event) {
            var input = document.getElementById("messageText");
            ws.send(input.value);
            input.value = '';
            event.preventDefault();
        }
    </script>
</body>
</html>
"""


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


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket)
    await manager.broadcast(f"[{username}] joined the chat")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"[{username}]: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"[{username}] left the chat")
