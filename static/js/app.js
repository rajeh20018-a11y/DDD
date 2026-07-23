const state = { places: [], scene: 0 };
const $ = (selector) => document.querySelector(selector);
const API_BASE = location.port === '5500' ? 'http://127.0.0.1:8772' : '';
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
  $('#places').innerHTML = items.map(p => `<a class="place-card place-link" href="destinations.html"><span class="place-icon">${p.icon}</span><span class="category">${escapeHTML(p.category)}</span><h3>${escapeHTML(p.name)}</h3><p>${escapeHTML(p.description)}</p><div class="place-meta"><span>★ ${p.rating}</span><span>⌖ ${escapeHTML(p.distance)}</span></div><b class="card-link-label">عرض الوجهة ←</b></a>`).join('');
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
  'service-detail.html?service=destinations&item=1'
];
document.querySelectorAll('.destination-card').forEach((card,index)=>card.href=destinationTargets[index]||'destinations.html');
const interestForm = $('#interestForm');
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
    message.className = 'form-message success'; message.textContent = result.message; event.currentTarget.reset();
  } catch (error) { const saved=JSON.parse(localStorage.getItem('asirx_interests')||'[]');saved.push({...payload,created_at:new Date().toISOString()});localStorage.setItem('asirx_interests',JSON.stringify(saved));message.className='form-message success';message.textContent='شكرًا لتسجيل اهتمامك 🌿 تم حفظ بياناتك محليًا في نسخة Live Server.';event.currentTarget.reset(); }
  finally { button.disabled = false; button.innerHTML = 'سجّل اهتمامي <span>←</span>'; }
});
loadPlaces();
