# 🌃 Smart City Assistant

An AI-powered Smart City Assistant that provides users with **current weather, latest city news, and city-related information** through a conversational interface.

The application uses a **LangChain Agent** connected to an LLM and external tools. The agent determines which tool is required based on the user's query and retrieves the relevant information.

---

## 🚀 Features

- 🌤️ **Current Weather**
  - Retrieves real-time weather information for Indian cities.
  - Uses the OpenWeather API.

- 📰 **Latest News**
  - Retrieves the latest news related to a city.
  - Uses Tavily for web search.

- 🤖 **AI Agent**
  - Built using LangChain's Agent framework.
  - The LLM determines which available tool should be used based on the user's request.

- 🧠 **LLM Integration**
  - Uses Groq's `openai/gpt-oss-120b` model.

- 💬 **Conversational Interface**
  - Maintains conversation history during the session.

- 🌌 **Streamlit UI**
  - Interactive chatbot interface.
  - Night-sky themed interface with stars and moon.

- 🔐 **Environment Variables**
  - API keys are stored using environment variables rather than being hard-coded.

---

## 🏗️ Project Architecture

```text
                         User
                           │
                           ▼
                    ┌─────────────┐
                    │ Streamlit UI│
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  LangChain  │
                    │    Agent    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Groq LLM   │
                    └──────┬──────┘
                           │
                 Decides which tool
                    should be used
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      ┌───────────────┐         ┌───────────────┐
      │ Weather Tool  │         │   News Tool   │
      └───────┬───────┘         └───────┬───────┘
              │                         │
              ▼                         ▼
       OpenWeather API              Tavily API
              │                         │
              └────────────┬────────────┘
                           ▼
                    Tool Results
                           │
                           ▼
                       Groq LLM
                           │
                           ▼
                    Final Response
