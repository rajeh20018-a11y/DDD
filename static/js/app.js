const state = { places: [], scene: 0 };
const $ = (selector) => document.querySelector(selector);
document.querySelectorAll('input[name="email"]').forEach(input=>input.closest('label,.field')?.remove());
const API_BASE = location.port === '5500' ? 'http://127.0.0.1:8772' : '';
function track(event){fetch(`${API_BASE}/api/analytics`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event,path:location.pathname})}).catch(()=>{})}
track('site_visit');
const escapeHTML = (value) => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

async function loadPlaces() {
  try {
    const response = await fetch(`${API_BASE}/api/places`);
    state.places = (await response.json()).places;
    renderPlaces('الكل');
  } catch {
    state.places = [
      {icon:'🏛️',category:'تراثية',name:'قرية رجال ألمع',description:'بيوت حجرية ملونة تحكي تاريخ المنطقة.',rating:4.9,distance:'وسط القرية'},
      {icon:'⛰️',category:'طبيعية',name:'جبال السودة',description:'غابات وإطلالات جبلية واسعة.',rating:4.8,distance:'45 دقيقة'},
      {icon:'🍲',category:'مطاعم',name:'مذاق ألمع',description:'أطباق عسيرية محلية أصيلة.',rating:4.7,distance:'8 دقائق'},
      {icon:'☕',category:'مقاهٍ',name:'مقهى الجبل',description:'قهوة سعودية وإطلالة هادئة.',rating:4.6,distance:'12 دقيقة'}
    ]; renderPlaces('الكل');
  }
}
function renderPlaces(filter) {
  const items = filter === 'الكل' ? state.places : state.places.filter(p => p.category === filter);
  $('#places').innerHTML = items.map(p => {const target=p.category==='مطاعم'||p.category==='مقاهٍ'?'restaurants.html':p.category==='فنادق'?'hotels.html':p.category==='فعاليات'?'events.html':'destinations.html';return `<a class="place-card place-link" href="${target}"><span class="place-icon">${p.icon}</span><span class="category">${escapeHTML(p.category)}</span><h3>${escapeHTML(p.name)}</h3><p>${escapeHTML(p.description)}</p><div class="place-meta"><span>★ ${p.rating}</span><span>⌖ ${escapeHTML(p.distance)}</span></div><b class="card-link-label">عرض التفاصيل ←</b></a>`}).join('');
}
document.querySelectorAll('.filters button').forEach(button => button.addEventListener('click', () => {
  document.querySelector('.filters .active').classList.remove('active'); button.classList.add('active'); renderPlaces(button.dataset.filter);
}));

const days = $('#days');
days.addEventListener('input', () => $('#daysValue').textContent = days.value === '1' ? 'يوم واحد' : `${days.value} أيام`);
$('#plannerForm').addEventListener('submit', async event => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  let plan;
  try { const result = await fetch(`${API_BASE}/api/plan`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({days:form.get('days'), budget:form.get('budget'), interests:form.getAll('interests')})}); if(!result.ok)throw new Error(); plan=await result.json(); }
  catch { const count=Number(form.get('days')); plan={schedule:Array.from({length:count},(_,i)=>({day:i+1,title:'يوم بين الطبيعة والتراث',places:state.places.slice((i*2)%state.places.length,((i*2)%state.places.length)+2)}))}; }
  $('#planResult').className = 'plan-result show';
  $('#planResult').innerHTML = plan.schedule.map(day => `<article class="day-card"><span>اليوم ${day.day}</span><h3>${day.title}</h3>${day.places.map(p => `<p>${p.icon} ${escapeHTML(p.name)}</p>`).join('')}</article>`).join('');
  $('#planResult').scrollIntoView({behavior:'smooth', block:'center'});
  setTimeout(()=>{ $('#interest').scrollIntoView({behavior:'smooth',block:'start'}); const experience=$('#leadExperience'); if(experience)experience.value='تخطيط الرحلات'; },1200);
});

const sceneNames = ['القرية التراثية', 'الجبال والمدرجات', 'القصور الحجرية'];
const scenePositions = [50, 15, 85];
function setPanoramaPosition(position) {
  shift = Math.max(5, Math.min(95, position));
  $('#panorama').style.backgroundPosition = `${shift}% center`;
  const progress = $('#panoramaProgress');
  if (progress) progress.style.transform = `translateX(${(shift - 50) * .85}%)`;
}
function changeScene(step) { state.scene = (state.scene + step + sceneNames.length) % sceneNames.length; $('#sceneName').textContent = sceneNames[state.scene]; setPanoramaPosition(scenePositions[state.scene]); }
$('#tourNext').onclick = () => changeScene(1); $('#tourPrev').onclick = () => changeScene(-1);
let startX = 0, shift = 50;
$('#panorama').addEventListener('pointerdown', e => { startX = e.clientX; $('#panorama').setPointerCapture(e.pointerId); });
$('#panorama').addEventListener('pointermove', e => { if (!$('#panorama').hasPointerCapture(e.pointerId)) return; const delta = (e.clientX-startX) / $('#panorama').clientWidth * 100; startX=e.clientX; setPanoramaPosition(shift-delta); });
document.querySelectorAll('.hotspot').forEach(h => h.onclick = () => toast(h.dataset.info));
function toast(message) { $('#toast').textContent = message; $('#toast').classList.add('show'); setTimeout(()=>$('#toast').classList.remove('show'), 3500); }

const panel = $('#assistantPanel');
$('#askAssistant').onclick = () => { panel.classList.add('open'); panel.setAttribute('aria-hidden','false'); $('#chatInput').focus(); };
$('#closeAssistant').onclick = () => { panel.classList.remove('open'); panel.setAttribute('aria-hidden','true'); };
$('#chatForm').addEventListener('submit', event => { event.preventDefault(); const input=$('#chatInput'), q=input.value.trim(); if(!q)return; addMessage(q,'user'); input.value=''; setTimeout(()=>addMessage(answer(q),'bot'),450); });
function addMessage(text,type){const p=document.createElement('p');p.className=type;p.textContent=text;$('#messages').appendChild(p);$('#messages').scrollTop=$('#messages').scrollHeight;}
function answer(q){ if(q.includes('وقت')||q.includes('متى'))return 'أفضل الأوقات عادةً من أكتوبر إلى أبريل، وتأكد من الطقس قبل الانطلاق.'; if(q.includes('مطعم')||q.includes('أكل'))return 'جرّب الأطباق العسيرية المحلية، ويمكنك تصفية قسم الاستكشاف إلى «مطاعم».'; if(q.includes('يوم'))return 'ابدأ بالقرية والمتحف صباحًا، ثم وادي ريم، واختتم بإطلالة جبلية وقت الغروب.'; return 'أنصحك بالبدء بالجولة الافتراضية، ثم اختيار اهتماماتك في مخطط الرحلة للحصول على اقتراح مناسب.';}
$('.menu-button').onclick=()=>{const header=$('.site-header');header.classList.toggle('open');$('.menu-button').setAttribute('aria-expanded',header.classList.contains('open'));};
// ربط وجهات الواجهة الرئيسية بصفحات التفاصيل.
const destinationTargets=[
  'service-detail.html?service=destinations&item=0',
  'service-detail.html?service=destinations&item=1',
  'service-detail.html?service=destinations&item=2',
  'service-detail.html?service=destinations&item=3'
];
document.querySelectorAll('.destination-card').forEach((card,index)=>card.href=destinationTargets[index]||'destinations.html');
const heroIcons=['360°','🤖','🗺️','🏨','📍'];document.querySelectorAll('.feature-row strong').forEach((icon,index)=>icon.textContent=heroIcons[index]||icon.textContent);
document.addEventListener('click',event=>{const target=event.target.closest('a,button');if(!target)return;const href=target.getAttribute('href')||'';if(href.includes('tours-360')||target.closest('#tour'))track('tour_360_click');if(href.includes('trip-planner')||target.closest('#plannerForm'))track('trip_planner_click');if(href.includes('wa.me'))track('whatsapp_click')});
const interestForm = $('#interestForm');
if(interestForm)track('interest_form_open');
if(interestForm&&!interestForm.elements.budget){const firstConsent=interestForm.querySelector('.consent');firstConsent.insertAdjacentHTML('beforebegin','<div class="field"><label>الميزانية التقريبية (اختياري)</label><select name="budget"><option value="">غير محددة</option><option>أقل من 2,000 ريال</option><option>2,000–5,000 ريال</option><option>5,000–10,000 ريال</option><option>أكثر من 10,000 ريال</option></select></div><div class="field"><label>ملاحظات إضافية</label><textarea name="notes" rows="3" maxlength="1000"></textarea></div>')}
if (interestForm) interestForm.addEventListener('submit', async event => {
  event.preventDefault();
  const button = event.currentTarget.querySelector('button[type="submit"]');
  const message = $('#interestMessage');
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.privacy_consent = form.has('privacy_consent');
  payload.marketing_consent = form.has('marketing_consent');
  button.disabled = true; button.textContent = 'جارٍ التسجيل…'; message.className = 'form-message'; message.textContent = '';
  try {
    const response = await fetch(`${API_BASE}/api/interests`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'تعذر إكمال التسجيل');
    message.className = 'form-message success'; message.innerHTML = '<h3>شكرًا لتسجيل اهتمامك في AsirX</h3><p>تم استلام بياناتك بنجاح وسنتواصل معك عند توفر التجربة المناسبة.</p><p><a href="/">العودة للرئيسية</a> · <a href="https://wa.me/966500000000" target="_blank" rel="noopener">التواصل عبر واتساب</a> · <a href="/destinations.html">استكشاف الوجهات</a></p>'; event.currentTarget.reset();
  } catch (error) { message.className='form-message error';message.textContent=error.message||'تعذر حفظ البيانات. لم يتم تسجيل الطلب؛ حاول مرة أخرى.'; }
  finally { button.disabled = false; button.innerHTML = 'سجّل اهتمامي <span>←</span>'; }
});
loadPlaces();
const GOOGLE_FORM_URL='https://forms.gle/pByYj499KTFH3RXy8';
const THANK_YOU_MESSAGE='تم استلام بياناتك بنجاح وسنتواصل معك قريبًا\nنتمنى لك تجربة سياحية جميلة في منطقة عسير';
document.addEventListener('click',event=>{const control=event.target.closest('a,button');if(!control||!(/سجّل اهتمام|مهتم بهذه التجربة/.test(control.textContent)))return;event.preventDefault();window.open(GOOGLE_FORM_URL,'_blank','noopener');setTimeout(()=>alert(THANK_YOU_MESSAGE),150)},true);
if(interestForm){const googleCta=document.createElement('div');googleCta.className='interest-form google-form-cta';googleCta.innerHTML='<h3>نموذج تسجيل الاهتمام</h3><p>اضغط الزر التالي وأكمل بياناتك في نموذج AsirX الرسمي.</p><a class="button primary wide" href="https://forms.gle/pByYj499KTFH3RXy8" target="_blank" rel="noopener">سجّل اهتمامك <span>←</span></a>';interestForm.replaceWith(googleCta)}
