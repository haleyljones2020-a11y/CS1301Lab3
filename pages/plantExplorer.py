"""
Page 1 — Plant Explorer
------------------------
A Streamlit page that fetches data from the Trefle API (https://trefle.io),
a global plant database, and lets the user search, filter, and explore
growing-condition data for plants.

External API: Trefle (https://trefle.io/api/v1)
You need a free API token from https://trefle.io/ -- enter it in the
sidebar text box when the app runs (or hardcode it into TREFLE_TOKEN below
for local testing).

All data analysis/processing (family counts, filtering, extracting growth
fields) is done manually in Python below -- no LLM is used to process or
interpret the API data.
"""

import requests
import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(page_title="Plant Explorer", page_icon="🌿", layout="wide")

st.title("🌿 Plant Explorer")
st.write(
    "Search a global plant database (powered by the "
    "[Trefle API](https://trefle.io)), filter results by plant family, "
    "and explore the ideal growing conditions for any species."
)

BASE_URL = "https://trefle.io/api/v1"

# --------------------------------------------------------------------------
# Sidebar — API token + search controls
# --------------------------------------------------------------------------
st.sidebar.header("Settings")

token = st.sidebar.text_input(
    "Trefle API token",
    value="",
    type="password",
    help="Get a free token at https://trefle.io/ after creating an account.",
)

search_query = st.sidebar.text_input(
    "Search for a plant (common or scientific name)",
    value="rose",
)

num_results = st.sidebar.slider(
    "Number of search results to fetch",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    help="How many plants to pull back from the API for this search.",
)

st.sidebar.caption(
    "Tip: try queries like 'oak', 'tomato', 'lavender', 'fern', or 'cactus'."
)

if not token:
    st.info(
        "👈 Enter your free Trefle API token in the sidebar to get started. "
        "Sign up at https://trefle.io/ if you don't have one yet."
    )
    st.stop()


# --------------------------------------------------------------------------
# API helper functions (cached so we don't hammer the API on every rerun)
# --------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def search_plants(query: str, token: str, per_page: int) -> list:
    """Query the Trefle search endpoint and return a list of plant records."""
    results = []
    page = 1
    per_request = 20  # Trefle's max page size
    while len(results) < per_page:
        resp = requests.get(
            f"{BASE_URL}/plants/search",
            params={"q": query, "token": token, "page": page},
            timeout=10,
        )
        if resp.status_code != 200:
            break
        payload = resp.json()
        data = payload.get("data", [])
        if not data:
            break
        results.extend(data)
        if not payload.get("links", {}).get("next"):
            break
        page += 1
    return results[:per_page]


@st.cache_data(ttl=3600, show_spinner=False)
def get_plant_detail(plant_id: int, token: str) -> dict:
    """Fetch full detail (including growth conditions) for a single plant."""
    resp = requests.get(
        f"{BASE_URL}/plants/{plant_id}",
        params={"token": token},
        timeout=10,
    )
    if resp.status_code != 200:
        return {}
    return resp.json().get("data", {})


# --------------------------------------------------------------------------
# Fetch + fully error-handle the search request
# --------------------------------------------------------------------------
with st.spinner("Fetching plants from Trefle..."):
    try:
        raw_plants = search_plants(search_query, token, num_results)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error contacting Trefle API: {e}")
        st.stop()

if not raw_plants:
    st.warning(
        "No plants found (or the API token/rate limit was rejected). "
        "Try a different search term or check your token."
    )
    st.stop()

# --------------------------------------------------------------------------
# Build a DataFrame from the raw API data (manual processing, no LLM)
# --------------------------------------------------------------------------
records = []
for p in raw_plants:
    records.append(
        {
            "id": p.get("id"),
            "common_name": p.get("common_name") or "Unknown",
            "scientific_name": p.get("scientific_name") or "Unknown",
            "family": p.get("family") or "Unspecified",
            "genus": p.get("genus") or "Unspecified",
            "image_url": p.get("image_url"),
        }
    )
df = pd.DataFrame(records)

# --------------------------------------------------------------------------
# Interactive control #2 — filter by plant family (built from fetched data)
# --------------------------------------------------------------------------
families = ["All"] + sorted(df["family"].unique().tolist())
selected_family = st.sidebar.selectbox("Filter results by family", families)

if selected_family != "All":
    filtered_df = df[df["family"] == selected_family].reset_index(drop=True)
else:
    filtered_df = df

st.subheader(f"Results for '{search_query}' ({len(filtered_df)} plants)")
st.dataframe(
    filtered_df[["common_name", "scientific_name", "family", "genus"]],
    use_container_width=True,
)

# --------------------------------------------------------------------------
# Dynamic visualization #1 — family distribution bar chart (interactive)
# --------------------------------------------------------------------------
st.markdown("### 📊 Plant Family Distribution")

family_counts = (
    df["family"].value_counts().reset_index()
)
family_counts.columns = ["family", "count"]

fig_family = px.bar(
    family_counts,
    x="family",
    y="count",
    title=f"Families represented in search results for '{search_query}'",
    labels={"family": "Plant Family", "count": "Number of Species"},
    color="count",
    color_continuous_scale="Greens",
)
fig_family.update_layout(xaxis_tickangle=-40)
st.plotly_chart(fig_family, use_container_width=True)

# --------------------------------------------------------------------------
# Interactive control #3 — pick an individual plant to inspect
# --------------------------------------------------------------------------
st.markdown("### 🔍 Inspect a Specific Plant")

if filtered_df.empty:
    st.warning("No plants match this family filter. Try 'All' or a new search.")
    st.stop()

plant_labels = [
    f"{row.common_name} ({row.scientific_name})"
    for row in filtered_df.itertuples()
]
selected_label = st.selectbox("Choose a plant to view details", plant_labels)
selected_row = filtered_df.iloc[plant_labels.index(selected_label)]

with st.spinner("Fetching plant details..."):
    detail = get_plant_detail(int(selected_row["id"]), token)

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"**{selected_row['common_name']}**")
    st.markdown(f"*{selected_row['scientific_name']}*")
    st.markdown(f"Family: {selected_row['family']}")
    st.markdown(f"Genus: {selected_row['genus']}")
    if selected_row["image_url"]:
        st.image(selected_row["image_url"], caption=selected_row["common_name"])
    else:
        st.caption("No image available for this plant.")

with col2:
    growth = (detail.get("main_species") or {}).get("growth") or {}

    if not growth:
        st.info("No growing-condition data is available for this plant in Trefle.")
    else:
        # ---- Dynamic visualization #2 — growth condition index chart ----
        # These fields are all reported by Trefle on a comparable 0-10 scale,
        # so it's meaningful to plot them together.
        index_fields = {
            "Light needs": growth.get("light"),
            "Atmospheric humidity": growth.get("atmospheric_humidity"),
            "Soil humidity": growth.get("soil_humidity"),
            "Soil nutriments": growth.get("soil_nutriments"),
            "Soil salinity": growth.get("soil_salinity"),
        }
        index_data = {k: v for k, v in index_fields.items() if v is not None}

        if index_data:
            index_df = pd.DataFrame(
                {"Condition": list(index_data.keys()), "Score (0-10)": list(index_data.values())}
            )
            fig_growth = px.bar(
                index_df,
                x="Condition",
                y="Score (0-10)",
                range_y=[0, 10],
                title=f"Growing Condition Index — {selected_row['common_name']}",
                color="Score (0-10)",
                color_continuous_scale="Teal",
            )
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("No 0-10 scale growth index data available for this plant.")

        # ---- Extra numeric details, manually extracted/processed ----
        min_temp = (growth.get("minimum_temperature") or {}).get("deg_c")
        max_temp = (growth.get("maximum_temperature") or {}).get("deg_c")
        ph_min = growth.get("ph_minimum")
        ph_max = growth.get("ph_maximum")

        detail_cols = st.columns(2)
        with detail_cols[0]:
            if min_temp is not None and max_temp is not None:
                st.metric("Temperature range (°C)", f"{min_temp}° to {max_temp}°")
            else:
                st.caption("Temperature range: not reported")
        with detail_cols[1]:
            if ph_min is not None and ph_max is not None:
                st.metric("Soil pH range", f"{ph_min} to {ph_max}")
            else:
                st.caption("Soil pH range: not reported")

st.divider()
st.caption(
    "Data source: Trefle (trefle.io) — a global plant and botanical species database. "
    "All filtering, counting, and field extraction above is performed locally in Python."
)
