import streamlit as st
from app.db import init_db, list_posts, get_post_by_slug
from pathlib import Path


def render_post(post):
    st.title(post["title"])
    if post["cover_image"]:
        st.image(post["cover_image"], use_column_width=True)
    st.markdown(post["content_md"], unsafe_allow_html=False)


def main():
    st.set_page_config(page_title="Streamlit Blog", page_icon="📝", layout="centered")
    init_db()

    query_params = st.query_params
    slug = query_params.get("p", [None])[0] if isinstance(query_params.get("p"), list) else query_params.get("p")

    st.sidebar.page_link("pages/1_Blog.py", label="Home", icon="🏠")
    st.sidebar.page_link("pages/2_Admin.py", label="Admin", icon="🛠️")

    if slug:
        post = get_post_by_slug(slug)
        if post and post["published"] == 1:
            render_post(post)
        else:
            st.error("Post not found or unpublished")
    else:
        st.title("Blog")
        posts = list_posts(published_only=True)
        for post in posts:
            with st.container(border=True):
                st.subheader(post["title"])
                if post["cover_image"]:
                    st.image(post["cover_image"], use_column_width=True)
                st.markdown(post["content_md"][:300] + ("..." if len(post["content_md"]) > 300 else ""))
                st.link_button("Read more", url=f"?p={post['slug']}", use_container_width=False)


if __name__ == "__main__":
    main()