# رِحال ألمع — MVP

نموذج أولي عربي لمنصة استكشاف رجال ألمع افتراضيًا والتخطيط للرحلة. الخادم مبني بمكتبات Python القياسية، والبيانات محفوظة محليًا في SQLite.

## التشغيل محليًا

```powershell
python app.py
```

ثم افتح `http://localhost:8000`. يمكن تغيير المنفذ عبر متغير البيئة `PORT`.

## النشر على Render

- أنشئ Web Service من المستودع.
- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`

تنبيه: قرص Render الافتراضي مؤقت، لذلك بيانات SQLite الجديدة قد تُفقد عند إعادة النشر. هذا مقبول للاختبار الأولي، ويمكن إضافة Persistent Disk عند الحاجة.

## تسجيلات العملاء ولوحة الإدارة

يحفظ نموذج «سجّل اهتمامك» البيانات في جدول `interests`. اضبط متغير البيئة `ADMIN_KEY` بقيمة سرية، ثم افتح:

```text
http://localhost:8000/admin/interests?key=YOUR_ADMIN_KEY
```

تتضمن الصفحة رابط تصدير CSV بترميز عربي، ويمكن فتح الملف مباشرة في Excel. القيمة الافتراضية المحلية هي `change-me` ويجب تغييرها قبل النشر.

### استخدام قاعدة البيانات مع Live Server

شغّل `start-live-backend.bat` واترك نافذته مفتوحة، ثم افتح `index.html` باستخدام Live Server. تعمل الواجهة على المنفذ 5500 وترسل التسجيلات إلى خادم SQLite المحلي على المنفذ 8772.

## الهيكل

- `app.py`: الخادم ومسارات API.
- `database.py`: إنشاء SQLite والاستعلامات.
- `templates/`: قوالب HTML.
- `static/`: CSS وJavaScript والصور مستقبلًا.
