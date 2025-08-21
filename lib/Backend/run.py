import uvicorn

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "app:app",  # Path to your FastAPI app
        host="0.0.0.0",  # Allows external access
        port=8000,  # Port to run the server on
        reload=True,  # Auto-reload on code changes
        workers=1  # Number of worker processes
    )
