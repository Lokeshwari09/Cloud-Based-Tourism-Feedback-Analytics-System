import csv, io, json, os, sqlite3
from datetime import datetime
from flask import Flask, Response, jsonify, render_template, request
from analyzer import analyze, top_keywords

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE, "data", "feedback.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
app = Flask(__name__)

SAMPLES = [
    ("Munnar", 5, "Beautiful scenic tea gardens and very friendly guide. Loved the peaceful views."),
    ("Munnar", 2, "Hotel room was dirty and the staff were rude. Too expensive for the service."),
    ("Goa", 4, "Great beach, delicious seafood at the restaurant. A bit crowded but worth it."),
    ("Goa", 1, "Terrible taxi scam at the airport, felt unsafe. Worst experience."),
    ("Jaipur", 5, "Amazing fort and excellent guide. Food was fresh and affordable."),
    ("Jaipur", 3, "Nice temple but traffic was slow and the road was noisy."),
    ("Kodaikanal", 4, "Comfortable resort, clean rooms and helpful staff. Recommend it."),
    ("Kodaikanal", 2, "Bus was late and the washroom was smelly. Disappointing trip."),
    ("Ooty", 5, "Fantastic hill views, perfect weather and a smooth train ride."),
    ("Ooty", 2, "Ticket prices are overpriced and the park was not clean."),
    ("Kerala Backwaters", 5, "Best houseboat stay. Wonderful food and friendly, polite crew."),
    ("Kerala Backwaters", 3, "Good views but the boat was cold and service was slow."),
]


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def add(con, destination, rating, comment):
    a = analyze(comment, rating)
    con.execute("INSERT INTO feedback(destination,rating,comment,sentiment,score,topics,created_at) VALUES(?,?,?,?,?,?,?)",
                (destination, rating, comment, a["label"], a["score"], json.dumps(a["topics"]),
                 datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    return a


def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY AUTOINCREMENT, destination TEXT, rating INTEGER, comment TEXT,
            sentiment TEXT, score REAL, topics TEXT, created_at TEXT)""")
        if os.environ.get("SEED", "1") == "1" and con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] == 0:
            for d, r, c in SAMPLES:
                add(con, d, r, c)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/feedback")
def post_feedback():
    d = request.get_json(silent=True) or request.form
    dest, comment = (d.get("destination") or "").strip(), (d.get("comment") or "").strip()
    if not dest or not comment:
        return {"error": "destination and comment are required"}, 400
    rating = int(d.get("rating") or 3)
    with db() as con:
        a = add(con, dest, rating, comment)
    return jsonify(a), 201


@app.get("/api/feedback")
def list_feedback():
    with db() as con:
        rows = con.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT 50").fetchall()
    return jsonify([dict(r, topics=json.loads(r["topics"])) for r in rows])


@app.post("/api/upload")
def upload_csv():
    f = request.files.get("file")
    if not f:
        return {"error": "attach a CSV as 'file' (destination,rating,comment)"}, 400
    n = 0
    with db() as con:
        for row in csv.DictReader(io.StringIO(f.read().decode("utf-8"))):
            if row.get("destination") and row.get("comment"):
                add(con, row["destination"], int(row.get("rating") or 3), row["comment"])
                n += 1
    return {"imported": n}


@app.get("/api/stats")
def stats():
    with db() as con:
        rows = [dict(r) for r in con.execute("SELECT * FROM feedback")]
    sent = {"positive": 0, "neutral": 0, "negative": 0}
    dest, topics, daily = {}, {}, {}
    for r in rows:
        sent[r["sentiment"]] += 1
        dest.setdefault(r["destination"], []).append(r["score"])
        for t in json.loads(r["topics"]):
            topics.setdefault(t, []).append(r["score"])
        daily.setdefault(r["created_at"][:10], []).append(r["score"])
    avg = lambda v: round(sum(v) / len(v), 3)
    return jsonify({
        "total": len(rows), "sentiment": sent,
        "by_destination": {k: avg(v) for k, v in dest.items()},
        "by_topic": {k: {"avg": avg(v), "count": len(v)} for k, v in topics.items()},
        "trend": {k: avg(v) for k, v in sorted(daily.items())},
        "keywords": top_keywords([r["comment"] for r in rows]),
    })


@app.get("/export.csv")
def export():
    with db() as con:
        rows = con.execute("SELECT destination,rating,comment,sentiment,score,created_at FROM feedback").fetchall()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["destination", "rating", "comment", "sentiment", "score", "created_at"])
    w.writerows([tuple(r) for r in rows])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=feedback.csv"})


init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
