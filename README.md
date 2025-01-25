# LearnMate: AI-powered Study Assistant

LearnMate is an AI-powered study assistant designed to enhance the learning experience for students. It leverages the power of AI to provide personalized study recommendations, answer questions, and create a more engaging and interactive learning environment.

## Demo

[![LearnMate Demo](https://img.youtube.com/vi/qNFZzqNMBZI/0.jpg)](https://www.youtube.com/watch?v=qNFZzqNMBZI)

## Features

- **Personalized Study Recommendations**: AI-driven study plans tailored to individual learning patterns
- **Question Answering**: Interactive Q&A sessions with AI tutor
- **Interactive Learning Environment**: Engaging study sessions with real-time feedback
- **Performance Analytics**: Detailed insights into learning progress
- **Adaptive Learning**: Difficulty adjusts based on user performance

## Tech Stack

### Backend
- FastAPI
- SQLModel
- OpenAI GPT-4
- ElevenLabs
- SQLite
- Poetry (dependency management)
- Pydantic
- AIOHTTP

### Key Dependencies
- Python 3.11+
- FastAPI for REST API
- SQLModel for ORM
- OpenAI GPT-4 for AI interactions
- ElevenLabs for voice synthesis
- Uvicorn for ASGI server
- SQLite for database

## Getting Started

1. Clone the repository
2. Install dependencies using Poetry
3. Set up your OpenAI API key in the `.env` file
4. Run the application using `uvicorn main:app --reload`

## API Documentation

Once running, access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
