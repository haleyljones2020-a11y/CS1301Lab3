import requests
import streamlit as st
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
st.set_page_config(page_title = "Chat with Sprout!", page_icon = "🌱")
st.title("Chat with Sprout! 🌱")
st.write("Chat about anything and everything plants with Sprout! You can inquire about plant care specifics, tips for growing different types of plants, plant identification and more!")

st.sidebar.header("Settings")
trefle_token = st.sidebar.text_input("Trefle API Token", type = "password", help = "Enter your Trefle API token here!")
gemini_key = st.sidebar.text_input("Gemini API Key", type = "password", help = "Enter your Gemini API key here!")
    
search_query = st.sidebar.text_input("Plant Search", value = "houseplant")

if st.sidebar.button("Reset Conversation"):
    st.session_state.pop("genai_client", None)
    st.session_state.pop("genai_client_key", None)
    st.session_state.pop("chat_session", None)
    st.session_state.pop("display_messages", None)
    st.rerun()

if not gemini_key or not trefle_token:
    st.info("Please enter your Trefle API token and your Gemini API key to continue!")
    st.stop()

def plantChat(query,token):
    url = "https://trefle.io/api/v1/plants/search"
    try:
        response = requests.get(url, params ={"q": query, "token": token}, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException:
        return []


with st.spinner("Sprout is gathering his response..."):
    plants = plantChat(search_query, trefle_token)
if not plants:
    st.warning("No information could be found based on your prompt. Please check your search or your Trefle API token.")
    st.stop()
plantList = []
for plant in plants[:10]:
    common = plant.get("common_name") or "Unknown Plant"
    scientific = plant.get("scientific_name") or "Unknown Species"
    plantList.append(f"{common} ({scientific})")

plantStr = str(plantList)

system_prompt = (
    f"You are Sprout, a friendly AI assistant who specializes in plants. "
    f"The plants returned from the Trefle API include: {plantStr}. "
    f"Whenever possinble, answer the user's questions using these plants as "
    f"context. If the user asks a question about plants, answer it normally "
    f"and keep the conversation focused on your knowledge of plants only. "
    f"If the user strays from the topic of plants, kindly answer with a brief "
    f"response and gently pull the conversation back to plants or gardening. "
    f"Keep your responses school appropriate, friendly, concise and easy to "
    f"understand."
)

if ("genai_client" not in st.session_state or st.session_state.get("genai_client_key") != gemini_key):
    try:
        st.session_state.genai_client = genai.Client(api_key=gemini_key)
        st.session_state.genai_client_key = gemini_key
        st.session_state.pop("chat_session", None)
    except Exception as e:
        st.error(f"Could not connect to Gemini: {e}")
        st.stop()
client = st.session_state.genai_client

if "chat_session" not in st.session_state:
    try:
        st.session_state.chat_session = client.chats.create(model="gemini-flash-latest", config= types.GenerateContentConfig(system_instruction = system_prompt),)
    except genai_errors.APIError as e:
        st.error(f"Could not start the chat session: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Something went wrong: {e}")
        st.stop()
if "display_messages" not in st.session_state:
        st.session_state.display_messages = [{"role":"assistant", "content": ("Hello! My name is Sprout! As me anything about plants and gardening!"),}]
for message in st.session_state.display_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_prompt = st.chat_input("Ask Sprout about your plants...")

if user_prompt:
    st.session_state.display_messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Sprout is thinking...")
        reply_text = None
        try:
            context = (f"The following plants we returned from the Trefle API: {plantStr}. User question: {user_prompt}")
            response = st.session_state.chat_session.send_message(context)
            try:
                reply_text = response.text
                if not reply_text:
                    raise ValueError("Empty response")
            except (ValueError, AttributeError):
                reply_text = ("Sorry! I could not generate a response for your question. Please try again with a different question about plants!")
        except genai_errors.APIError as e:
            code = getattr(e, "code", None)
            if code == 429:
                reply_text = ("Sprout seems to be recieving a few too many requests as the moment. Please wait a few minutes and try again!")
            elif code == 404:
                reply_text = ("The Gemini model could not be found. Please try again another time!")
            else:
                reply_text = (f"Gemini returned an error: \n\n{e}")
        except Exception as e:
            reply_text = ("Something went wrong")
        placeholder.markdown(reply_text)
    st.session_state.display_messages.append({"role":"assistant", "content":reply_text})

st.divider()
st.caption("Sprout is powered by a Google Gemini API which uses plant information gathered from the Trefle API to provide you with personalized plant advice!")
                
        
                                              
