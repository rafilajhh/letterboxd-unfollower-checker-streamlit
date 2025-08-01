import streamlit as st
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import nest_asyncio

nest_asyncio.apply()

async def fetch_page(session, url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://letterboxd.com/",
        "Connection": "keep-alive"
    }
    async with session.get(url, headers=headers, timeout=30) as response:
        return await response.text()
    
async def get_profile_data(username):
    url = f"https://letterboxd.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    def get_count(tab):
        selector = f'a[href="/{username}/{tab}/"] > span.value'
        tag = soup.select_one(selector)
        return int(tag.text.replace(',', '')) if tag else 0

    followers = get_count("followers")
    following = get_count("following")
    max_pages = max(followers, following) / 25
    return int(max_pages) + 1

async def get_user_list(username, tab, max_pages):
    urls = [
        f"https://letterboxd.com/{username}/{tab}/page/{page}/"
        for page in range(1, max_pages + 1)
    ]
    
    user_list = []
    async with aiohttp.ClientSession() as session:
        htmls = await asyncio.gather(*[fetch_page(session, url) for url in urls])
        for html in htmls:
            soup = BeautifulSoup(html, "html.parser")
            user_blocks = soup.select("div.person-summary")
            if not user_blocks:
                continue
            for user in user_blocks:
                avatar_tag = user.select_one("a.avatar")
                if avatar_tag and avatar_tag.has_attr("href"):
                    user_lb = avatar_tag["href"].strip("/")
                    user_list.append(user_lb)
    return user_list


async def main_async(username):
    max_pages = await get_profile_data(username)
    followers = await get_user_list(username, "followers", max_pages)
    following = await get_user_list(username, "following", max_pages)
    return followers, following


st.title("🎬 Letterboxd Unfollower Checker")
st.write("**Use this tool to automatically compare your following and followers lists, and get a complete list of users who don't follow you back.**")

username = st.text_input("Letterboxd username: ").strip()

_, middle, _ = st.columns(3)
check_button = middle.button("Check now!", use_container_width=True)

if check_button and username:
    with st.status(f"Fetching account data for '{username}'...", expanded=True) as status:
        with st.spinner("Fetching followers and following...", show_time=True):
            followers, following = asyncio.run(main_async(username))

        status.update(label="Data loaded successfully!", state="complete", expanded=False)

    set_followers = set(followers)
    set_following = set(following)

    unfollowers = list(set_following - set_followers)
    unfollowing = list(set_followers - set_following)

    st.subheader(f"{username.title()}'s Profile:")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"- 🚀 **Following**: {len(following)}")
    with col2:
        st.write(f"- 🎟️ **Followers**: {len(followers)}")

    col3, col4 = st.columns(2)
    with col3:
        st.write(f"- 😒 **Doesn't Follow You Back**: {len(unfollowers)}")
    with col4:
        st.write(f"- 💔 **You Don't Follow Back**: {len(unfollowing)}")

    st.divider()
    col5, col6 = st.columns(2)
    with col5:
        st.subheader("Doesn't Follow You Back:")
        if unfollowers:
            st.caption("People you follow, but they don’t follow you")
            for i, user in enumerate(unfollowers, start=1):
                st.write(f"{i}. {user} : https://letterboxd.com/{user}/")
        elif not followers and not following:
            st.warning("You don't follow anyone and no one follows you.")
        else:
            st.success("Everyone you follow also follows you back! 🎉")

    with col6:
        st.subheader("You Don't Follow Back:")
        if unfollowing:
            st.caption("People who follow you, but you don’t follow them")
            for i, user in enumerate(unfollowing, start=1):
                st.write(f"{i}. {user} : https://letterboxd.com/{user}/")
        elif not followers and not following:
            st.warning("You don't follow anyone and no one follows you.")
        else:
            st.success("You follow back everyone who follows you! 👍")

    st.divider()
    st.markdown("🐞 Found a bug? Contact me — Made by [rafilajhh](https://letterboxd.com/rafilajhh/)")

