How to run the Python backend locally (starting the FastAPI server with Uvicorn):

- Open the VS Code terminal at the root of the project (travelapp-backend)
- Run: source .venv/bin/activate
- Run: uvicorn app.main:app --reload
- Open in the browser: http://127.0.0.1:8000/
- Once http://127.0.0.1:8000/ is up and running, it's also possible to test the API using Postman

To stop the server, just press Ctrl + C