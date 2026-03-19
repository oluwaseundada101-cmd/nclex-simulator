# NGN NCLEX Simulator — How to Run

## Option A: Run Locally on Your Laptop (Recommended)

This runs entirely on your computer. No internet required after setup.

### First-time setup (do this once)

1. **Install Python 3.11**
   - Go to: https://www.python.org/downloads/release/python-3119/
   - Scroll down, click **Windows installer (64-bit)**
   - Run the installer — **CHECK the box "Add Python to PATH"** before clicking Install

2. **Put all files in one folder**
   - Create a folder on your Desktop called `nclex-simulator`
   - Put these 3 files inside it:
     - `app.py`
     - `questions.json`
     - `RUN_LOCAL.bat`

### Every time you want to run it

1. Double-click **RUN_LOCAL.bat**
2. A black window opens and installs anything needed (first time only, ~1 min)
3. Your browser opens automatically at `http://localhost:8501`
4. Done — use the app just like the online version

To stop: close the black window, or press **Ctrl+C** inside it.

---

## Option B: Run via Streamlit Cloud (Online)

If your Streamlit Cloud account is blocked (Error 403):

1. Go to https://share.streamlit.io
2. Click **contact support** on the error page
3. Tell them: *"My free account was blocked for fair-use limits. I am a nursing student using this for personal NCLEX study. Please unblock."*
4. They usually respond within 24 hours and unblock you.

Once unblocked, your app will be back online at the same URL automatically
because your GitHub files are already up to date.

---

## How to Update Questions for a New Unit

1. Generate a new `questions.json` for your new unit (using the QUESTION_SCHEMA.md as a prompt guide)
2. Replace the `questions.json` file in your folder with the new one
3. If running locally: restart the app (close and double-click RUN_LOCAL.bat again)
4. If using Streamlit Cloud: upload the new `questions.json` to GitHub — it redeploys automatically

That's it. You never need to touch `app.py`.

---

## File Descriptions

| File | What it does |
|------|-------------|
| `app.py` | The simulator application — don't edit this |
| `questions.json` | Your question bank — replace this for each new unit |
| `requirements.txt` | Tells Streamlit Cloud which version to use |
| `RUN_LOCAL.bat` | Double-click to run on Windows |
| `QUESTION_SCHEMA.md` | Template for generating new questions with AI |
| `HOW_TO_RUN.md` | This file |
