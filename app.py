import requests
import json
import pandas as pd
import datetime as dt
import streamlit as st
import plotly.express as px
import time

# @st.cache
def get_token():

    url = "https://zoom.us/oauth/token?grant_type=account_credentials&account_id=QpgI8qwKRWqoMLsq86U9Hg"

    payload = {}
    auth_token = st.secrets["token"]["auth_token"]
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Cookie": "TS018dd1ba=01663b36a1194991630163c56912969935698aaa2a33a0ee810ddcbecd646f5daea83bc555efd8890887730b40a24318028fc17f69; TS01f92dc5=01663b36a1b9a96cea77eb07d086d4137aa7b3e04566e40df3ea74bf203e8ade5fb0b1d4fe150c401444f59e360bfdd5b790169011; __cf_bm=mo2H9ar6h_d4uYsC9SDos7T3oSGeFzHUtWzOcaUalts-1671459548-0-AWbHafN6vZP/f0CUp9OXwgORVCAfZfAgQLTFayb3Flkt0irphltu2LTiGfjd9GfsHUiPwT/D2l3/JIMWj8m8xzA=; _zm_chtaid=275; _zm_ctaid=zJCcWkV-TNGHo2TjyVh44w.1671459858576.d5d43daf7e700fdd1d000921698c1378; _zm_mtk_guid=5b4d4a664cc540dfa8f5b1f5997e7178; _zm_page_auth=us06_c_9x4NQ_P1TTWy00RFJkju0g; _zm_ssid=us06_c_4MhVHnsYTR-tKK8Xlh9WfA; cred=0D856E9DC672A09B750A7D1D25E50BFE",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    data = json.loads(response.text)
    token = data["access_token"]

    return token


def get_attendee_data(meeting_id, token):

    url = f"https://api.zoom.us/v2/report/meetings/{meeting_id}/participants?page_size=300&include_fields=registrant_id"

    payload = {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Cookie": "TS018dd1ba=01fdd41ebb0f3a8443fc13ae2a95e4e1d44d8e7a1a4e1549e010a6d95295bfb862bd6abd572673ce76d2281675b223f31c72291957; __cf_bm=nw.19Qizl4qrpDcidtmIAf7vqt0NURpBZTN5RcmdJ1s-1671452186-0-AR4pMXu3bw5WCcwO5ssp6e1RLR8xwfBa1WS/vZEYcuerfwMw2pwAWY+0jolXtUGJahIGvmXet6qzYF0TiW3Oe5g=; _zm_mtk_guid=5b4d4a664cc540dfa8f5b1f5997e7178; _zm_page_auth=us06_c_9x4NQ_P1TTWy00RFJkju0g; _zm_ssid=us06_c_4MhVHnsYTR-tKK8Xlh9WfA; TS01f92dc5=01fdd41ebb0f3a8443fc13ae2a95e4e1d44d8e7a1a4e1549e010a6d95295bfb862bd6abd572673ce76d2281675b223f31c72291957; cred=C3303E69F7C95F2A210E12317553CE6F",
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)

    df = pd.DataFrame(data["participants"])
    df["join_time"] = df["join_time"].apply(
        lambda x: dt.datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
        + dt.timedelta(hours=5, minutes=30)
    )
    df["leave_time"] = df["leave_time"].apply(
        lambda x: dt.datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")
        + dt.timedelta(hours=5, minutes=30)
    )

    return df


# get the access token of zoom api
token = get_token()

# Frontend
col1, col2, col3 = st.columns(3)
with col1:
    st.write("")
with col2:
    st.image("black_logo.png", width=225)
    st.write("")
with col3:
    st.write("")

st.write("----")

st.markdown(
    "<h2 style='text-align: center; color: black;'>Analyze Live Sessions - LA Cohorts</h2>",
    unsafe_allow_html=True,
)

st.write("----")

# get meeting id from the user
meeting_id = st.text_input("Enter the meeting ID of the live session")

if st.button("Analyze Live Session"):
    with st.spinner("Analyzing..."):
        df = get_attendee_data(meeting_id, token)
        # df = df.groupby("user_email", as_index=False).max()
        df = df.groupby("user_email", as_index=False).agg(
            {"join_time": "min", "leave_time": "max", "duration": "sum", "name": "max"}
        )

        df["join_time_only"] = df["join_time"].apply(lambda x: x.strftime("%H:%M:%S"))

        st.write("----")
        st.subheader("Live Session Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:
            total_users_joined = df["user_email"].unique().shape[0]
            st.metric("Total users joined", f"{total_users_joined}")

        with col2:
            joined_before_cutoff = df[df["join_time_only"] < "09:10:00"].shape[0]
            st.metric(
                "Joined before 09:10 AM",
                f"{round((joined_before_cutoff/total_users_joined)*100,1)}% ({joined_before_cutoff})",
            )

        with col3:
            ideal_duration = df[df["duration"] > 2700].shape[0]
            st.metric(
                "> 45 mins duration",
                f"{round((ideal_duration/total_users_joined)*100,1)}% ({ideal_duration})",
            )

        st.write("------")
        st.subheader("Join and Leave Time Analysis")

        fig = px.scatter(
            df, x="join_time", y="duration", color_discrete_sequence=["green"]
        )
        fig.add_trace(
            px.scatter(
                df, x="leave_time", y="duration", color_discrete_sequence=["red"]
            ).data[0]
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        st.write("------")
        st.subheader("User Data")
        df_user_data = df[["name", "user_email", "join_time", "leave_time", "duration"]]
        df_user_data["Points"] = df_user_data["duration"].apply(
            lambda x: 100 if x >= 2700 else round(100 * x / 2700)
        )
        st.dataframe(df_user_data)

        st.write("-----")

        @st.cache
        def convert_df(df_user_data):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df_user_data.to_csv().encode("utf-8")

        csv = convert_df(df_user_data)

        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="user_data.csv",
            mime="text/csv",
        )

        st.write("-----")
