from dotenv import load_dotenv
import os
import requests

load_dotenv()

import streamlit as st

from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from tavily import TavilyClient
from langchain.agents import create_agent


# =========================================================
# STREAMLIT PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Smart City Assistant",
    layout="wide"
)


# =========================================================
# 🌌 NIGHT SKY UI
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 20%, white 0px, transparent 2px),
        radial-gradient(circle at 25% 70%, white 0px, transparent 2px),
        radial-gradient(circle at 40% 15%, white 0px, transparent 2px),
        radial-gradient(circle at 55% 80%, white 0px, transparent 2px),
        radial-gradient(circle at 70% 30%, white 0px, transparent 2px),
        radial-gradient(circle at 85% 65%, white 0px, transparent 2px),
        radial-gradient(circle at 95% 15%, white 0px, transparent 2px),
        linear-gradient(
            180deg,
            #020617 0%,
            #07152f 45%,
            #0a1f3d 75%,
            #020617 100%
        );

    background-size:
        140px 140px,
        190px 190px,
        220px 220px,
        170px 170px,
        200px 200px,
        160px 160px,
        240px 240px,
        cover;

    color: white;
}


/* Main container */

.block-container {
    max-width: 1000px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}


/* Moon */

.moon {
    position: fixed;
    top: 80px;
    right: 80px;

    width: 85px;
    height: 85px;

    border-radius: 50%;

    background: #f8fafc;

    box-shadow:
        0 0 15px white,
        0 0 35px rgba(255,255,255,0.7),
        0 0 70px rgba(150,200,255,0.4);

    z-index: 0;
}


/* Title */

.title {
    text-align: center;

    font-size: 48px;
    font-weight: 700;

    color: white;

    text-shadow:
        0 0 10px rgba(100,180,255,0.8),
        0 0 25px rgba(80,150,255,0.5);

    margin-bottom: 5px;
}


/* Subtitle */

.subtitle {
    text-align: center;

    color: #b8c7e6;

    font-size: 18px;

    margin-bottom: 35px;
}


/* Chat messages */

[data-testid="stChatMessage"] {

    background: rgba(10, 25, 55, 0.65);

    border:
        1px solid rgba(150,200,255,0.15);

    border-radius: 18px;

    padding: 10px;

    margin-bottom: 12px;

    backdrop-filter: blur(10px);

    box-shadow:
        0 8px 25px rgba(0,0,0,0.25);
}


/* Chat input */

.stChatInputContainer textarea {

    background: rgba(5,20,45,0.9) !important;

    color: white !important;

    border:
        1px solid rgba(120,180,255,0.4) !important;

    border-radius: 15px !important;
}


/* Sidebar */

section[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            #020617,
            #07152f
        );

    border-right:
        1px solid rgba(255,255,255,0.1);
}


/* Buttons */

.stButton button {

    border-radius: 12px;

    background: rgba(30,80,150,0.7);

    color: white;

    border:
        1px solid rgba(150,200,255,0.4);
}


.stButton button:hover {

    background: rgba(50,110,200,0.85);

    border-color:
        rgba(180,220,255,0.8);
}

</style>

<div class="moon"></div>

""", unsafe_allow_html=True)


# =========================================================
# 🌃 HEADER
# =========================================================

st.markdown(
    '<div class="title">🌃 Smart City Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Your intelligent assistant for weather, news & city information</div>',
    unsafe_allow_html=True
)


# =========================================================
# 🌦️ WEATHER TOOL
# =========================================================

@tool
def get_weather(city: str) -> str:
    """Get current weather of a city"""
    
    api_key = os.getenv("OPEN_WEATHER_API_KEY")

    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={city},IN&appid={api_key}&units=metric"
    )
    
    response = requests.get(url)

    data = response.json()
    
    if str(data.get("cod")) != "200":
        return f"Error: {data.get('message', 'Could not fetch weather')}"
    
    temp = data["main"]["temp"]

    desc = data["weather"][0]["description"]
    
    return f"Weather in {city}: {desc}, {temp}°C"


# =========================================================
# 📰 NEWS TOOL
# =========================================================

tavily_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


@tool
def get_news(city: str) -> str:
    """Get latest news about a city"""
    
    response = tavily_client.search(
        query=f"latest news in {city}",
        search_depth="basic",
        max_results=3
    )
    
    results = response.get("results", [])
    
    if not results:
        return f"No news found for {city}"
    
    news_list = []
    
    for r in results:

        title = r.get("title", "No title")

        url = r.get("url", "")

        snippet = r.get("content", "")
        
        news_list.append(
            f"- {title}\n"
            f"  🔗 {url}\n"
            f"  📝 {snippet[:100]}..."
        )
    
    return (
        f"Latest news in {city}:\n\n"
        + "\n\n".join(news_list)
    )


# =========================================================
# 🧠 LLM SETUP
# =========================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b"
)


# =========================================================
# 🤖 AGENT
# =========================================================

agent = create_agent(
    llm,

    tools=[
        get_weather,
        get_news
    ],

    system_prompt="""
You are a city assistant.

You ONLY answer:
1. Weather-related questions
2. Latest news-related questions
3. City related information like transportation, events and related information.

IMPORTANT TOOL INSTRUCTIONS:

- For weather-related questions, ALWAYS use the get_weather tool.
- For latest news-related questions, ALWAYS use the get_news tool.
- If the user asks for BOTH weather and latest news, use BOTH tools.
- If the user mentions a city, use that city when calling the tools.
- Do not make up weather or news information.
- Use the information returned by the tools to answer the user.
- NEVER ask the user for permission before using a tool.
- NEVER ask "May I use the tool?"
- NEVER ask the user to say yes before calling a tool.

For unrelated questions, respond:
"I can only help with city weather and latest news and city related information."
"""
)


# =========================================================
# 💬 SESSION STATE
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🌃 Smart City")

    st.markdown("""
### What I can do

🌤️ **Weather**

📰 **Latest News**

🚇 **Transportation**

🎉 **City Events**

🏙️ **City Information**
### 🚀 What I Built

✅ **Weather Tool**  
Integrated OpenWeather API to fetch current weather.

✅ **News Tool**  
Integrated Tavily to retrieve latest city news.

✅ **AI Agent**  
Built a LangChain agent that decides which tool to use.

✅ **LLM Integration**  
Connected the agent with Groq's GPT-OSS model.

✅ **System Prompt**  
Restricted the assistant to weather, news and city-related queries.

✅ **Tool Calling**  
Enabled the agent to automatically call the required tools.

✅ **Conversation History**  
Maintained previous messages during the conversation.
""")

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.rerun()


# =========================================================
# DISPLAY PREVIOUS MESSAGES
# =========================================================

for message in st.session_state.messages:

    if isinstance(message, HumanMessage):

        with st.chat_message("user"):

            st.markdown(message.content)

    else:

        with st.chat_message("assistant"):

            st.markdown(message.content)


# =========================================================
# USER INPUT
# =========================================================

user_input = st.chat_input(
    "Ask about weather, news or city information..."
)


# =========================================================
# PROCESS USER QUESTION
# =========================================================

if user_input:

    # -----------------------------------------
    # Display user message
    # -----------------------------------------

    with st.chat_message("user"):

        st.markdown(user_input)


    st.session_state.messages.append(
        HumanMessage(
            content=user_input
        )
    )


    # -----------------------------------------
    # Run Agent
    # -----------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "🌃 Checking city information..."
        ):

            try:

                result = agent.invoke(
                    {
                        "messages": st.session_state.messages
                    }
                )

                response = result[
                    "messages"
                ][-1].content

            except Exception as e:

                response = (
                    f"⚠️ Something went wrong:\n\n"
                    f"{str(e)}"
                )


        st.markdown(response)


    # -----------------------------------------
    # Save complete agent message history
    # -----------------------------------------

    st.session_state.messages = result["messages"]

    