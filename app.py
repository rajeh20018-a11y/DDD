"""خادم الويب الرئيسي للنسخة الأولية - يعتمد على مكتبات Python القياسية فقط."""
import json
import mimetypes
import os
import csv
import io
import html
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from database import (get_places, create_plan, save_message, save_interest,
                      get_interests, delete_interest, track_event, get_analytics, init_db,
                      get_messages, delete_message, get_dashboard_summary)

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
    page = page.replace('href="/#interest"', 'href="/interest.html"')
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
    page = page.replace('href="/interest/"', 'href="/interest.html"')
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
        if path in ("/ddd", "/ddd/"):
            return self.send_data((TEMPLATES_DIR / "admin.html").read_bytes(), content_type="text/html; charset=utf-8")
        if path in ("/admin", "/admin/", "/admin/interests"):
            self.send_response(302)
            self.send_header("Location", "/ddd")
            self.end_headers()
            return
        if path == "/api/admin/dashboard":
            if not self.admin_allowed():
                return self.send_data({"error": "غير مصرح"}, 401)
            return self.send_data({
                "summary": get_dashboard_summary(),
                "interests": get_interests(),
                "messages": get_messages(),
                "analytics": get_analytics(),
            })
        if path == "/admin/interests-legacy":
            if not self.admin_allowed():
                return self.send_data({"error": "غير مصرح"}, 401)
            rows = get_interests()
            key = html.escape(self.admin_key(), quote=True)
            stats = {}
            for row in rows: stats[row["experience"]] = stats.get(row["experience"], 0) + 1
            cards = "".join(f'''<tr data-service="{html.escape(r['experience'], quote=True)}"><td>{html.escape(r['name'])}</td><td>{html.escape(r['phone'])}</td><td>{html.escape(r['city'])}</td><td>{html.escape(r['experience'])}</td><td>{html.escape(r['destination'])}</td><td>{html.escape(r['travel_date'] or '-')}</td><td>{r['created_at']}</td><td><button onclick="removeRow({r['id']},this)">حذف</button></td></tr>''' for r in rows)
            options = "".join(f'<option>{html.escape(name)}</option>' for name in sorted(stats))
            counts = "".join(f'<span>{html.escape(name)}: <b>{count}</b></span>' for name,count in stats.items())
            analytics = "".join(f'<span>{html.escape(x["event"])}: <b>{x["count"]}</b></span>' for x in get_analytics())
            page = f'''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>لوحة المهتمين | AsirX</title><style>body{{font-family:Arial;background:#f5f0e6;color:#18352d;margin:0;padding:28px}}h1{{margin-bottom:6px}}.tools,.stats{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}}input,select,a,button,.stats span{{padding:10px;border:1px solid #d7d1c8;background:#fff;color:inherit}}a{{text-decoration:none}}table{{width:100%;border-collapse:collapse;background:#fff}}td,th{{padding:10px;border:1px solid #ddd;text-align:right}}button{{cursor:pointer;color:#922e25}}@media(max-width:800px){{.table{{overflow:auto}}table{{min-width:850px}}}}</style><h1>لوحة المهتمين</h1><p>إجمالي السجلات: <b>{len(rows)}</b></p><div class="stats">{counts or '<span>لا توجد بيانات بعد</span>'}</div><div class="stats">{analytics or '<span>لا توجد أحداث تتبع بعد</span>'}</div><div class="tools"><input id="search" placeholder="ابحث بالاسم أو الجوال"><select id="service"><option value="">كل الخدمات</option>{options}</select><a href="/admin/interests.csv?key={key}">تصدير CSV</a></div><div class="table"><table><thead><tr><th>الاسم</th><th>الجوال</th><th>المدينة</th><th>الخدمة</th><th>الوجهة</th><th>موعد السفر</th><th>التاريخ</th><th></th></tr></thead><tbody>{cards}</tbody></table></div><script>const key={json.dumps(self.admin_key())};const search=document.querySelector('#search'),service=document.querySelector('#service');function filter(){{document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.includes(search.value)||service.value&&r.dataset.service!==service.value)}}search.oninput=filter;service.onchange=filter;async function removeRow(id,button){{if(!confirm('حذف هذا السجل التجريبي؟'))return;const r=await fetch('/api/admin/interests/'+id+'?key='+encodeURIComponent(key),{{method:'DELETE'}});if(r.ok)button.closest('tr').remove();else alert('تعذر الحذف')}};</script></html>'''
            return self.send_data(page.encode("utf-8"), content_type="text/html; charset=utf-8")
        if path == "/admin/interests.csv":
            if not self.admin_allowed():
                return self.send_data({"error": "غير مصرح"}, 401)
            rows = get_interests()
            output = io.StringIO(); writer = csv.writer(output)
            writer.writerow(["الرقم", "الاسم", "الجوال", "البريد", "المدينة", "الوجهة", "الخدمة", "موعد السفر", "المسافرون", "الميزانية", "الملاحظات", "موافقة التسويق", "تاريخ التسجيل"])
            for r in rows: writer.writerow([r["id"],r["name"],r["phone"],r["email"],r["city"],r["destination"],r["experience"],r["travel_date"],r["travelers"],r.get("budget",""),r.get("notes",""),r["marketing_consent"],r["created_at"]])
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
                track_event("interest_form_complete", payload.get("path", ""))
                return self.send_data({"id": interest_id, "message": "شكرًا لتسجيل اهتمامك في منصة عسير AsirX\n\nتم استلام بياناتك بنجاح وسيتم التواصل معك قريبًا لتزويدك بالتفاصيل\n\nنسعد بخدمتك ونتمنى لك تجربة سياحية مميزة في عسير"}, 201)
            if path == "/api/analytics":
                track_event(payload.get("event", ""), payload.get("path", ""))
                return self.send_data({"ok": True}, 201)
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_data({"error": "بيانات الطلب غير صالحة", "detail": str(exc)}, 400)
        self.send_data({"error": "المسار غير موجود"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/admin/interests/") and self.admin_allowed():
            try:
                interest_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                return self.send_data({"error": "رقم غير صالح"}, 400)
            return self.send_data({"deleted": bool(delete_interest(interest_id))})
        if path.startswith("/api/admin/messages/") and self.admin_allowed():
            try:
                message_id = int(path.rsplit("/", 1)[1])
            except ValueError:
                return self.send_data({"error": "رقم غير صالح"}, 400)
            return self.send_data({"deleted": bool(delete_message(message_id))})
        return self.send_data({"error": "غير مصرح"}, 401)

    def admin_key(self):
        return os.environ.get("ADMIN_PASSWORD", os.environ.get("ADMIN_KEY", "Rr@11223344"))

    def admin_username(self):
        return os.environ.get("ADMIN_USERNAME", "Rr@11223344")

    def admin_allowed(self):
        from urllib.parse import parse_qs
        query = parse_qs(urlparse(self.path).query)
        username = self.headers.get("X-Admin-Username") or query.get("username", [""])[0]
        password = self.headers.get("X-Admin-Password") or query.get("key", [""])[0]
        return (hmac.compare_digest(username, self.admin_username()) and
                hmac.compare_digest(password, self.admin_key()))

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "8000"))
    print(f"Rijal Explorer يعمل على http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), AppHandler).serve_forever()
