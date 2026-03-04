import streamlit as st
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
import asyncio
import nest_asyncio
import random

nest_asyncio.apply()

semaphore = asyncio.Semaphore(5)

async def fetch_page(session, url):
    timeout = 30
    async with semaphore:
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            response = await session.get(url, timeout=timeout)
            
            if response.status_code != 200:
                print(f"Gagal fetch {url}, status: {response.status_code}")
                return ""
            
            return response.text
            
        except Exception as e:
            print(f"Error saat fetch {url}: {e}")
            return ""

async def get_profile_data(username):
    url = f"https://letterboxd.com/{username}/"
    
    async with AsyncSession(impersonate="chrome") as session:
        response = await session.get(url, timeout=30)
        
        if response.status_code != 200:
            return 0, 0 
            
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    def get_count(tab):
        selector = f'a[href="/{username.lower()}/{tab}/"] > span.value'
        tag = soup.select_one(selector)
        return int(tag.text.replace(',', '')) if tag else 0

    followers = get_count("followers")
    following = get_count("following")
    max_pages_followers = int(followers / 25) + 1
    max_pages_following = int   (following / 25) + 1
    return max_pages_followers, max_pages_following, followers, following

async def get_user_list(username, tab,  max_pages_followers, max_pages_following):
    if tab == "followers":
        urls = [
            f"https://letterboxd.com/{username}/{tab}/page/{page}/"
            for page in range(1, max_pages_followers + 1)
        ]
    else:
        urls = [
            f"https://letterboxd.com/{username}/{tab}/page/{page}/"
            for page in range(1, max_pages_following + 1)
        ]

    user_list = []
    async with AsyncSession(impersonate="chrome") as session:
        htmls = await asyncio.gather(*[fetch_page(session, url) for url in urls])
        for html in htmls:
            if not html:
                continue
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

async def main_async(username, max_pages_followers=0, max_pages_following=0):
    print(f"Processing username: {username}, max_pages_followers: {max_pages_followers}, max_pages_following: {max_pages_following}")
    followers_list = await get_user_list(username, "followers", max_pages_followers, max_pages_following)
    following_list = await get_user_list(username, "following", max_pages_followers, max_pages_following)
    return followers_list, following_list


st.title("🎬 Letterboxd Unfollower Checker")
st.write("**Use this tool to automatically compare your following and followers lists, and get a complete list of users who don't follow you back.**")

username = st.text_input("Letterboxd username: ").strip()

_, middle, _ = st.columns(3)
check_button = middle.button("Check now!", use_container_width=True)

if check_button and username:
    max_pages_followers, max_pages_following, followers, following = asyncio.run(get_profile_data(username))

    if max_pages_followers > 256 or max_pages_following > 256:
        st.warning("This account has too many followers or following. The tool can only check up to 6400 followers/following due to Letterboxd's pagination limits.")
    else:
        with st.status(f"Fetching account data for '{username}'...", expanded=True) as status:
            with st.spinner("Fetching followers and following...", show_time=True):
                followers_list, following_list = asyncio.run(main_async(username, max_pages_followers, max_pages_following))

            status.update(label="Data loaded successfully!", state="complete", expanded=False)
        
        set_followers = set(followers_list)
        set_following = set(following_list)

        unfollowers = list(set_following - set_followers)
        unfollowing = list(set_followers - set_following)

        if followers != len(followers_list) or following != len(following_list):
            st.warning("Letterboxd website might down or this website is blocked by Letterboxd. Please try again later.")
        else:
            st.subheader(f"{username.title()}'s Profile:")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"- 🚀 **Following**: {following}")
            with col2:
                st.write(f"- 🎟️ **Followers**: {followers}")
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