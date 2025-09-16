from flask import Flask, render_template, request, redirect, session
from auth import check_admin_password
import json
import os
from sqlite_logger import get_logs, init_db

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this!

LOG_FILE = "proxy_logs.json"

# Load logs from file
def load_logs():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except Exception:
                    continue
    return logs

def avatar_for_hash(user_hash):
    idx = int(user_hash, 16) % 10 + 1
    return f"/static/avatars/{idx}.png"

# Initialize the SQLite database
init_db()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if check_admin_password(request.form["password"]):
            session["admin"] = True
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    masked_type = request.args.get("masked_type", "")
    min_count = request.args.get("min_count", "")
    # Load logs from SQLite
    logs = get_logs(masked_type if masked_type else None)
    # Filtering by min_count
    if min_count:
        try:
            min_count = int(min_count)
            logs = [log for log in logs if log.get("count", 0) >= min_count]
        except ValueError:
            pass
    for log in logs:
        log["avatar"] = avatar_for_hash(log.get("masked_value", "0"))
    return render_template("dashboard.html", logs=logs, masked_type=masked_type, min_count=min_count, file_type="", status="", date="")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(port=9001, debug=True) 