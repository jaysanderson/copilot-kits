(function(){
var $=function(i){return document.getElementById(i)};
var LANG='en',PAGE='apply',busy=false;
(function(){var p=new URLSearchParams(location.search).get('p');if(p&&document.querySelector('#tabs [data-page="'+p+'"]')){PAGE=p;document.querySelectorAll('#tabs button').forEach(function(x){x.setAttribute('aria-selected',x.dataset.page===p?'true':'false')})}})();
var TXT={
 en:{tabs:{apply:'How to apply',international:'International students',scholarships:'Scholarships',perth:'Perth campus'},navall:'Ask the whole site',navstudy:'Study',how:'How this works',open:'Open on university.edu.au',foot:'Demonstration built on content from university.edu.au. Answers come from the page shown; always confirm details on university.edu.au. Not an official The university service.',loadp:'Loading the page...',ph:'Ask about this page',ask:'Ask',busy:'Reading the page...',lead:'Read a University page on the left. Ask about it, in your own language, on the right. The answer points to the passage it came from.',h1:'Ask this page',
  found:'Passages the answer relied on, matched word for word in the page',show:'Show them',nohl:'The answer named passages, but none could be matched word for word in the page text, so nothing is highlighted.',nonecite:'',decl:'This page does not say enough to answer that. Try asking about what the page covers.',err:'That did not load. Check your connection and try again.',retry:'Try again',timeout:'That took too long.',wrong:'The reply did not come back in the language picked. Try again.'},
 zh:{tabs:{apply:'如何申请',international:'国际学生',scholarships:'奖学金',perth:'珀斯校区'},navall:'向整个网站提问',navstudy:'学习',how:'运作方式',open:'在 university.edu.au 打开',foot:'本演示基于 university.edu.au 的内容构建。答案来自所示页面，请务必在 university.edu.au 核实细节。并非大学官方服务。',loadp:'正在加载页面...',ph:'询问这个页面',ask:'提问',busy:'正在阅读页面...',lead:'左边阅读大学的页面，右边用您自己的语言提问。答案会指向来源段落。',h1:'向这个页面提问',
  found:'答案所依据的段落，已与页面原文逐字核对',show:'查看',nohl:'答案引用了段落，但无法在页面文本中逐字核对，因此没有高亮。',nonecite:'',decl:'这个页面没有足够的信息来回答。请询问页面涵盖的内容。',err:'加载失败。请检查网络后重试。',retry:'重试',timeout:'等待时间过长。',wrong:'回复没有使用所选语言。请重试。'},
 ar:{tabs:{apply:'كيفية التقديم',international:'الطلاب الدوليون',scholarships:'المنح الدراسية',perth:'حرم بيرث'},navall:'اسأل الموقع كله',navstudy:'الدراسة',how:'كيف يعمل هذا',open:'افتح على university.edu.au',foot:'عرض توضيحي مبني على محتوى university.edu.au. تأتي الإجابات من الصفحة المعروضة؛ تأكد دائمًا من التفاصيل على university.edu.au. ليست خدمة رسمية من جامعة مردوخ.',loadp:'جارٍ تحميل الصفحة...',ph:'اسأل عن هذه الصفحة',ask:'اسأل',busy:'جارٍ قراءة الصفحة...',lead:'اقرأ صفحة مردوخ على اليسار واسأل عنها بلغتك على اليمين. تشير الإجابة إلى المقطع الذي استندت إليه.',h1:'اسأل هذه الصفحة',
  found:'المقاطع التي اعتمدت عليها الإجابة، مطابقة حرفيًا في الصفحة',show:'اعرضها',nohl:'ذكرت الإجابة مقاطع، لكن تعذرت مطابقتها حرفيًا في نص الصفحة، لذلك لا يوجد تمييز.',nonecite:'',decl:'لا تحتوي هذه الصفحة على معلومات كافية للإجابة. جرّب السؤال عمّا تغطيه الصفحة.',err:'تعذر التحميل. تحقق من الاتصال وحاول مجددًا.',retry:'حاول مجددًا',timeout:'استغرق الأمر وقتًا طويلًا.',wrong:'لم يأتِ الرد باللغة المختارة. حاول مجددًا.'},
 id:{tabs:{apply:'Cara mendaftar',international:'Mahasiswa internasional',scholarships:'Beasiswa',perth:'Kampus Perth'},navall:'Tanya seluruh situs',navstudy:'Studi',how:'Cara kerjanya',open:'Buka di university.edu.au',foot:'Demonstrasi yang dibangun dari konten university.edu.au. Jawaban berasal dari halaman yang ditampilkan; selalu pastikan detailnya di university.edu.au. Bukan layanan resmi The university.',loadp:'Memuat halaman...',ph:'Tanya tentang halaman ini',ask:'Tanya',busy:'Membaca halaman...',lead:'Baca halaman University di kiri. Tanyakan dalam bahasa Anda di kanan. Jawaban menunjuk ke bagian yang menjadi sumbernya.',h1:'Tanya halaman ini',
  found:'Bagian yang menjadi dasar jawaban, cocok kata demi kata di halaman',show:'Tampilkan',nohl:'Jawaban menyebut bagian tertentu, tetapi tidak ada yang cocok kata demi kata di teks halaman, jadi tidak ada yang disorot.',nonecite:'',decl:'Halaman ini tidak cukup menjelaskan hal itu. Coba tanyakan apa yang dibahas halaman.',err:'Gagal memuat. Periksa koneksi dan coba lagi.',retry:'Coba lagi',timeout:'Terlalu lama.',wrong:'Balasan tidak dalam bahasa yang dipilih. Coba lagi.'}
};
function T(k){return TXT[LANG][k]}
var esc=window.MuMd.esc;
var md=window.MuMd.md;
function fetchT(url,opt,ms){
 var c=new AbortController(),t=setTimeout(function(){c.abort()},ms);
 opt=opt||{};opt.signal=c.signal;
 return fetch(url,opt).finally(function(){clearTimeout(t)});
}
function loadPage(){
 var body=$('pm-body');body.innerHTML='<p class="pm-load">'+esc(T('loadp'))+'</p>';
 $('pm-result').hidden=true;
 fetchT('/api/page/'+PAGE,{},window.__TL||20000).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(d){
  $('pm-label').textContent=T('tabs')[PAGE]||d.label;$('pm-open').href=d.url;
  body.innerHTML=d.blocks.map(function(b){return '<div data-b="'+b.i+'">'+b.html+'</div>'}).join('');
  body.scrollTop=0;
 }).catch(function(){
  body.innerHTML='<p class="pm-err">'+esc(T('err'))+' <button type="button" id="rl">'+esc(T('retry'))+'</button></p>';
  $('rl').onclick=loadPage;
 });
}
function chips(){
 // Suggested questions are generated by a real ask over this page, once per page and language.
 // If that fails or returns fewer than three usable questions, no chips show: nothing canned.
 var c=$('chips');c.innerHTML='';var mine=PAGE+LANG;
 fetchT('/api/page-chips?page='+PAGE+'&lang='+LANG,{},window.__TC||20000).then(function(r){return r.ok?r.json():{chips:[]}}).then(function(d){
  if(mine!==PAGE+LANG)return;c.innerHTML='';
  (d.chips||[]).forEach(function(t){var b=document.createElement('button');b.type='button';b.textContent=t;b.onclick=function(){$('q').value=t;ask(t)};c.appendChild(b)});
 }).catch(function(){});
}
function setLang(l){
 LANG=l;var rtl=l==='ar';
 document.querySelectorAll('#langs button').forEach(function(b){b.setAttribute('aria-checked',b.dataset.lang===l?'true':'false')});
 $('q').placeholder=T('ph');$('go').textContent=T('ask');$('q').dir=rtl?'rtl':'ltr';
 $('pm-h1').textContent=T('h1');$('pm-lead').textContent=T('lead');
 $('pm-ask').setAttribute('dir',rtl?'rtl':'ltr');
 ['pm-head','tabs'].forEach(function(i){$(i).setAttribute('dir',rtl?'rtl':'ltr')});
 document.querySelectorAll('#tabs button').forEach(function(b){b.textContent=T('tabs')[b.dataset.page]});
 $('nav-all').textContent=T('navall');$('nav-study').textContent=T('navstudy');$('how-btn').textContent=T('how');
 $('pm-open').textContent=T('open');$('pm-foot').textContent=T('foot');
 var lb=$('pm-label');if(lb.textContent)lb.textContent=T('tabs')[PAGE];
 document.documentElement.lang=l==='zh'?'zh-Hans':l;
 chips();
}
function clearHl(){document.querySelectorAll('#pm-body mark.hl').forEach(function(m){var p=m.parentNode;while(m.firstChild)p.insertBefore(m.firstChild,m);p.removeChild(m)})}
function highlight(idx,focus){
 clearHl();var first=null;
 idx.forEach(function(i){
  var el=document.querySelector('#pm-body [data-b="'+i+'"]');if(!el)return;
  var m=document.createElement('mark');m.className='hl';
  while(el.firstChild)m.appendChild(el.firstChild);el.appendChild(m);
  if(!first||i===focus)first=m;
 });
 if(first)first.scrollIntoView({behavior:'smooth',block:'center'});
 return !!first;
}
function ask(q){
 if(busy||!q)return;busy=true;$('go').disabled=true;clearHl();
 var r=$('pm-result');r.hidden=false;r.removeAttribute('dir');r.innerHTML='<p class="pm-load">'+esc(T('busy'))+'</p>';
 var go=function(attempt){
  return fetchT('/api/page-ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page:PAGE,q:q,lang:LANG})},attempt?(window.__T2||60000):(window.__T1||35000))
   .then(function(res){if(res.status===504)throw 'timeout';if(!res.ok)throw 'err';return res.json()});
 };
 go(0).catch(function(e){if(e==='err')throw e;return go(1)}).then(function(d){
  if(d.declined){r.innerHTML='<p>'+esc(T('decl'))+'</p>';return}
  r.setAttribute('dir',d.dir);
  var h=md(d.answer);
  if(d.lang!=='en'&&!d.lang_ok){h='<p class="pm-err">'+esc(T('wrong'))+'</p>'+h}
  var cite='';
  if(d.cite==='found')cite='<div class="pm-cite"><span>'+esc(T('found'))+'</span><button type="button" id="showhl">'+esc(T('show'))+'</button></div>';
  else if(d.cite==='unverified')cite='<div class="pm-cite none">'+esc(T('nohl'))+'</div>';
  r.innerHTML=h+cite;
  if(d.located){highlight(d.highlight,d.focus);$('showhl').onclick=function(){highlight(d.highlight,d.focus)}}
 }).catch(function(){
  r.innerHTML='<p class="pm-err">'+esc(T('err'))+' <button type="button" id="rt">'+esc(T('retry'))+'</button></p>';
  $('rt').onclick=function(){busy=false;ask(q)};
 }).finally(function(){busy=false;$('go').disabled=false});
}
document.querySelectorAll('#tabs button').forEach(function(b){b.onclick=function(){
 document.querySelectorAll('#tabs button').forEach(function(x){x.setAttribute('aria-selected',x===b?'true':'false')});
 PAGE=b.dataset.page;chips();loadPage();
}});
document.querySelectorAll('#langs button').forEach(function(b){b.onclick=function(){setLang(b.dataset.lang)}});
$('ask-form').onsubmit=function(e){e.preventDefault();ask($('q').value.trim())};
var modal=$('modal');
function closeM(){modal.hidden=true;document.body.style.overflow=''}
$('how-btn').onclick=function(){modal.hidden=false;document.body.style.overflow='hidden';
 fetch('/static/page-reveal.html').then(function(r){return r.text()}).then(function(t){$('modal-content').innerHTML=t});};
$('modal-close').onclick=closeM;
modal.addEventListener('click',function(e){if(e.target===modal)closeM()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeM()});
setLang('en');loadPage();
})();
