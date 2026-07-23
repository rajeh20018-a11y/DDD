const qs=(s)=>document.querySelector(s), qsa=(s)=>document.querySelectorAll(s);
qsa('input[name="email"]').forEach(input=>input.closest('label,.field')?.remove());
const API_BASE=location.port==='5500'?'http://127.0.0.1:8772':'';
// ثلاثة أنواع مصوّرة خاصة بكل خدمة.
const serviceTypes={
  'tours-360':[['تراث','جولة رجال ألمع','قصور وممرات تاريخية'],['طبيعة','جولة السودة','غابات وإطلالات جبلية'],['مغامرة','جولة الحبلة','منحدرات ومسارات ساحرة']],
  'ai-assistant':[['اقتراحات','دليل الوجهات','أماكن تناسب اهتماماتك'],['إقامة','دليل الفنادق','خيارات قريبة من مسارك'],['برنامج','مخطط ذكي','جدول يومي سريع']],
  'trip-planner':[['ثقافة','رحلة تراثية','قرى ومتاحف وحكايات'],['استرخاء','رحلة طبيعية','جبال وغابات وإطلالات'],['نشاط','رحلة مغامرات','مسارات وتجارب محلية']],
  'hotels':[['تراث','نُزل ريفية','إقامة بطابع عسيري'],['رفاهية','منتجعات جبلية','إطلالات وخدمات متكاملة'],['مدينة','فنادق أبها','قريبة من الخدمات']],
  'destinations':[['تاريخ','وجهات تراثية','قرى وقصور ومتاحف'],['طبيعة','وجهات طبيعية','جبال وغابات وأودية'],['ترفيه','أماكن عائلية','ممشى وبحيرات وأنشطة']],
  'restaurants':[['محلي','مطاعم شعبية','مذاقات جنوبية أصيلة'],['قهوة','مقاهٍ جبلية','جلسات وإطلالات هادئة'],['عائلي','مطاعم عائلية','خيارات تناسب الجميع']],
  'events':[['ثقافة','مهرجانات تراثية','عروض وفنون محلية'],['حركة','تجارب مغامرة','مشي وتسلق واستكشاف'],['تذوق','تجارب محلية','أسواق ومنتجات المنطقة']]
};
const serviceSlugs={
  'tours-360':['rijal-almaa','sawda','habala'],
  'ai-assistant':['destinations-guide','hotels-guide','smart-schedule'],
  'trip-planner':['heritage-trip','nature-trip','adventure-trip'],
  'hotels':['heritage-lodges','mountain-resorts','city-hotels'],
  'destinations':['heritage','nature','family'],
  'restaurants':['local-food','mountain-cafes','family-restaurants'],
  'events':['heritage-festivals','adventures','local-experiences']
};
const pageKey=location.pathname.split('/').filter(Boolean).pop()?.replace('.html','');
const liveMode=location.port==='5500'||location.protocol==='file:';
if(liveMode){
  const staticLinks={'/':'/index.html','/destinations/':'/destinations.html','/trip-planner/':'/trip-planner.html','/hotels/':'/hotels.html','/restaurants/':'/restaurants.html','/events/':'/events.html','/tours-360/':'/tours-360.html','/interest/':'/interest.html'};
  qsa('a[href]').forEach(a=>{const target=staticLinks[a.getAttribute('href')];if(target)a.href=target});
}
// شريط موحّد يربط جميع واجهات المنصة ببعضها.
const connectedNav=document.createElement('nav');connectedNav.className='connected-nav';
connectedNav.innerHTML=`<a href="/index.html">الرئيسية</a><a href="/tours-360.html">جولات 360°</a><a href="/ai-assistant.html">المساعد الذكي</a><a href="/trip-planner.html">تخطيط الرحلات</a><a href="/hotels.html">الفنادق</a><a href="/destinations.html">الوجهات</a><a href="/restaurants.html">المطاعم</a><a href="/events.html">الفعاليات</a><a href="/interest.html">سجّل اهتمامك</a>`;
document.querySelector('header')?.after(connectedNav);
if(serviceTypes[pageKey]){
  const showcase=document.createElement('section'); showcase.className='type-showcase';
  showcase.innerHTML=serviceTypes[pageKey].map((x,i)=>`<a href="${liveMode?`/service-detail.html?service=${pageKey}&item=${i}`:`/services/${pageKey}/${serviceSlugs[pageKey][i]}/`}" class="type-card visual-${i+1}"><span>${x[0]}</span><h2>${x[1]}</h2><p>${x[2]}</p><b>افتح الصفحة ←</b></a>`).join('');
  qs('.page-intro').after(showcase); const content=qs('.content'); if(content)content.id='serviceContent';
}
const panorama=qs('#realPanorama');let pan=50,start=0;
function movePan(value){pan=Math.max(4,Math.min(96,value));panorama.style.backgroundPosition=`${pan}% center`;}
if(panorama){panorama.onpointerdown=e=>{start=e.clientX;panorama.setPointerCapture(e.pointerId)};panorama.onpointermove=e=>{if(!panorama.hasPointerCapture(e.pointerId))return;const d=(e.clientX-start)/panorama.clientWidth*100;start=e.clientX;movePan(pan-d)};qsa('.point').forEach(p=>p.onclick=e=>{e.stopPropagation();qs('#tourInfo').textContent=p.dataset.text});qs('#tourPlace').onchange=e=>movePan(Number(e.target.value));}
const replies=q=>q.includes('يوم')?'برنامج ليومين: رجال ألمع والمتحف في اليوم الأول، والسودة وأبها في اليوم الثاني.':q.includes('عائل')?'رجال ألمع وبحيرة سد أبها والحبلة خيارات مناسبة للعائلة.':q.includes('سكن')||q.includes('فندق')?'يمكنك مراجعة صفحة الفنادق؛ نُزل القرية هو الأقرب لرجال ألمع.':q.includes('وقت')?'الفترة من أكتوبر إلى أبريل ألطف عادةً، مع التحقق من الطقس قبل السفر.':'أنصحك باختيار اهتماماتك في مخطط الرحلة للحصول على اقتراح أدق.';
const assistantForm=qs('#assistantForm');function addChat(t,c){const p=document.createElement('p');p.className=c;p.textContent=t;qs('#pageMessages').append(p)}
if(assistantForm){assistantForm.onsubmit=e=>{e.preventDefault();const i=qs('#assistantInput'),q=i.value.trim();if(!q)return;addChat(q,'user');i.value='';setTimeout(()=>addChat(replies(q),'bot'),300)};qsa('.suggestion').forEach(b=>b.onclick=()=>{qs('#assistantInput').value=b.textContent;assistantForm.requestSubmit()});qs('#saveChat').onclick=()=>alert('تم حفظ المقترحات على هذا الجهاز للنسخة التجريبية.');}
const planner=qs('#fullPlanner');if(planner)planner.onsubmit=async e=>{e.preventDefault();const result=qs('#fullPlanResult');try{const f=new FormData(planner),r=await fetch(`${API_BASE}/api/plan`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({days:f.get('days'),budget:f.get('budget'),interests:f.getAll('interests')})});if(!r.ok)throw new Error();const p=await r.json();result.innerHTML=p.schedule.map(d=>`<article class="result-day"><b>اليوم ${d.day}</b><h3>${d.title}</h3>${d.places.map(x=>`<p>${x.icon} ${x.name}</p>`).join('')}</article>`).join('')+`<div class="notice">تم إنشاء الرحلة، سيتم نقلك الآن لإكمال التسجيل…</div>`;setTimeout(()=>location.href='/interest.html?experience='+encodeURIComponent('تخطيط الرحلات'),1400)}catch{result.innerHTML='<div class="notice">تعذر إنشاء الرحلة الآن. تحقق من اتصال الخادم وحاول مرة أخرى.</div>'}};
qsa('.add-plan').forEach(b=>b.onclick=()=>{b.textContent='✓ أضيفت إلى الخطة';b.disabled=true});
qsa('.listing button:not(.add-plan)').forEach(b=>b.onclick=()=>alert('سيتم ربط الحجز بمقدم الخدمة في المرحلة التالية.'));
const interest=qs('#standaloneInterest');
if(interest){const selectedExperience=new URLSearchParams(location.search).get('experience');if(selectedExperience){const select=interest.querySelector('[name="experience"]');if(select)select.value=selectedExperience}}
if(interest)interest.onsubmit=async e=>{e.preventDefault();const m=qs('#standaloneMessage'),button=interest.querySelector('button[type="submit"]'),f=new FormData(interest),data=Object.fromEntries(f.entries());data.privacy_consent=f.has('privacy_consent');data.marketing_consent=f.has('marketing_consent');data.path=location.pathname;button.disabled=true;m.textContent='جارٍ إرسال بياناتك…';try{const r=await fetch(`${API_BASE}/api/interests`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}),out=await r.json();if(!r.ok)throw new Error(out.detail||out.error);interest.reset();m.style.color='#246044';m.innerHTML='<h2>شكرًا لتسجيل اهتمامك في AsirX</h2><p>تم استلام بياناتك بنجاح وسنتواصل معك عند توفر التجربة المناسبة.</p><div class="success-actions"><a class="btn" href="/">العودة للرئيسية</a><a class="btn track-whatsapp" href="https://wa.me/966500000000" target="_blank" rel="noopener">التواصل عبر واتساب</a><a class="btn" href="/destinations.html">استكشاف الوجهات</a></div>'}catch(error){m.style.color='#922e25';m.textContent=error.message||'تعذر حفظ البيانات. حاول مرة أخرى.'}finally{button.disabled=false}};
function track(event){fetch(`${API_BASE}/api/analytics`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event,path:location.pathname})}).catch(()=>{})}track('site_visit');if(interest)track('interest_form_open');document.addEventListener('click',e=>{const a=e.target.closest('a,button');if(!a)return;const href=a.getAttribute('href')||'';if(href.includes('tours-360'))track('tour_360_click');if(href.includes('trip-planner')||a.closest('#fullPlanner'))track('trip_planner_click');if(href.includes('wa.me'))track('whatsapp_click')});
