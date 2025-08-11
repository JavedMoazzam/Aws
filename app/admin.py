import streamlit as st
from pathlib import Path
from app.db import init_db, list_posts, create_post, update_post, delete_post, get_post_by_id
from app.utils import slugify, save_uploaded_file
from app.security import hash_password, verify_password
from app.db import get_user_by_username, create_user


def ensure_admin_user():
    admin_username = st.secrets.get("auth", {}).get("admin_username", "admin")
    admin_password = st.secrets.get("auth", {}).get("admin_password", "change-me")
    user = get_user_by_username(admin_username)
    if user is None:
        password_hash = hash_password(admin_password)
        create_user(admin_username, password_hash, role="admin")


def admin_login() -> bool:
    if "auth_user" in st.session_state:
        return True

    st.subheader("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        user = get_user_by_username(username)
        if user and verify_password(password, user["password_hash"]):
            st.session_state["auth_user"] = dict(user)
            st.success("Logged in")
            st.rerun()
        else:
            st.error("Invalid credentials")
    return False


def admin_panel():
    st.set_page_config(page_title="Admin - Streamlit Blog", page_icon="🛠️", layout="wide")
    init_db()
    ensure_admin_user()

    if not admin_login():
        return

    st.title("Blog Admin Panel")

    with st.sidebar:
        st.write(f"Logged in as: {st.session_state['auth_user']['username']}")
        if st.button("Logout"):
            st.session_state.pop("auth_user", None)
            st.rerun()

    tab_list, tab_create = st.tabs(["Posts", "Create Post"])

    with tab_create:
        with st.form("create_post_form"):
            title = st.text_input("Title")
            slug = st.text_input("Slug", value="", placeholder="auto-generated from title if empty")
            content_md = st.text_area("Content (Markdown)", height=300)
            cover = st.file_uploader("Cover Image", type=["png", "jpg", "jpeg", "gif"])
            published = st.checkbox("Published", value=False)
            submitted = st.form_submit_button("Create", type="primary")

        if submitted:
            if not title or not content_md:
                st.error("Title and content are required")
            else:
                use_slug = slugify(slug or title)
                cover_path = None
                if cover is not None:
                    cover_path = save_uploaded_file(cover.getvalue(), cover.name)
                post_id = create_post(title, use_slug, content_md, cover_path, published)
                st.success("Post created")
                st.rerun()

    with tab_list:
        posts = list_posts(published_only=False)
        for post in posts:
            with st.expander(f"{post['title']} ({'Published' if post['published'] else 'Draft'})"):
                with st.form(f"edit_form_{post['id']}"):
                    title = st.text_input("Title", value=post["title"])
                    slug = st.text_input("Slug", value=post["slug"])
                    content_md = st.text_area("Content (Markdown)", value=post["content_md"], height=250)
                    published = st.checkbox("Published", value=bool(post["published"]))
                    new_cover = st.file_uploader("Replace Cover Image", type=["png", "jpg", "jpeg", "gif"], key=f"cover_{post['id']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        save_btn = st.form_submit_button("Save", type="primary")
                    with col2:
                        delete_btn = st.form_submit_button("Delete", type="secondary")

                if save_btn:
                    cover_path = post["cover_image"]
                    if new_cover is not None:
                        cover_path = save_uploaded_file(new_cover.getvalue(), new_cover.name)
                    update_post(post["id"], title, slugify(slug), content_md, cover_path, published)
                    st.success("Saved")
                    st.rerun()

                if delete_btn:
                    delete_post(post["id"])
                    st.warning("Deleted")
                    st.rerun()


if __name__ == "__main__":
    admin_panel()