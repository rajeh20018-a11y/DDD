"""خادم الويب الرئيسي للنسخة الأولية - يعتمد على مكتبات Python القياسية فقط."""
import json
import mimetypes
import os
import csv
import io
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from database import get_places, create_plan, save_message, save_interest, get_interests, init_db

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

SECTIONS = {
    "360-tours": ("🧭", "جولات 360°", "تجوّل افتراضيًا داخل المواقع السياحية", "جولات تفاعلية غامرة داخل قرى ومعالم عسير، مع نقاط معلومات وصور وحكايات محلية."),
    "smart-assistant": ("🤖", "المساعد الذكي", "دليلك الشخصي في عسير", "اطرح أسئلتك، تعرّف على الوجهات المناسبة، واحصل على برنامج مقترح وفق اهتماماتك."),
    "trip-planner": ("🗺️", "تخطيط الرحلات", "رحلة مصممة على مقاسك", "حدّد المدة والميزانية وعدد المسافرين والاهتمامات لنقترح جدولًا يوميًا مرنًا."),
    "stays": ("🏨", "الفنادق والمنتجعات", "إقامة قريبة من التجربة", "استعرض خيارات الإقامة مع الموقع والسعر والتقييم وانتقل إلى منصة الحجز المناسبة."),
    "destinations": ("📍", "الوجهات السياحية", "كل عسير في مكان واحد", "اكتشف المعالم التراثية والطبيعية والترفيهية، واحفظ الأماكن التي تود زيارتها."),
    "food": ("🍽️", "المطاعم والمقاهي", "مذاقات محلية تستحق التجربة", "تعرّف على المطاعم الشعبية والمقاهي القريبة من كل وجهة."),
    "experiences": ("🎟️", "الفعاليات والتجارب", "عِش الثقافة المحلية", "اكتشف المهرجانات والجولات والأنشطة الموسمية والتجارب التي يقدمها أهل المنطقة."),
}

PAGE_ROUTES = {
    "tours-360": "tours-360.html", "ai-assistant": "ai-assistant.html",
    "trip-planner": "trip-planner.html", "hotels": "hotels.html",
    "destinations": "destinations.html", "restaurants": "restaurants.html",
    "events": "events.html", "interest": "interest.html",
}
# دعم الروابط المباشرة بصيغة اسم الملف، مثل tours-360.html
PAGE_ROUTES.update({filename: filename for filename in PAGE_ROUTES.values()})

SERVICE_DETAILS = {
    "tours-360": [("rijal-almaa", "جولة رجال ألمع", "تراث", "تجوّل بين القصور الحجرية والممرات التاريخية في القرية التراثية."), ("sawda", "جولة السودة", "طبيعة", "شاهد الغابات والقمم والإطلالات الجبلية في تجربة بانورامية."), ("habala", "جولة الحبلة", "مغامرة", "اكتشف المنحدرات والمسارات والقرية الجبلية الفريدة.")],
    "ai-assistant": [("destinations-guide", "دليل الوجهات", "اقتراحات", "مساعد يرشّح الوجهات المناسبة حسب وقتك واهتماماتك."), ("hotels-guide", "دليل الفنادق", "إقامة", "اقتراح أماكن إقامة قريبة من مسارك وضمن ميزانيتك."), ("smart-schedule", "المخطط الذكي", "برنامج", "إنشاء جدول يومي متوازن للرحلة خلال ثوانٍ.")],
    "trip-planner": [("heritage-trip", "رحلة تراثية", "ثقافة", "برنامج يركز على القرى والمتاحف والأسواق والحكايات المحلية."), ("nature-trip", "رحلة طبيعية", "استرخاء", "برنامج للجبال والغابات والأودية والإطلالات الهادئة."), ("adventure-trip", "رحلة مغامرات", "نشاط", "مسارات وتجارب وأنشطة خارجية لمحبي المغامرة.")],
    "hotels": [("heritage-lodges", "النُزل الريفية", "تراث", "إقامة دافئة بطابع معماري مستوحى من هوية عسير."), ("mountain-resorts", "المنتجعات الجبلية", "رفاهية", "منتجعات بإطلالات وخدمات متكاملة وسط الطبيعة."), ("city-hotels", "فنادق أبها", "مدينة", "فنادق عملية قريبة من المطاعم والخدمات والفعاليات.")],
    "destinations": [("heritage", "الوجهات التراثية", "تاريخ", "قرى وقصور ومتاحف تروي تاريخ عسير وثقافتها."), ("nature", "الوجهات الطبيعية", "طبيعة", "جبال وغابات وأودية ومشاهد خضراء ممتدة."), ("family", "الوجهات العائلية", "ترفيه", "متنزهات وبحيرات وأنشطة تناسب جميع أفراد العائلة.")],
    "restaurants": [("local-food", "المطاعم الشعبية", "محلي", "أطباق جنوبية أصيلة وتجارب طعام تعكس هوية المنطقة."), ("mountain-cafes", "المقاهي الجبلية", "قهوة", "قهوة سعودية وجلسات هادئة بإطلالات جميلة."), ("family-restaurants", "المطاعم العائلية", "عائلي", "خيارات متنوعة ومساحات مناسبة للعائلات والأطفال.")],
    "events": [("heritage-festivals", "المهرجانات التراثية", "ثقافة", "عروض وفنون وأسواق شعبية تحتفي بتراث المنطقة."), ("adventures", "تجارب المغامرة", "حركة", "مشي وتسلق واستكشاف بصحبة منظمي تجارب محليين."), ("local-experiences", "التجارب المحلية", "تذوق", "أسواق ومزارع وورش حرفية وتذوق منتجات عسير.")],
}
SERVICE_TITLES = {"tours-360": "جولات 360°", "ai-assistant": "المساعد الذكي", "trip-planner": "تخطيط الرحلات", "hotels": "الفنادق والمنتجعات", "destinations": "الوجهات السياحية", "restaurants": "المطاعم والمقاهي", "events": "الفعاليات والتجارب"}


def render_home():
    """دمج أجزاء الصفحة لتسهيل تعديل الرأس والتذييل لاحقًا."""
    header = (TEMPLATES_DIR / "header.html").read_text(encoding="utf-8")
    page = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
    footer = (TEMPLATES_DIR / "footer.html").read_text(encoding="utf-8")
    return page.replace("{{HEADER}}", header).replace("{{FOOTER}}", footer).encode("utf-8")


def render_section(slug):
    icon, title, subtitle, description = SECTIONS[slug]
    page = (TEMPLATES_DIR / "section.html").read_text(encoding="utf-8")
    values = {"{{ICON}}": icon, "{{TITLE}}": title, "{{SUBTITLE}}": subtitle, "{{DESCRIPTION}}": description}
    for key, value in values.items():
        page = page.replace(key, value)
    return page.encode("utf-8")


def render_service_detail(service, item_slug):
    item = next((entry for entry in SERVICE_DETAILS.get(service, []) if entry[0] == item_slug), None)
    if not item:
        return None
    _, title, category, description = item
    page = (TEMPLATES_DIR / "service-detail.html").read_text(encoding="utf-8")
    parent_title = SERVICE_TITLES.get(service, service.replace("-", " "))
    for key, value in {"{{TITLE}}": title, "{{CATEGORY}}": category, "{{DESCRIPTION}}": description, "{{SERVICE}}": service, "{{PARENT}}": parent_title}.items():
        page = page.replace(key, value)
    return page.encode("utf-8")


class AppHandler(BaseHTTPRequestHandler):
    def send_data(self, data, status=200, content_type="application/json; charset=utf-8"):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        """السماح لواجهة Live Server بإرسال البيانات إلى خادم Python المحلي."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self.send_data(render_home(), content_type="text/html; charset=utf-8")
        if path == "/service-detail.html":
            return self.send_data((BASE_DIR / "service-detail.html").read_bytes(), content_type="text/html; charset=utf-8")
        slug = path.strip("/")
        parts = slug.split("/")
        if len(parts) == 3 and parts[0] == "services":
            detail = render_service_detail(parts[1], parts[2])
            if detail:
                return self.send_data(detail, content_type="text/html; charset=utf-8")
        if slug in PAGE_ROUTES:
            page = TEMPLATES_DIR / "pages" / PAGE_ROUTES[slug]
            return self.send_data(page.read_bytes(), content_type="text/html; charset=utf-8")
        if slug in SECTIONS:
            return self.send_data(render_section(slug), content_type="text/html; charset=utf-8")
        if path == "/api/places":
            return self.send_data({"places": get_places()})
        if path == "/admin/interests":
            if not self.admin_allowed():
                return self.send_data({"error": "غير مصرح"}, 401)
            rows = get_interests()
            cards = "".join(f"<tr><td>{r['id']}</td><td>{html.escape(r['name'])}</td><td>{html.escape(r['phone'])}</td><td>{html.escape(r['city'])}</td><td>{html.escape(r['experience'])}</td><td>{r['created_at']}</td></tr>" for r in rows)
            html = f'''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><title>العملاء المهتمون</title><style>body{{font-family:Arial;padding:30px}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border:1px solid #ddd}}a{{display:inline-block;margin-bottom:20px}}</style><h1>العملاء المهتمون ({len(rows)})</h1><a href="/admin/interests.csv?key={self.admin_key()}">تصدير إلى Excel (CSV)</a><table><tr><th>#</th><th>الاسم</th><th>الجوال</th><th>المدينة</th><th>التجربة</th><th>التاريخ</th></tr>{cards}</table></html>'''
            return self.send_data(html.encode("utf-8"), content_type="text/html; charset=utf-8")
        if path == "/admin/interests.csv":
            if not self.admin_allowed():
                return self.send_data({"error": "غير مصرح"}, 401)
            rows = get_interests()
            output = io.StringIO(); writer = csv.writer(output)
            writer.writerow(["الرقم", "الاسم", "الجوال", "البريد", "المدينة", "الوجهة", "التجربة", "موعد السفر", "المسافرون", "موافقة التسويق", "تاريخ التسجيل"])
            for r in rows: writer.writerow([r["id"],r["name"],r["phone"],r["email"],r["city"],r["destination"],r["experience"],r["travel_date"],r["travelers"],r["marketing_consent"],r["created_at"]])
            data = ('\ufeff' + output.getvalue()).encode('utf-8')
            self.send_response(200); self.send_header("Content-Type", "text/csv; charset=utf-8"); self.send_header("Content-Disposition", "attachment; filename=asirx-interests.csv"); self.send_header("Content-Length", str(len(data))); self.end_headers(); return self.wfile.write(data)
        if path.startswith("/static/"):
            relative = path.removeprefix("/static/")
            target = (STATIC_DIR / relative).resolve()
            if STATIC_DIR.resolve() not in target.parents or not target.is_file():
                return self.send_data({"error": "الملف غير موجود"}, 404)
            return self.send_data(target.read_bytes(), content_type=mimetypes.guess_type(target)[0] or "application/octet-stream")
        self.send_data({"error": "المسار غير موجود"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if path == "/api/plan":
                return self.send_data(create_plan(payload))
            if path == "/api/contact":
                if not payload.get("name") or not payload.get("message"):
                    return self.send_data({"error": "الاسم والرسالة مطلوبان"}, 400)
                save_message(payload)
                return self.send_data({"message": "وصلت رسالتك، سنتواصل معك قريبًا."}, 201)
            if path == "/api/interests":
                interest_id = save_interest(payload)
                return self.send_data({"id": interest_id, "message": "شكرًا لتسجيل اهتمامك 🌿 تم استلام بياناتك وسنتواصل معك عند إطلاق التجربة والعروض المناسبة."}, 201)
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_data({"error": "بيانات الطلب غير صالحة", "detail": str(exc)}, 400)
        self.send_data({"error": "المسار غير موجود"}, 404)

    def admin_key(self):
        return os.environ.get("ADMIN_KEY", "change-me")

    def admin_allowed(self):
        from urllib.parse import parse_qs
        query = parse_qs(urlparse(self.path).query)
        return query.get("key", [""])[0] == self.admin_key()

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8000"))
    print(f"Rijal Explorer يعمل على http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), AppHandler).serve_forever()
