"""
Page 2 — Sprout, the Plant Care Chatbot
----------------------------------------
A conversational chatbot built with Google's Gemini API that keeps the same
overall theme as Page 1 (plants / gardening) WITHOUT calling the Trefle API
or any external plant-data API. All plant knowledge here comes from the
Gemini LLM itself, not from Page 1's data source.

Requirements covered:
  - Try/Except error handling around every Gemini call (rate limits, safety
    blocks, network issues) so the app can never crash from a Gemini error.
  - Conversation memory across turns using st.session_state + Gemini's
    chat-session history.
  - Same theme as Page 1 (plants/gardening) but no API-from-page-1 data.
"""

import streamlit as st
import google.generativeai as genai

# google-api-core exceptions aren't guaranteed to be importable on every
# version of the google-generativeai package, so we fall back gracefully.
try:
    from google.api_core.exceptions import (
        ResourceExhausted,
        GoogleAPIError,
        InvalidArgument,
    )
except ImportError:  # pragma: no cover - defensive fallback
    ResourceExhausted = Exception
    GoogleAPIError = Exception
    InvalidArgument = Exception


# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(page_title="Sprout - Plant Chatbot", page_icon="🌱")

st.title("🌱 Sprout — Your Plant Care Chat Buddy")
st.write(
    "Chat with **Sprout**, an AI gardening and houseplant-care assistant. "
    "This page uses the Google Gemini API directly — it does **not** pull "
    "any data from the Trefle API used on the Plant Explorer page."
)

SYSTEM_PROMPT = (
    "You are Sprout, a friendly, knowledgeable assistant who specializes in "
    "plants, gardening, houseplant care, and botany. Keep every response "
    "focused on plant-related topics whenever possible (watering schedules, "
    "sunlight needs, soil, pests, propagation, plant identification tips, "
    "gardening advice, etc.). If the user asks something totally unrelated "
    "to plants, gently steer the conversation back to plants after a brief, "
    "polite answer. Keep responses concise, warm, and easy to follow for a "
    "school-appropriate audience."
)

# --------------------------------------------------------------------------
# Sidebar — API key + model settings
# --------------------------------------------------------------------------
st.sidebar.header("Settings")

api_key = st.sidebar.text_input(
    "Google Gemini API key",
    type="password",
    help="Get a free API key at https://aistudio.google.com/apikey",
)

model_name = st.sidebar.selectbox(
    "Gemini model",
    ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    index=0,
    help="Flash models are faster and cheaper; Pro is more capable.",
)

if st.sidebar.button("🔄 Reset conversation"):
    st.session_state.pop("chat_session", None)
    st.session_state.pop("display_messages", None)
    st.rerun()

if not api_key:
    st.info("👈 Enter your Gemini API key in the sidebar to start chatting with Sprout.")
    st.stop()

# --------------------------------------------------------------------------
# Configure Gemini + set up (or reuse) a persistent chat session
# --------------------------------------------------------------------------
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT,
    )
except Exception as e:
    st.error(f"Couldn't initialize the Gemini model: {e}")
    st.stop()

# "chat_session" holds Gemini's own memory of the conversation so it can
# refer back to earlier turns. "display_messages" is what we render on
# screen. Both persist in session_state across reruns, which is how the
# chatbot remembers prior conversation turns.
if "chat_session" not in st.session_state:
    try:
        st.session_state.chat_session = model.start_chat(history=[])
    except Exception as e:
        st.error(f"Couldn't start a new chat session: {e}")
        st.stop()

if "display_messages" not in st.session_state:
    st.session_state.display_messages = [
        {
            "role": "assistant",
            "content": "Hi, I'm Sprout 🌱 Ask me anything about plants, "
            "gardening, or houseplant care!",
        }
    ]

# --------------------------------------------------------------------------
# Render existing conversation
# --------------------------------------------------------------------------
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------------------------------
# Handle new user input
# --------------------------------------------------------------------------
user_prompt = st.chat_input("Ask Sprout about your plants...")

if user_prompt:
    # Show the user's message immediately
    st.session_state.display_messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("🌿 Sprout is thinking...")

        reply_text = None
        try:
            # send_message() uses the chat_session's internal history, so
            # Gemini "remembers" everything said earlier in this session.
            response = st.session_state.chat_session.send_message(user_prompt)

            # Accessing .text can itself raise if the response was blocked
            # by Gemini's safety filters (e.g. inappropriate content), so
            # this needs its own try/except separate from network errors.
            try:
                reply_text = response.text
            except (ValueError, AttributeError):
                block_reason = None
                try:
                    block_reason = response.prompt_feedback.block_reason
                except Exception:
                    pass
                reply_text = (
                    "🚫 I can't respond to that one — it looks like the "
                    "content may have been flagged as inappropriate"
                    + (f" ({block_reason})" if block_reason else "")
                    + ". Let's keep chatting about plants and gardening!"
                )

        except ResourceExhausted:
            reply_text = (
                "⏳ I'm getting a lot of requests right now and hit a rate "
                "limit. Please wait a moment and try again."
            )
        except InvalidArgument as e:
            reply_text = (
                "⚠️ There was a problem with that request (it may have been "
                f"too long or malformed). Details: {e}"
            )
        except GoogleAPIError as e:
            reply_text = f"⚠️ The Gemini API returned an error: {e}"
        except Exception as e:
            # Final safety net: no matter what goes wrong, the app should
            # never crash -- always show a friendly message instead.
            reply_text = (
                "⚠️ Something unexpected went wrong while talking to Sprout. "
                f"({e}) Please try again."
            )

        placeholder.markdown(reply_text)

    st.session_state.display_messages.append(
        {"role": "assistant", "content": reply_text}
    )

st.divider()
st.caption(
    "Sprout is powered by the Google Gemini API and stays focused on the "
    "same plant/gardening theme as the Plant Explorer page, but does not "
    "use the Trefle API or any data from that page."
)
