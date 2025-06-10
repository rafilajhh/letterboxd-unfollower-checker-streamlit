import streamlit as st
from bs4 import BeautifulSoup
import requests

def get_user_list(username,tab):
    page = 1
    user_list = []
    while True:
        url = f"https://letterboxd.com/{username}/{tab}/page/{page}/"
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://letterboxd.com/",
        "Connection": "keep-alive"
        }
        response = requests.get(url,headers=headers,timeout=30)
        soup = BeautifulSoup(response.text, "html.parser")
        user_blocks = soup.select("div.person-summary")

        if not user_blocks:
            break

        for user in user_blocks:
            avatar_tag = user.select_one("a.avatar")
            if avatar_tag and avatar_tag.has_attr("href"):
                user_lb = avatar_tag["href"].strip("/")
                user_list.append(user_lb)
        page += 1
    return user_list


st.title("🎬 Letterboxd Unfollower Checker")
st.write("**Use this tool to automatically compare your following and followers lists, and get a complete list of users who don't follow you back.**")
username = st.text_input("Letterboxd username: ")
_,middle,_ = st.columns(3,vertical_alignment="bottom")
check_button = middle.button("Check now!",use_container_width=True)

if check_button and username:
    with st.status(f"Analyzing account data '{username}'...'",expanded=True) as status:
        with st.spinner(text="Fetching for data followers...",show_time=True):
            followers = get_user_list(username,"followers")

        with st.spinner(text="Fetching for data following...",show_time=True):
            following = get_user_list(username,"following")
        status.update(label=f"Data loaded successfully! Please see the results below.",state="complete",expanded=False)
    
    unfollowing = [user for user in followers if user not in following]
    unfollowers = [user for user in following if user not in followers] 


    st.subheader(f"{username.title()}'s Profile:")
    col1,col2 = st.columns(2)
    with col1:
        st.write(f"- 🚀 **Following**: {len(following)}")
    with col2:
        st.write(f"- 🎟️ **Followers**: {len(followers)}")
    col3,col4 = st.columns(2)
    with col3:
        st.write(f"- 😒 **Doesn't Follow You Back**: {len(unfollowers)}")
    with col4:
        st.write(f"- 💔 **You Don't Follow Back**: {len(unfollowing)}")

    st.divider()

    col5,col6 = st.columns(2)
    with col5:
        st.subheader("Doesn't Follow You Back:")
        if unfollowers:
            st.caption("People you follow, but they don’t follow you")
            for i, user in enumerate(unfollowers,start=1):
                st.write(f"{i}. {user} : https://letterboxd.com/{user}/")
        elif len(followers) == 0 or len(followers) == 0:
            st.warning("You don't follow anyone and no one follows you")
        else:
            st.success("Everyone you follow also follows you back! 🎉")

    with col6:
        st.subheader("You Don't Follow Back:")
        if unfollowing:
            st.caption("People who follow you, but you don’t follow them")
            for i, user in enumerate(unfollowing,start=1):
                st.write(f"{i}. {user} : https://letterboxd.com/{user}/")
        elif len(followers) == 0 or len(followers) == 0:
            st.warning("You don't follow anyone and no one follows you")
        else:
            st.success("You follow back everyone who follows you! 👍")

    st.divider()
    st.markdown("**Made by:** [rafilajhh](https://letterboxd.com/rafilajhh/)")
