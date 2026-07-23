"""إنشاء قاعدة SQLite وعمليات البيانات البسيطة للـ MVP."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "db.sqlite3"

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
        """)
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
    with connect() as db:
        cursor = db.execute("""INSERT INTO interests
            (name,phone,email,city,destination,experience,travel_date,travelers,privacy_consent,marketing_consent)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", (
            str(data["name"]).strip(), str(data["phone"]).strip(), str(data.get("email", "")).strip(),
            str(data["city"]).strip(), str(data["destination"]).strip(), str(data["experience"]).strip(),
            data.get("travel_date") or None, travelers, 1, 1 if data.get("marketing_consent") else 0
        ))
        return cursor.lastrowid


def get_interests():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM interests ORDER BY created_at DESC")]
