import streamlit as st

st.set_page_config(page_title="NCLEX Simulator", page_icon="🧪", layout="centered")

st.title("NCLEX Simulator (Smoke Test)")

st.write(
    "If you can see this text, your `app.py` is connected "
    "correctly and Streamlit is deploying from this GitHub repo."
)

question = "A client with heart failure reports sudden weight gain and shortness of breath. What is the priority nursing action?"
options = [
    "Reassure the client and schedule a follow-up visit",
    "Auscultate lung sounds and assess for crackles",
    "Encourage oral fluid intake",
    "Hold all medications until the provider is notified",
]

st.subheader("Sample Question")
answer = st.radio("Select your answer:", options)

if st.button("Submit"):
    if answer == "Auscultate lung sounds and assess for crackles":
        st.success("Correct ✅: Assess for fluid overload and pulmonary edema first.")
    else:
        st.error("Not quite. The priority is to assess for pulmonary congestion.")
