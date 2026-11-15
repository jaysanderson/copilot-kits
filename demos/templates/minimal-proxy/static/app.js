(function(){
'use strict';
var I18N={
 en:{h1:'Ask us anything about studying at University',lead:'Get a straight answer, with the pages it came from.',label:'Your question',ph:'e.g. How do I apply?',ask:'Ask',
  chips:['How do I apply as an international student?','What are the entry requirements for undergraduate study?','What scholarships are available?','Which campuses does University have?'],
  found:'Pages found on university.edu.au',working:'Finding the answer in University’s pages...',slow:'Taking longer than usual. Trying again...',fail:'We could not get an answer right now.',retry:'Try again',
  declined:'We could not find a sourced answer to that in University’s pages. Try rephrasing, or contact University directly.',contact:'Contact University',sources:'Sources',
  notlang:'This answer came back in English rather than your chosen language. The sources are linked below.',asked:'You asked'},
 zh:{h1:'关于在大学学习，随时提问',lead:'直接得到答案，并附上来源页面。',label:'您的问题',ph:'例如：如何申请？',ask:'提问',
  chips:['国际学生如何申请？','本科入学要求是什么？','有哪些奖学金？','大学有哪些校区？'],
  found:'在 university.edu.au 找到的页面',working:'正在大学的网页中查找答案...',slow:'耗时比平时长，正在重试...',fail:'目前无法获取答案。',retry:'重试',
  declined:'在大学的网页中没有找到有来源支持的答案。请换一种问法，或直接联系大学。',contact:'联系大学',sources:'来源',
  notlang:'此答案以英文返回，而不是您选择的语言。来源链接见下方。',asked:'您的提问'},
 ar:{h1:'اسأل أي شيء عن الدراسة في جامعة مردوخ',lead:'احصل على إجابة واضحة مع الصفحات التي استندت إليها.',label:'سؤالك',ph:'مثال: كيف أتقدم؟',ask:'اسأل',
  chips:['كيف أتقدم بطلب كطالب دولي؟','ما هي شروط القبول للدراسة الجامعية؟','ما المنح الدراسية المتاحة؟','أين تقع جامعة مردوخ؟'],
  found:'صفحات وُجدت على university.edu.au',working:'جارٍ البحث عن الإجابة في صفحات مردوخ...',slow:'استغرق الأمر وقتاً أطول من المعتاد. نعيد المحاولة...',fail:'تعذّر الحصول على إجابة الآن.',retry:'حاول مرة أخرى',
  declined:'لم نجد إجابة موثقة بالمصادر في صفحات مردوخ. جرّب صياغة أخرى أو تواصل مع الجامعة مباشرة.',contact:'تواصل مع مردوخ',sources:'المصادر',
  notlang:'جاءت هذه الإجابة بالإنجليزية بدلاً من اللغة التي اخترتها. المصادر موضحة أدناه.',asked:'سؤالك'},
 id:{h1:'Tanyakan apa saja tentang kuliah di University',lead:'Dapatkan jawaban yang jelas, lengkap dengan halaman sumbernya.',label:'Pertanyaan Anda',ph:'mis. Bagaimana cara mendaftar?',ask:'Tanya',
  chips:['Bagaimana cara mendaftar sebagai mahasiswa internasional?','Apa persyaratan masuk untuk program sarjana?','Beasiswa apa saja yang tersedia?','University memiliki kampus di mana saja?'],
  found:'Halaman ditemukan di university.edu.au',working:'Mencari jawaban di halaman University...',slow:'Butuh waktu lebih lama dari biasanya. Mencoba lagi...',fail:'Kami belum bisa mendapatkan jawaban saat ini.',retry:'Coba lagi',
  declined:'Kami tidak menemukan jawaban bersumber untuk itu di halaman University. Coba ubah pertanyaan, atau hubungi University langsung.',contact:'Hubungi University',sources:'Sumber',
  notlang:'Jawaban ini kembali dalam bahasa Inggris, bukan bahasa pilihan Anda. Sumbernya ditautkan di bawah.',asked:'Pertanyaan Anda'}
};
var lang='en';
var $=function(id){return document.getElementById(id)};
var T=function(k){return I18N[lang][k]};
var q=$('q'),res=$('result'),wrap=$('result-wrap'),go=$('go');
// Timeouts (hard rule): short first attempt fails fast into a visible retry; longer second.
var T1=(window.__T1||30000),T2=(window.__T2||70000);

var esc=MuMd.esc;
// One shared renderer (static/mdlite.js); every markdown heading on this surface renders as h3.
function md(text){return MuMd.md(text,{h:3,cites:true})}
window.MU_md=md;

function setLang(l){
 lang=l;
 document.querySelectorAll('#langs button').forEach(function(b){b.setAttribute('aria-checked',b.dataset.lang===l?'true':'false')});
 document.querySelectorAll('[data-i18n]').forEach(function(e){e.textContent=T(e.dataset.i18n)});
 q.placeholder=T('ph');
 var rtl=l==='ar';
 q.dir=rtl?'rtl':'ltr';
 document.querySelector('.ask-card').setAttribute('dir',rtl?'rtl':'ltr');
 document.querySelector('.ask-card').lang=l==='zh'?'zh-Hans':l;
 var c=$('chips');c.innerHTML='';
 T('chips').forEach(function(t){var b=document.createElement('button');b.type='button';b.textContent=t;b.onclick=function(){q.value=t;ask(t)};c.appendChild(b)});
}
document.querySelectorAll('#langs button').forEach(function(b){b.onclick=function(){setLang(b.dataset.lang)}});

function post(qq,ms){
 var ctl=new AbortController(),t=setTimeout(function(){ctl.abort()},ms);
 return fetch('/api/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q:qq,lang:lang}),signal:ctl.signal})
  .then(function(r){clearTimeout(t);if(!r.ok){var e=new Error('http');e.status=r.status;throw e}return r.json()},function(e){clearTimeout(t);throw e});
}
function show(html,rtl){wrap.hidden=false;res.innerHTML=html;wrap.scrollIntoView({behavior:'smooth',block:'start'})}
function loading(msg,pages){
 var h='<div class="loading"><div class="spin"></div><span>'+esc(msg)+'</span></div>';
 if(pages&&pages.length){h+='<div class="found"><h4>'+esc(T('found'))+'</h4><ul>'+pages.map(function(p){return '<li>'+(p.url?'<a href="'+esc(p.url)+'" target="_blank" rel="noopener">'+esc(p.title)+'</a>':esc(p.title))+'</li>'}).join('')+'</ul></div>'}
 show(h);
}
function failure(qq){
 show('<div class="err"><p>'+esc(T('fail'))+'</p><button type="button" id="retry">'+esc(T('retry'))+'</button></div>');
 $('retry').onclick=function(){ask(qq)};
}
var busy=false,foundPages=null,seq=0;
function ask(qq){
 qq=(qq||'').trim();if(!qq||busy)return;
 busy=true;go.disabled=true;foundPages=null;var my=++seq;loading(T('working'));
 fetch('/api/pages',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q:qq})}).then(function(r){return r.ok?r.json():null}).then(function(d){
  if(d&&d.pages&&d.pages.length&&busy&&my===seq){foundPages=d.pages;loading(T('working'),foundPages)}}).catch(function(){});
 var stalled=function(e){return e&&(e.name==='AbortError'||e.status===504)};
 post(qq,T1).catch(function(e){
  if(stalled(e)){loading(T('slow'),foundPages);return post(qq,T2)}
  throw e;
 }).then(function(d){render(qq,d)},function(){failure(qq)})
 .then(function(){busy=false;go.disabled=false});
}
function render(qq,d){
 var dir=d.dir||'ltr';
 var h='<p class="q" dir="'+dir+'">'+esc(T('asked'))+': '+esc(qq)+'</p>';
 if(d.declined){
  h+='<div class="answer"><p>'+esc(T('declined'))+'</p></div><div class="ctas"><a class="alt" rel="noopener" href="https://www.university.edu.au/contact-us">'+esc(T('contact'))+'</a></div>';
  show(h);return;
 }
 h+='<div class="answer" dir="'+dir+'" lang="'+(lang==='zh'?'zh-Hans':lang)+'">'+md(d.answer)+'</div>';
 if(d.lang_ok===false)h+='<div class="note">'+esc(T('notlang'))+'</div>';
 h+='<div class="sources" dir="ltr"><h4>'+esc(T('sources'))+'</h4><ol>';
 d.sources.forEach(function(s){
  h+='<li id="src-'+s.n+'"><span class="n">'+s.n+'</span>'+(s.url?'<a href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.title)+'</a>':'<span>'+esc(s.title)+'</span>')+'</li>';
 });
 h+='</ol></div>';
 if(d.ctas&&d.ctas.length){
  h+='<div class="ctas">'+d.ctas.map(function(c,i){return '<a class="'+(i?'alt':'')+'" target="_blank" rel="noopener" href="'+esc(c.url)+'">'+esc(c.label)+'</a>'}).join('')+'</div>';
 }
 show(h);
}
$('ask-form').addEventListener('submit',function(e){e.preventDefault();ask(q.value)});

// How this works: content fetched on open so the reveal is a separate document.
var modal=$('modal');
function closeM(){modal.hidden=true;document.body.style.overflow=''}
$('how-btn').onclick=function(){
 modal.hidden=false;document.body.style.overflow='hidden';
 fetch('/static/reveal.html').then(function(r){return r.text()}).then(function(t){$('modal-content').innerHTML=t});
};
$('modal-close').onclick=closeM;
modal.addEventListener('click',function(e){if(e.target===modal)closeM()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeM()});
setLang('en');
})();
