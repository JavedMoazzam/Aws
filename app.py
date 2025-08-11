import os
from typing import Dict, List, Tuple, Any

import streamlit as st
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


# ---- Configuration ----
DEFAULT_MONGODB_URI = (
    os.getenv(
        "MONGODB_URI",
        "mongodb+srv://testdb:dbUsername@cluster.di9pq.mongodb.net/",
    )
)
DB_NAME = "hotels"
COLLECTION_NAME = "hotel_list"


# ---- Connection Helpers ----
@st.cache_resource(show_spinner=False)
def get_mongo_collection(uri: str = DEFAULT_MONGODB_URI) -> Collection:
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    # Trigger a quick server selection to fail fast if misconfigured
    client.admin.command("ping")
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


@st.cache_data(show_spinner=False)
def get_filter_options(collection: Collection) -> Tuple[List[str], List[str], float, float]:
    try:
        places = sorted([p for p in collection.distinct("place") if isinstance(p, str)])
        states = sorted([s for s in collection.distinct("state") if isinstance(s, str)])

        # Compute rating range (min/max) from data; fall back to sensible defaults
        pipeline = [
            {"$match": {"rating": {"$type": ["double", "int", "long", "decimal"]}}},
            {
                "$group": {
                    "_id": None,
                    "min_rating": {"$min": "$rating"},
                    "max_rating": {"$max": "$rating"},
                }
            },
        ]
        agg = list(collection.aggregate(pipeline))
        if agg:
            min_rating = float(agg[0].get("min_rating", 0.0))
            max_rating = float(agg[0].get("max_rating", 5.0))
        else:
            # If no numeric ratings found, provide a generic range
            min_rating, max_rating = 0.0, 5.0
    except PyMongoError:
        places, states, min_rating, max_rating = [], [], 0.0, 5.0

    return places, states, min_rating, max_rating


def build_query(selected_places: List[str], selected_states: List[str], rating_range: Tuple[float, float]) -> Dict[str, Any]:
    filters: List[Dict[str, Any]] = []

    if selected_places:
        filters.append({"place": {"$in": selected_places}})

    if selected_states:
        filters.append({"state": {"$in": selected_states}})

    if rating_range:
        min_r, max_r = rating_range
        filters.append({"rating": {"$gte": float(min_r), "$lte": float(max_r)}})

    return {"$and": filters} if filters else {}


def get_current_index(state_key: str, max_index: int) -> int:
    if state_key not in st.session_state:
        st.session_state[state_key] = 0
    current = int(st.session_state[state_key])
    if max_index < 0:
        return 0
    return max(0, min(current, max_index))


def set_current_index(state_key: str, new_index: int) -> None:
    st.session_state[state_key] = max(0, new_index)


# ---- UI ----
def main() -> None:
    st.set_page_config(page_title="Hotel Browser", page_icon="🏨", layout="centered")
    st.title("🏨 Hotel Browser")
    st.caption("Filter and browse hotels from MongoDB, one at a time")

    # Connection
    try:
        collection = get_mongo_collection()
    except Exception as e:
        st.error("Failed to connect to MongoDB. Check your URI or network.")
        with st.expander("Error Details"):
            st.exception(e)
        st.stop()

    # Sidebar Filters
    st.sidebar.header("Filters")
    places, states, min_rating, max_rating = get_filter_options(collection)

    selected_places = st.sidebar.multiselect(
        "Place",
        options=places,
        default=places,
        help="Filter by place. If none selected, all places are included.",
    )

    selected_states = st.sidebar.multiselect(
        "State",
        options=states,
        default=states,
        help="Filter by state. If none selected, all states are included.",
    )

    rating_min, rating_max = st.sidebar.slider(
        "Rating range",
        min_value=float(min_rating),
        max_value=float(max_rating if max_rating > min_rating else min_rating + 5.0),
        value=(float(min_rating), float(max_rating if max_rating > min_rating else min_rating + 5.0)),
        step=0.1,
        help="Filter by rating range",
    )

    # Treat empty selections as no filter
    places_filter = selected_places or []
    states_filter = selected_states or []

    query = build_query(places_filter, states_filter, (rating_min, rating_max))

    # Fetch count and current doc
    try:
        total_count = collection.count_documents(query)
    except PyMongoError as e:
        st.error("Failed to query hotels.")
        with st.expander("Error Details"):
            st.exception(e)
        st.stop()

    st.write(f"Results: {total_count}")

    if total_count == 0:
        st.info("No hotels match the selected filters.")
        st.stop()

    # Pagination (one-by-one)
    state_key = "current_hotel_index"

    # Reset index when filters change by using a simple key composed of filters
    filter_key = (tuple(sorted(places_filter)), tuple(sorted(states_filter)), round(rating_min, 2), round(rating_max, 2))
    if getattr(st.session_state, "last_filter_key", None) != filter_key:
        set_current_index(state_key, 0)
        st.session_state["last_filter_key"] = filter_key

    current_index = get_current_index(state_key, total_count - 1)

    # Controls
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Prev", use_container_width=True, disabled=current_index <= 0):
            set_current_index(state_key, current_index - 1)
            st.rerun()
    with col_info:
        st.markdown(
            f"<div style='text-align:center'>Hotel {current_index + 1} of {total_count}</div>",
            unsafe_allow_html=True,
        )
    with col_next:
        if st.button("Next ➡️", use_container_width=True, disabled=current_index >= total_count - 1):
            set_current_index(state_key, current_index + 1)
            st.rerun()

    # Fetch the current hotel document
    try:
        cursor = (
            collection
            .find(query, projection={"_id": 0})
            .sort([("name", 1), ("rating", -1)])
            .skip(current_index)
            .limit(1)
        )
        hotel = next(cursor, None)
    except PyMongoError as e:
        st.error("Failed to fetch hotel document.")
        with st.expander("Error Details"):
            st.exception(e)
        st.stop()

    if not hotel:
        st.warning("Unexpected: No hotel found at the current index.")
        st.stop()

    # Display hotel details
    name = hotel.get("name", "Unknown Hotel")
    rating = hotel.get("rating", "-")
    place = hotel.get("place", "-")
    state = hotel.get("state", "-")
    country = hotel.get("country", "-")

    st.subheader(name)

    meta_cols = st.columns(3)
    meta_cols[0].metric("Rating", f"{rating}")
    meta_cols[1].write(f"📍 {place}, {state}")
    meta_cols[2].write(f"🌎 {country}")

    with st.expander("Raw document"):
        st.json(hotel)


if __name__ == "__main__":
    main()