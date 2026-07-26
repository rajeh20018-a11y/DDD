"""إنشاء قاعدة SQLite وعمليات البيانات البسيطة للـ MVP."""
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).resolve().parent / "db.sqlite3"))

PLACES = [
    ("قرية رجال ألمع التراثية", "تراثية", "قلب الوجهة وبيوت حجرية ملونة تحكي تاريخ المنطقة.", "وسط القرية", 4.9, "🏛️"),
    ("متحف رجال ألمع", "تراثية", "مقتنيات ووثائق محلية داخل حصن تاريخي مميز.", "القرية التراثية", 4.8, "🗝️"),
    ("وادي ريم", "طبيعية", "مسار أخضر وهدوء مثالي للنزهات والتصوير.", "25 دقيقة", 4.7, "🌿"),
    ("ممشى السحاب", "طبيعية", "إطلالات جبلية واسعة وأجواء لطيفة وقت الغروب.", "35 دقيقة", 4.6, "⛰️"),
    ("مذاق ألمع", "مطاعم", "أطباق عسيرية محلية في أجواء مستوحاة من التراث.", "8 دقائق", 4.5, "🍲"),
    ("مقهى الجبل", "مقاهٍ", "قهوة سعودية وإطلالة هادئة على المدرجات الخضراء.", "12 دقيقة", 4.4, "☕"),
    ("نُزل القرية", "فنادق", "إقامة ريفية قريبة من أبرز المعالم التراثية.", "5 دقائق", 4.7, "🛖"),
]


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS places (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                category TEXT NOT NULL, description TEXT NOT NULL,
                distance TEXT NOT NULL, rating REAL NOT NULL, icon TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                email TEXT, message TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT,
                city TEXT NOT NULL, destination TEXT NOT NULL,
                experience TEXT NOT NULL, travel_date TEXT,
                travelers INTEGER, privacy_consent INTEGER NOT NULL,
                marketing_consent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL, path TEXT, visitor_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        columns = {row[1] for row in db.execute("PRAGMA table_info(interests)")}
        for name, definition in (("budget", "TEXT"), ("notes", "TEXT")):
            if name not in columns:
                db.execute(f"ALTER TABLE interests ADD COLUMN {name} {definition}")
        analytics_columns = {row[1] for row in db.execute("PRAGMA table_info(analytics)")}
        if "visitor_id" not in analytics_columns:
            db.execute("ALTER TABLE analytics ADD COLUMN visitor_id TEXT")
        if db.execute("SELECT COUNT(*) FROM places").fetchone()[0] == 0:
            db.executemany("INSERT INTO places(name,category,description,distance,rating,icon) VALUES(?,?,?,?,?,?)", PLACES)


def get_places():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM places ORDER BY rating DESC")]


def create_plan(data):
    days = max(1, min(int(data.get("days", 2)), 5))
    interests = data.get("interests", [])
    places = get_places()
    if interests:
        preferred = [p for p in places if p["category"] in interests]
        places = preferred + [p for p in places if p not in preferred]
    schedule = []
    for day in range(days):
        selected = places[(day * 2):(day * 2 + 2)] or places[:2]
        schedule.append({"day": day + 1, "title": "يوم بين التراث والطبيعة", "places": selected})
    return {"days": days, "budget": data.get("budget", "متوسطة"), "schedule": schedule}


def save_message(data):
    with connect() as db:
        db.execute("INSERT INTO messages(name,email,message) VALUES(?,?,?)", (data["name"], data.get("email", ""), data["message"]))


def save_interest(data):
    """حفظ بيانات العميل المهتم بعد التحقق الأساسي."""
    fields = ("name", "phone", "city", "destination", "experience")
    if any(not str(data.get(field, "")).strip() for field in fields):
        raise ValueError("يرجى تعبئة جميع الحقول المطلوبة")
    if not data.get("privacy_consent"):
        raise ValueError("يجب الموافقة على سياسة الخصوصية")
    travelers = data.get("travelers") or None
    if travelers is not None:
        travelers = max(1, min(int(travelers), 30))
    phone = "".join(char for char in str(data["phone"]) if char.isdigit())
    if len(phone) < 9:
        raise ValueError("رقم الجوال غير صالح")
    with connect() as db:
        if db.execute("SELECT 1 FROM interests WHERE REPLACE(REPLACE(REPLACE(phone,' ',''),'-',''),'+','') = ?", (phone,)).fetchone():
            raise ValueError("رقم الجوال مسجّل مسبقًا")
        cursor = db.execute("""INSERT INTO interests
            (name,phone,email,city,destination,experience,travel_date,travelers,privacy_consent,marketing_consent,budget,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (
            str(data["name"]).strip(), phone, str(data.get("email", "")).strip(),
            str(data["city"]).strip(), str(data["destination"]).strip(), str(data["experience"]).strip(),
            data.get("travel_date") or None, travelers, 1, 1 if data.get("marketing_consent") else 0,
            str(data.get("budget", "")).strip(), str(data.get("notes", "")).strip()
        ))
        return cursor.lastrowid


def get_interests():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM interests ORDER BY created_at DESC")]


def delete_interest(interest_id):
    with connect() as db:
        return db.execute("DELETE FROM interests WHERE id = ?", (interest_id,)).rowcount


def track_event(event, path="", visitor_id=""):
    allowed = {"site_visit", "tour_360_click", "trip_planner_click", "interest_form_open", "interest_form_complete", "whatsapp_click"}
    if event not in allowed:
        raise ValueError("حدث تتبع غير صالح")
    with connect() as db:
        db.execute("INSERT INTO analytics(event,path,visitor_id) VALUES(?,?,?)", (event, str(path)[:300], str(visitor_id)[:100]))


def get_analytics():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT event, COUNT(*) AS count FROM analytics GROUP BY event ORDER BY count DESC")]


def get_messages():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM messages ORDER BY created_at DESC")]


def delete_message(message_id):
    with connect() as db:
        return db.execute("DELETE FROM messages WHERE id = ?", (message_id,)).rowcount


def get_dashboard_summary():
    """Return the small aggregate dataset needed by the admin dashboard."""
    with connect() as db:
        totals = {
            "interests": db.execute("SELECT COUNT(*) FROM interests").fetchone()[0],
            "messages": db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            "visits": db.execute("""SELECT COUNT(DISTINCT CASE
                WHEN visitor_id IS NOT NULL AND visitor_id != '' THEN visitor_id
                ELSE 'legacy-' || id END) FROM analytics WHERE event = 'site_visit'""").fetchone()[0],
            "plans": db.execute("SELECT COUNT(*) FROM analytics WHERE event = 'trip_planner_click'").fetchone()[0],
        }
        daily = [dict(row) for row in db.execute("""
            SELECT date(created_at) AS day, COUNT(*) AS count
            FROM interests
            WHERE created_at >= datetime('now', '-6 days')
            GROUP BY date(created_at) ORDER BY day
        """)]
        experiences = [dict(row) for row in db.execute("""
            SELECT experience AS label, COUNT(*) AS count
            FROM interests GROUP BY experience ORDER BY count DESC
        """)]
        destinations = [dict(row) for row in db.execute("""
            SELECT destination AS label, COUNT(*) AS count FROM interests
            GROUP BY destination ORDER BY count DESC LIMIT 8
        """)]
        cities = [dict(row) for row in db.execute("""
            SELECT city AS label, COUNT(*) AS count FROM interests
            GROUP BY city ORDER BY count DESC LIMIT 8
        """)]
        return {"totals": totals, "daily": daily, "experiences": experiences,
                "destinations": destinations, "cities": cities}
