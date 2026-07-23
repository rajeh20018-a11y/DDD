// تركيب القالب في وضع Live Server الذي لا يدعم قوالب Python.
Promise.all([
  fetch('/templates/index.html').then(r=>r.text()),
  fetch('/templates/header.html').then(r=>r.text()),
  fetch('/templates/footer.html').then(r=>r.text())
]).then(([page,header,footer])=>{
  const body=page.match(/<body>([\s\S]*)<\/body>/i)?.[1]||page;
  document.body.innerHTML=body.replace('{{HEADER}}',header).replace('{{FOOTER}}',footer).replace('<script src="/static/js/app.js"></script>','');
  const script=document.createElement('script');script.src='/static/js/app.js';document.body.appendChild(script);
}).catch(()=>{document.body.innerHTML='<p style="padding:40px">تعذر تحميل ملفات الواجهة. شغّل Live Server من مجلد المشروع الرئيسي.</p>'});
