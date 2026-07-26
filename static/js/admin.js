const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
let credentials=JSON.parse(sessionStorage.getItem('asirx_admin_credentials')||'null')||{username:'',password:''};
let dashboardData={interests:[],messages:[],analytics:[],summary:{totals:{},daily:[],experiences:[]}};
const eventNames={site_visit:'زيارات الموقع',tour_360_click:'نقرات جولات 360°',trip_planner_click:'طلبات تخطيط الرحلة',interest_form_open:'فتح نموذج الاهتمام',interest_form_complete:'إكمال نموذج الاهتمام',whatsapp_click:'نقرات واتساب'};
const colors=['#d69b47','#245d4e','#7b9d8f','#d9c6a4','#8a6446','#aabbb3'];
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const formatDate=v=>v?new Intl.DateTimeFormat('ar-SA',{dateStyle:'medium'}).format(new Date(v.replace(' ','T')+'Z')):'—';
function api(path,options={}){options.headers={...(options.headers||{}),'X-Admin-Username':credentials.username,'X-Admin-Password':credentials.password};return fetch(path,options)}
async function loadDashboard(){
  const response=await api('/api/admin/dashboard');
  if(!response.ok)throw new Error('مفتاح الإدارة غير صحيح');
  dashboardData=await response.json();sessionStorage.setItem('asirx_admin_credentials',JSON.stringify(credentials));
  $('#loginView').hidden=true;$('#dashboardView').hidden=false;renderAll();
}
function renderAll(){
  const {summary,interests,messages,analytics}=dashboardData,t=summary.totals;
  $('#totalInterests').textContent=t.interests||0;$('#totalVisits').textContent=t.visits||0;$('#totalMessages').textContent=t.messages||0;$('#totalPlans').textContent=t.plans||0;
  $('#leadBadge').textContent=interests.length;$('#messageBadge').textContent=messages.length;
  renderChart(summary.daily);renderDonut(summary.experiences,t.interests||0);renderRecent(interests.slice(0,5));renderInterests();renderMessages(messages);renderAnalytics(analytics);renderBreakdowns(summary);
  $('#experienceFilter').innerHTML='<option value="">كل الخدمات</option>'+summary.experiences.map(x=>`<option>${escapeHTML(x.label)}</option>`).join('');
  $('#exportCsv').href='#';
}
function renderChart(rows){
  const map=Object.fromEntries(rows.map(x=>[x.day,x.count])),days=[];for(let i=6;i>=0;i--){const d=new Date();d.setDate(d.getDate()-i);const key=d.toISOString().slice(0,10);days.push({key,count:map[key]||0,label:new Intl.DateTimeFormat('ar-SA',{weekday:'short'}).format(d)})}
  const max=Math.max(1,...days.map(x=>x.count));$('#dailyChart').innerHTML=days.map(x=>`<div class="bar-col"><b>${x.count}</b><i style="height:${Math.max(4,x.count/max*82)}%"></i><small>${x.label}</small></div>`).join('');
}
function renderDonut(rows,total){let at=0;const parts=rows.map((x,i)=>{const start=at;at+=total?x.count/total*100:0;return `${colors[i%colors.length]} ${start}% ${at}%`});$('#experienceDonut').style.background=parts.length?`conic-gradient(${parts.join(',')})`:'#e8e8e4';$('#experienceDonut').innerHTML=`<b>${total}</b><span>طلب</span>`;$('#experienceLegend').innerHTML=rows.slice(0,5).map((x,i)=>`<div><span><i style="background:${colors[i%colors.length]}"></i>${escapeHTML(x.label)}</span><b>${x.count}</b></div>`).join('')||'<small>لا توجد بيانات بعد</small>'}
const personCell=r=>`<div class="person"><span class="avatar">${escapeHTML((r.name||'?').trim()[0])}</span><div><b>${escapeHTML(r.name)}</b>${r.email?`<small>${escapeHTML(r.email)}</small>`:''}</div></div>`;
function renderRecent(rows){$('#recentRows').innerHTML=rows.map(r=>`<tr><td>${personCell(r)}</td><td><span class="pill">${escapeHTML(r.experience)}</span></td><td>${escapeHTML(r.destination)}</td><td>${formatDate(r.created_at)}</td></tr>`).join('')||'<tr><td colspan="4" class="empty">لا توجد تسجيلات بعد</td></tr>'}
function renderInterests(){const q=$('#leadSearch').value.trim().toLowerCase(),service=$('#experienceFilter').value;const rows=dashboardData.interests.filter(r=>(!q||`${r.name} ${r.phone} ${r.city}`.toLowerCase().includes(q))&&(!service||r.experience===service));$('#interestRows').innerHTML=rows.map(r=>`<tr><td>${personCell(r)}</td><td dir="ltr">${escapeHTML(r.phone)}</td><td>${escapeHTML(r.city)}</td><td><span class="pill">${escapeHTML(r.experience)}</span></td><td>${escapeHTML(r.destination)}</td><td>${r.travel_date?escapeHTML(r.travel_date):'—'}</td><td><button class="delete" data-delete-interest="${r.id}" aria-label="حذف">حذف</button></td></tr>`).join('')||'<tr><td colspan="7" class="empty">لا توجد نتائج مطابقة</td></tr>'}
function renderMessages(rows){$('#messageList').innerHTML=rows.map(r=>`<article class="message"><header><div><h3>${escapeHTML(r.name)}</h3><small>${escapeHTML(r.email||'بدون بريد')} · ${formatDate(r.created_at)}</small></div><button class="delete" data-delete-message="${r.id}">حذف</button></header><p>${escapeHTML(r.message)}</p></article>`).join('')||'<p class="empty">لا توجد رسائل بعد</p>'}
function renderAnalytics(rows){$('#analyticsList').innerHTML=rows.map(r=>`<article><span>${escapeHTML(eventNames[r.event]||r.event)}</span><b>${r.count}</b></article>`).join('')||'<p class="empty">لا توجد أحداث مسجلة بعد</p>'}
function renderBreakdowns(summary){const block=(title,rows)=>`<article class="panel"><div class="panel-head"><div><span>تحليل المهتمين</span><h2>${title}</h2></div></div><div class="legend">${(rows||[]).map((x,i)=>`<div><span><i style="background:${colors[i%colors.length]}"></i>${escapeHTML(x.label)}</span><b>${x.count}</b></div>`).join('')||'<small>لا توجد بيانات بعد</small>'}</div></article>`;$('#interestBreakdowns').innerHTML=block('حسب الوجهة',summary.destinations)+block('حسب المدينة',summary.cities)}
function openTab(id){$$('.tab').forEach(x=>x.classList.toggle('active',x.id===id));$$('nav [data-tab]').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));$('#pageTitle').textContent={overview:'نظرة عامة',interests:'العملاء المهتمون',messages:'الرسائل',analytics:'التحليلات'}[id]}
function toast(text){$('#adminToast').textContent=text;$('#adminToast').classList.add('show');setTimeout(()=>$('#adminToast').classList.remove('show'),2200)}
$('#loginForm').onsubmit=async e=>{e.preventDefault();credentials={username:$('#adminUsername').value.trim(),password:$('#adminPassword').value};$('#loginError').textContent='جارٍ التحقق…';try{await loadDashboard();$('#loginError').textContent=''}catch(error){$('#loginError').textContent=error.message}};
$('#togglePassword').onclick=()=>{const input=$('#adminPassword'),show=input.type==='password';input.type=show?'text':'password';$('#togglePassword').textContent=show?'🙈':'👁';$('#togglePassword').setAttribute('aria-label',show?'إخفاء كلمة المرور':'إظهار كلمة المرور');$('#togglePassword').setAttribute('aria-pressed',String(show))};
$$('[data-tab]').forEach(x=>x.onclick=()=>openTab(x.dataset.tab));$$('[data-open-tab]').forEach(x=>x.onclick=()=>openTab(x.dataset.openTab));$('#leadSearch').oninput=renderInterests;$('#experienceFilter').onchange=renderInterests;
$('#refresh').onclick=async()=>{await loadDashboard();toast('تم تحديث البيانات')};$('#logout').onclick=()=>{sessionStorage.removeItem('asirx_admin_credentials');location.href='/ddd'};
$('#exportCsv').onclick=async e=>{e.preventDefault();const response=await api('/admin/interests.csv');if(!response.ok)return toast('تعذر تصدير الملف');const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='asirx-interests.csv';link.click();URL.revokeObjectURL(url)};
document.addEventListener('click',async e=>{const interest=e.target.closest('[data-delete-interest]'),message=e.target.closest('[data-delete-message]');if(!interest&&!message)return;if(!confirm('هل تريد حذف هذا السجل نهائيًا؟'))return;const type=interest?'interests':'messages',id=(interest||message).dataset[interest?'deleteInterest':'deleteMessage'];const response=await api(`/api/admin/${type}/${id}`,{method:'DELETE'});if(response.ok){await loadDashboard();toast('تم حذف السجل')}else toast('تعذر حذف السجل')});
if(credentials.username&&credentials.password)loadDashboard().catch(()=>{sessionStorage.removeItem('asirx_admin_credentials');$('#adminUsername').value=credentials.username});
