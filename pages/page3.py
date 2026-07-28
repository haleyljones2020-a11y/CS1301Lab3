# Concept for page 3 - The user is able to enter two different things -
# 1 - environment type - amount of sunlight, relative temperature, humidity
# 2 - maintenance level - how frequent is this person able to make time for their plant (i.e. watering frequency, special attentiveness, etc) 
import requests
import streamlit as st
from google import genai
from google.genai import types

# page info - header and basic description

st.set_page_config(page_title="Search for Your Ideal Plant Using Chatbot!", page_icon="🌿")
st.title("Find Your Perfect Plant With Sprout!")
st.write("Chat with **Sprout** about the environmental conditions and maintenance level you would be able to provide a plant."
         "Once you have entered this information, your AI plant care assistant will reveal to you the ideal plant"
         "based on your lifestyle! This platform uses the Google Gemini API along with data from the Trefle API"
         "to find your perfect plant."
)

trefle_token = st.sidebar.text_input(
    "Trefle API Token",
    type = "password",
    help = "Enter your Trefle API token here!"
)

gemini_key = st.sidebar.text_input(
    "Gemini API Key",
    type = "password",
    help = "Enter your Google Gemini API key here!"
)

if not trefle_token or not gemini_key:
    st.info("Please enter your Trefle API token and your Gemini API key to continue!")
    st.stop()

environment = st.sidebar.multiselect(
    "🌞 What environment would your home provide for your new plant?",
    ["Direct sunlight", "Indirect sunlight", "Low sunlight", "Warm temperatures (68°-75°F)", "Cooler temperatures(60°-67°F)",
     "Hot temperatures (75°F+)", "Low humidity", "Medium humidity", "High humidity"]
)

maintenance = st.sidebar.select_slider(
    "🎍 How often will you remember to check on your plant?",
    ["Daily", "Every other day", "Weekly", "Biweekly", "Monthly", "I have a plant? (aka rarely)"]
)

if not environment:
    st.info("Please select at least one environment descriptor in the sidebar to continue!")
    st.stop()
def find_plants(query, token):
    url = f"https://trefle.io/api/v1/plants/search?q={query}&token={token}"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        return data.get("data",[])
    return []
with st.spinner("Fetching plant options from Trefle..."):
    plants = find_plants("houseplant", trefle_token)
if not plants:
    st.warning("No plant data was found from Trefle. You might want to check your token!")
    st.stop()
if st.button("Find my Perfect Plant!"):
    try:
        client = genai.Client(api_key=gemini_key)
        plantList = []
        for plant in plants[0:10]:
            name = plant.get("common_name") or "Unknown Plant"
            scientific = plant.get("scientific_name") or "Unknown Species"
            plantList.append(f"- {name} ({scientific})")

        plantStr = str(plantList)
        system_prompt = (
            f"You are Sprout, a friendly and intelligent assistant who is well educated in plants, gardening, "
            f"houseplant care, and botany. Keep your responses focused on plant-related topics for as long as "
            f"possible (including plant care, sunlight needs, watering schedules, soil, pests, propagation, "
            f"plant identification tips, gardening advice, etc.). If the user asks something completely "
            f"unrelated to plants, you should answer briefly but gently pull the conversation back to the topic "
            f"of plants soon after. "
            f"Your main job is to find the best plant for a user based on the information as follows: "
            f"User Environment Choices:{environment} and User Maintenance schedule:{maintenance}. "
            f"Possible plants from the Trefle data base are found here: {plantStr} "
            f"In your response, please provide the best matching plant (the common name and the scientific name in "
            f"parenthesis), a score of compatibility between the plant and the user, an explanation of why this "
            f"plant is ideal for them, and a few basic care instructions for keeping the plant alive and happy! "
        )
        with st.spinner("Sprout is picking out your plant now..."):
            response = client.models.generate_content(
                model = "gemini-flash-latest",
                contents = system_prompt
            )
            st.write(response.text)
    except Exception as e:
        st.error(f"Something went wrong with Gemini: {e}")
