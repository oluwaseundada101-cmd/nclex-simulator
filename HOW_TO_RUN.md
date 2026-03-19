# How to Run — NGN NCLEX Simulator v4

Four ways to run: Local (Python), Docker (local), Render.com (free cloud), HuggingFace Spaces (free cloud).

---

## Option 1 — Run Locally (Recommended for Development)

### Requirements
- Python **3.11** from https://www.python.org/downloads/ (NOT 3.12, 3.13, or 3.15)
- `pip` (comes with Python)

### Steps

```bash
# 1. Unzip the project folder and open a terminal inside it
cd ngn_app_v4

# 2. (Optional) Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app will open at http://localhost:8501 in your browser.

### Adding New Question Banks
- Drop any `.json` file following the schema in `QUESTION_SCHEMA.md` into the `ngn_app_v4/` folder
- Click **🔄 Reload Question Banks** in the sidebar — no restart needed

---

## Option 2 — Run with Docker (No Python Install Required)

### Requirements
- Docker Desktop: https://www.docker.com/products/docker-desktop/

### Steps

```bash
# 1. Open a terminal in the ngn_app_v4 folder

# 2. Build and start the container
docker compose up --build

# 3. Open your browser to:
http://localhost:8501
```

To stop:
```bash
docker compose down
```

Your progress database (`progress.db`) is persisted in a Docker volume, so scores survive container restarts.

---

## Option 3 — Deploy to Render.com (Free Cloud Hosting)

### One-time setup
1. Create a free account at https://render.com
2. Push this folder to a GitHub repo
3. In Render dashboard: **New → Web Service → Connect GitHub repo**
4. Render auto-detects `render.yaml` and configures the service
5. Click **Deploy** — your app is live at `https://your-app.onrender.com`

### Notes
- Free tier sleeps after 15 minutes of inactivity (first request takes ~30s to wake)
- `progress.db` does NOT persist on Render free tier — use a paid plan or Render Disk for persistence

---

## Option 4 — Deploy to HuggingFace Spaces (Free GPU/CPU Hosting)

### One-time setup
1. Create a free account at https://huggingface.co
2. Create a new Space: **New Space → Docker SDK**
3. Upload all files from `ngn_app_v4/` to the Space (or connect your GitHub repo)
4. The `README.md` at the root contains the required HuggingFace frontmatter:
   ```
   ---
   sdk: docker
   app_port: 8501
   ---
   ```
5. The Space builds and deploys automatically

### Notes
- HuggingFace Spaces with Docker SDK supports `app_port: 8501` which maps to your Streamlit server
- `progress.db` is stored on the Space's ephemeral disk — progress may reset if the Space is restarted

---

## Option 5 — Windows Quick Launch (RUN_LOCAL.bat)

Double-click `RUN_LOCAL.bat` — it handles the venv, install, and launch in one step.

> ⚠️ Requires Python 3.11 already installed and available as `python` in your PATH.

---

## File Reference

| File | Purpose |
|------|---------|
| `app.py` | Main entry point |
| `config.py` | Layer info, stop rules, badge maps |
| `grading.py` | Scoring logic + miss-type inference |
| `persistence.py` | SQLite progress tracking |
| `renderers.py` | Question rendering (all 6 types) |
| `home.py` | Home screen, bank cards, session settings |
| `questions.json` | Sample question bank (Unit 4) |
| `QUESTION_SCHEMA.md` | Full JSON schema documentation |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Local Docker orchestration |
| `render.yaml` | Render.com auto-deploy config |
| `README.md` | HuggingFace Space config header |

---

## Troubleshooting

### "No module named streamlit"
Run `pip install -r requirements.txt` again.

### "streamlit_autorefresh not found"
Run `pip install streamlit-autorefresh==1.0.1`. The timer still works without it (manual refresh), but live countdown requires this package.

### Questions not updating after adding a new JSON file
Click **🔄 Reload Question Banks** in the sidebar. This clears the cache and re-reads all JSON files.

### "JSONDecodeError" in sidebar
Your JSON file has a syntax error. Use https://jsonlint.com/ to validate it. The app will show the exact error line in the sidebar.

### Progress database error
Delete `progress.db` from the app folder and restart — the database is recreated automatically.

### Python 3.15 installation errors (numpy, etc.)
Python 3.15 is too new and not compatible with the required packages. Install Python 3.11 specifically from https://www.python.org/downloads/
