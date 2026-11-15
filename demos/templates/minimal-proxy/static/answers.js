(function(){
'use strict';
// Results page: the conversation. /answers?q=<question>&lang=<en|zh|ar|id>. The answer streams here; the
// question in the URL makes every first question a shareable, gateable page.
var D={ // destination chrome: t = card title, b = button label, d = one line
 apply:{en:['How to apply','Start your application','Steps, dates and the application pathways.'],zh:['如何申请','开始申请','申请步骤、日期与申请途径。'],ar:['كيفية التقدم','ابدأ طلبك','الخطوات والمواعيد ومسارات التقدم.'],id:['Cara mendaftar','Mulai pendaftaran','Langkah, tanggal, dan jalur pendaftaran.']},
 courses:{en:['Find a course','Search courses','Browse every course and study area.'],zh:['查找课程','搜索课程','浏览所有课程与学习领域。'],ar:['ابحث عن دورة','ابحث في الدورات','تصفّح جميع الدورات ومجالات الدراسة.'],id:['Cari kursus','Cari kursus','Telusuri semua kursus dan bidang studi.']},
 scholarships:{en:['Scholarships','See scholarships','What support you could be eligible for.'],zh:['奖学金','查看奖学金','您可能符合资格的资助。'],ar:['المنح الدراسية','اطّلع على المنح','الدعم الذي قد تكون مؤهلاً له.'],id:['Beasiswa','Lihat beasiswa','Dukungan yang mungkin bisa Anda dapatkan.']},
 entry:{en:['Entry requirements','Check entry requirements','What you need to be admitted.'],zh:['入学要求','查看入学要求','入学所需条件。'],ar:['شروط القبول','تحقق من شروط القبول','ما تحتاجه للقبول.'],id:['Persyaratan masuk','Cek persyaratan masuk','Yang Anda perlukan untuk diterima.']},
 international:{en:['International students','International student hub','Everything for studying from overseas.'],zh:['国际学生','国际学生专区','海外留学所需的一切信息。'],ar:['الطلاب الدوليون','مركز الطلاب الدوليين','كل ما يخص الدراسة من الخارج.'],id:['Mahasiswa internasional','Pusat mahasiswa internasional','Semua untuk belajar dari luar negeri.']},
 fees:{en:['Fees','See fees and costs','Course fees, support and cost of living.'],zh:['学费','查看学费与费用','课程费用、资助与生活成本。'],ar:['الرسوم','اطّلع على الرسوم والتكاليف','رسوم الدورات والدعم وتكلفة المعيشة.'],id:['Biaya','Lihat biaya','Biaya kuliah, dukungan, dan biaya hidup.']},
 visit:{en:['Open day','Plan your open day visit','See the campus and meet the people.'],zh:['开放日','规划开放日参观','参观校园，结识师生。'],ar:['اليوم المفتوح','خطط لزيارة اليوم المفتوح','شاهد الحرم الجامعي والتقِ بالناس.'],id:['Hari terbuka','Rencanakan kunjungan','Lihat kampus dan bertemu orang-orangnya.']},
 tours:{en:['Campus maps and tours','Explore the campuses','Where each campus is and how to tour it.'],zh:['校园地图与参观','探索校区','各校区位置与参观方式。'],ar:['خرائط الحرم وجولاته','استكشف الحرم الجامعي','مواقع الحرم وكيفية زيارته.'],id:['Peta dan tur kampus','Jelajahi kampus','Lokasi kampus dan cara mengunjunginya.']},
 accommodation:{en:['Accommodation','Find accommodation','Places to live while you study.'],zh:['住宿','查找住宿','求学期间的居住选择。'],ar:['السكن','ابحث عن سكن','أماكن للعيش أثناء الدراسة.'],id:['Akomodasi','Cari akomodasi','Tempat tinggal selama kuliah.']},
 visa:{en:['Student visa','Visa information','Before you move to Perth.'],zh:['学生签证','签证信息','赴珀斯前的准备。'],ar:['تأشيرة الطالب','معلومات التأشيرة','قبل الانتقال إلى بيرث.'],id:['Visa pelajar','Informasi visa','Sebelum pindah ke Perth.']},
 english:{en:['English proficiency','English test options','Accepted tests and scores.'],zh:['英语水平','英语考试选项','认可的考试与分数。'],ar:['إتقان اللغة الإنجليزية','خيارات اختبار اللغة','الاختبارات والدرجات المقبولة.'],id:['Kemahiran bahasa Inggris','Pilihan tes bahasa Inggris','Tes dan skor yang diterima.']},
 contact:{en:['Contact University','Contact University','Talk to a person at the university.'],zh:['联系大学','联系大学','与大学工作人员交流。'],ar:['تواصل مع مردوخ','تواصل مع مردوخ','تحدّث إلى أحد موظفي الجامعة.'],id:['Hubungi University','Hubungi University','Bicara dengan staf universitas.']}
};
var C={ // chat chrome
 en:{hint:'This is a conversation. Ask, follow up, and we will point you to the right page.', draft:'Drafting from University’s pages. Sources are checked when it finishes.',start:'Ask a question about studying at University', you:'You',bot:'University assistant',typing:'Finding the answer in University’s pages',slow:'Taking longer than usual. Trying again',found:'Pages found on university.edu.au',sources:'Sources for this answer',next:'Where to next',nextCited:'Suggested from the pages this answer used',open:'Open page',follow:'Ask a follow-up',send:'Send',fail:'We could not get an answer right now.',retry:'Try again',declined:'We could not find a sourced answer to that in University’s pages. A person at University can help directly.',notlang:'This answer came back in English rather than your chosen language. The sources are linked below.',clear:'New conversation',intro:'Ask a question and I will answer from University’s own pages, then point you to where to go next.'},
 zh:{hint:'这是一场对话。提问、追问，我们会带您前往合适的页面。', draft:'正在根据大学的网页撰写。完成后会核对来源。',start:'询问有关在大学学习的问题', you:'您',bot:'默多克助手',typing:'正在大学的网页中查找答案',slow:'耗时比平时长，正在重试',found:'在 university.edu.au 找到的页面',sources:'本答案的来源',next:'下一步去哪里',nextCited:'根据本答案引用的页面推荐',open:'打开页面',follow:'继续提问',send:'发送',fail:'目前无法获取答案。',retry:'重试',declined:'在大学的网页中没有找到有来源支持的答案。大学的工作人员可以直接帮助您。',notlang:'此答案以英文返回，而不是您选择的语言。来源链接见下方。',clear:'新对话',intro:'提出问题，我会根据大学自己的网页作答，并指引您下一步去哪里。'},
 ar:{hint:'هذه محادثة. اسأل ثم تابع أسئلتك وسنوجّهك إلى الصفحة المناسبة.', draft:'جارٍ كتابة الإجابة من صفحات مردوخ. يتم التحقق من المصادر عند الانتهاء.',start:'اطرح سؤالاً عن الدراسة في جامعة مردوخ', you:'أنت',bot:'مساعد مردوخ',typing:'جارٍ البحث عن الإجابة في صفحات مردوخ',slow:'استغرق الأمر وقتاً أطول من المعتاد. نعيد المحاولة',found:'صفحات وُجدت على university.edu.au',sources:'مصادر هذه الإجابة',next:'إلى أين بعد ذلك',nextCited:'مقترحات من الصفحات التي استندت إليها الإجابة',open:'افتح الصفحة',follow:'اطرح سؤالاً آخر',send:'إرسال',fail:'تعذّر الحصول على إجابة الآن.',retry:'حاول مرة أخرى',declined:'لم نجد إجابة موثقة بالمصادر في صفحات مردوخ. يمكن لأحد موظفي الجامعة مساعدتك مباشرة.',notlang:'جاءت هذه الإجابة بالإنجليزية بدلاً من اللغة التي اخترتها. المصادر موضحة أدناه.',clear:'محادثة جديدة',intro:'اطرح سؤالاً وسأجيب من صفحات مردوخ نفسها، ثم أدلّك على وجهتك التالية.'},
 id:{hint:'Ini percakapan. Tanyakan, lanjutkan, dan kami arahkan ke halaman yang tepat.', draft:'Menyusun dari halaman University. Sumber diperiksa setelah selesai.',start:'Ajukan pertanyaan tentang kuliah di University', you:'Anda',bot:'Asisten University',typing:'Mencari jawaban di halaman University',slow:'Butuh waktu lebih lama dari biasanya. Mencoba lagi',found:'Halaman ditemukan di university.edu.au',sources:'Sumber jawaban ini',next:'Langkah berikutnya',nextCited:'Disarankan dari halaman yang dipakai jawaban ini',open:'Buka halaman',follow:'Ajukan pertanyaan lanjutan',send:'Kirim',fail:'Kami belum bisa mendapatkan jawaban saat ini.',retry:'Coba lagi',declined:'Kami tidak menemukan jawaban bersumber untuk itu di halaman University. Staf University dapat membantu langsung.',notlang:'Jawaban ini kembali dalam bahasa Inggris, bukan bahasa pilihan Anda. Sumbernya ditautkan di bawah.',clear:'Percakapan baru',intro:'Ajukan pertanyaan dan saya akan menjawab dari halaman resmi University, lalu menunjukkan tujuan berikutnya.'}
};
var $=function(id){return document.getElementById(id)};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
// Markdown: the one shared renderer in app.js (exported as window.MU_md). No third copy here.
function md(t){
 return guard(md0(t));
}
// A marker must never paint raw: if any survives the renderer, give it the same badge markup.
function guard(h){return h.indexOf('\u27e6')<0?h:h.replace(/\u27e6([\d,]+)\u27e7/g,function(_,n){return '<sup class="c">'+n.split(',').map(function(x){return '<a href="#" aria-label="Source '+x+'">'+x+'</a>'}).join('')+'</sup>'})}
function md0(t){
 // Prefer the shared mdlite renderer once it handles citation markers (feature-tested); app.js's export until then.
 if(window.MuMd&&/<sup/.test(window.MuMd.md('a\u27e61\u27e7')))return window.MuMd.md(t,{h:3});
 if(typeof window.MU_md==='function')return window.MU_md(t);
 return t.split(/\n+/).filter(Boolean).map(function(p){return '<p>'+esc(p.replace(/⟦[\d,]+⟧/g,''))+'</p>'}).join('');
}

var P={
 en:{back:'Back to University home',how:'How this works',h:'Your question',emptyH:'Ask University a question',emptyP:'Pick one to start, or type your own below. You can keep the conversation going.',title:'Answers'},
 zh:{back:'返回大学首页',how:'工作原理',h:'您的问题',emptyH:'向大学提问',emptyP:'选择一个问题开始，或在下方输入您自己的问题。您可以继续追问。',title:'答案'},
 ar:{back:'العودة إلى صفحة مردوخ الرئيسية',how:'كيف يعمل هذا',h:'سؤالك',emptyH:'اسأل جامعة مردوخ',emptyP:'اختر سؤالاً للبدء أو اكتب سؤالك في الأسفل. يمكنك متابعة المحادثة.',title:'الإجابات'},
 id:{back:'Kembali ke beranda University',how:'Cara kerjanya',h:'Pertanyaan Anda',emptyH:'Tanyakan sesuatu tentang University',emptyP:'Pilih satu untuk memulai, atau ketik sendiri di bawah. Anda bisa melanjutkan percakapan.',title:'Jawaban'}
};
var STARTERS={
 en:['How do I apply as an international student?','What are the entry requirements for undergraduate study?','What scholarships are available?','Which campuses does University have?'],
 zh:['国际学生如何申请？','本科入学要求是什么？','有哪些奖学金？','大学有哪些校区？'],
 ar:['كيف أتقدم بطلب كطالب دولي؟','ما هي شروط القبول للدراسة الجامعية؟','ما المنح الدراسية المتاحة؟','أين تقع جامعة مردوخ؟'],
 id:['Bagaimana cara mendaftar sebagai mahasiswa internasional?','Apa persyaratan masuk untuk program sarjana?','Beasiswa apa saja yang tersedia?','University memiliki kampus di mana saja?']
};
var params=new URLSearchParams(location.search);
var curLang=['en','zh','ar','id'].indexOf(params.get('lang'))>=0?params.get('lang'):'en';
function lang(){return curLang}
function T(k){return C[curLang][k]}
var panel=$('chat'),thread=$('thread'),cq=$('cq'),csend=$('csend'),composer=$('composer');
var history=[],busy=false,turnSeq=0;
window.__chatTiming=[];
function chrome(){
 var l=curLang,rtl=l==='ar',p=P[l];
 document.documentElement.lang=l==='zh'?'zh-Hans':l;document.documentElement.dir=rtl?'rtl':'ltr';
 document.title='The university - '+p.title;
 $('back').querySelector('span').textContent=p.back;$('how-btn').textContent=p.how;
 $('emptyH').textContent=p.emptyH;$('emptyP').textContent=p.emptyP;
 panel.querySelector('.chat-title').textContent=T('bot');
 composer.querySelector('label').textContent=T('follow');
 var has=!!thread.querySelector('.msg.user');
 cq.placeholder=has?T('follow'):T('start');csend.textContent=T('send');
 $('newchat').textContent=T('clear');$('newchat').style.visibility=has?'visible':'hidden';
 document.querySelectorAll('#langs button').forEach(function(b){b.setAttribute('aria-checked',b.dataset.lang===l?'true':'false')});
 var st=$('starters');st.innerHTML='';STARTERS[l].forEach(function(t){var b=document.createElement('button');b.type='button';b.textContent=t;b.onclick=function(){ask(t)};st.appendChild(b)});
}
function brandCard(title,path,i){
 var v=(String(path||title).split('').reduce(function(a,c){return a+c.charCodeAt(0)},0))%3;
 return '<div class="tn tn-brand v'+v+'"><span class="tn-k">university.edu.au</span><span class="tn-t" dir="auto">'+esc(title)+'</span></div>';
}
var seen={};
function thumb(th,title,path){
 if(th&&th.image&&th.key&&seen[th.key])th=null; // same photograph already shown in this response: branded card instead
 if(th&&th.image&&th.key)seen[th.key]=1;
 if(th&&th.image)return '<div class="tn-wrap"><img class="tn-img" src="'+esc(th.image)+'" alt="" loading="lazy" referrerpolicy="no-referrer" data-title="'+esc(title)+'" data-path="'+esc(path||'')+'"></div>';
 return '<div class="tn-wrap">'+brandCard(title,path)+'</div>';
}
// A thumbnail that fails to load becomes the branded card carrying the page's own title.
document.addEventListener('error',function(e){
 var t=e.target;if(!t||!t.classList||!t.classList.contains('tn-img'))return;
 var w=t.parentNode;w.innerHTML=brandCard(t.dataset.title,t.dataset.path);var pt=w.parentNode&&w.parentNode.querySelector('.pc-t');if(pt)pt.remove();
},true);

function pageCard(p){
 var hasImg=!!(p.thumb&&p.thumb.image&&!(p.thumb.key&&seen[p.thumb.key]));
 return '<a class="pcard" href="'+esc(p.url)+'" target="_blank" rel="noopener" dir="ltr">'+thumb(p.thumb,p.title,p.path)+'<span class="pc-body">'+(p.n?'<span class="n">'+p.n+'</span>':'')+(hasImg?'<span class="pc-t">'+esc(p.title)+'</span>':'')+'<span class="pc-u">'+esc((p.path||'').replace(/^\//,'')||'university.edu.au')+'</span></span></a>';
}
function destCard(d,l){
 var t=D[d.key][l];
 return '<a class="dcard" href="'+esc(d.url)+'" target="_blank" rel="noopener">'+thumb(d.thumb,t[0],d.url)+'<span class="dc-body"><span class="dc-t">'+esc(t[0])+'</span><span class="dc-d">'+esc(t[2])+'</span><span class="dc-b">'+esc(t[1])+'<svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><path d="M4 10h11M11 5l5 5-5 5" fill="none" stroke="currentColor" stroke-width="2"/></svg></span></span></a>';
}
function userBubble(q){
 var u=document.createElement('div');u.className='msg user';u.setAttribute('dir','auto');
 u.innerHTML='<span class="who">'+esc(T('you'))+'</span><p>'+esc(q)+'</p>';thread.appendChild(u);return u;
}
function botBlock(){
 var b=document.createElement('div');b.className='msg bot';b.setAttribute('dir',lang()==='ar'?'rtl':'ltr');
 b.innerHTML='<span class="who">'+esc(T('bot'))+'</span><div class="b-typing"></div><div class="b-found"></div><div class="b-answer"></div><div class="b-src"></div><div class="b-next"></div>';
 thread.appendChild(b);return b;
}
function typing(b,msg){b.querySelector('.b-typing').innerHTML='<span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><span>'+esc(msg)+'</span>'}
function scrollTo(el){el.scrollIntoView({behavior:'smooth',block:'nearest'})}

function post(url,body,ms){
 var ctl=new AbortController(),t=setTimeout(function(){ctl.abort()},ms);
 return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:ctl.signal})
  .then(function(r){clearTimeout(t);if(!r.ok){var e=new Error('http');e.status=r.status;throw e}return r.json()},function(e){clearTimeout(t);throw e});
}
var T1=(window.__T1||30000),T2=(window.__T2||70000);

// Streamed reply (NDJSON). Idle timeout resets on every event, so a long answer that keeps arriving never trips
// it, while a stall fails fast into the visible retry. A second attempt gets the longer idle window.
function stream(body,idleMs,onText,onReset){
 var ctl=new AbortController(),timer=null,final=null;
 function arm(){clearTimeout(timer);timer=setTimeout(function(){ctl.abort()},idleMs)}
 arm();
 return fetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:ctl.signal}).then(function(r){
  if(!r.ok){var e=new Error('http');e.status=r.status;throw e}
  var rd=r.body.getReader(),dec=new TextDecoder(),buf='';
  function pump(){return rd.read().then(function(x){
   if(x.done){clearTimeout(timer);if(!final)throw new Error('incomplete');return final}
   arm();buf+=dec.decode(x.value,{stream:true});var parts=buf.split('\n');buf=parts.pop();
   parts.forEach(function(ln){if(!ln.trim())return;var d=JSON.parse(ln);
    if(d.t==='text')onText(d.text);else if(d.t==='reset')onReset();else if(d.t==='error'){var e=new Error('upstream');e.status=502;throw e}else if(d.t==='final')final=d});
   return pump()})}
  return pump();
 },function(e){clearTimeout(timer);throw e});
}
// Draft: complete lines through the shared renderer; the unfinished last line as plain text so half-typed
// markdown ("**Bol", "[text](htt") is never painted raw. The final event replaces all of it.
function drawDraft(b,text,l){
 var ans=b.querySelector('.b-answer'),box=ans.querySelector('.text.draft');
 if(!box){b.querySelector('.b-typing').innerHTML='';ans.innerHTML='<p class="draftnote">'+esc(T('draft'))+'</p><div class="text draft" dir="'+(l==='ar'?'rtl':'ltr')+'" lang="'+(l==='zh'?'zh-Hans':l)+'"></div>';box=ans.querySelector('.text.draft')}
 var cut=text.lastIndexOf('\n'),done=cut<0?'':text.slice(0,cut),tail=cut<0?text:text.slice(cut+1);
 tail=tail.replace(/^\s*[*\-#]+\s+/,'').replace(/\*+|_{2,}|`/g,'').replace(/\[([^\]]*)\]\([^)]*$/,'$1').replace(/\[([^\]]*)$/,'$1');
 box.innerHTML=(done?md(done):'')+(tail?'<p class="tail">'+esc(tail)+'</p>':'');
}

function ask(q){
 q=(q||'').trim();if(!q||busy)return;
 busy=true;csend.disabled=true;$('empty').hidden=true;chrome();
 var l=lang(),my=++turnSeq,t0=performance.now(),tm={q:q,lang:l};window.__chatTiming.push(tm);
 var ub=userBubble(q);var b=botBlock();typing(b,T('typing'));ub.scrollIntoView({behavior:'smooth',block:'start'});
 var painted=false;
 // Stage 1: real retrieval, painted the moment it lands. Runs alongside the answer, not before it.
 post('/api/chat/pages',{q:q},15000).then(function(d){
  if(!d||!d.pages||!d.pages.length||b.dataset.done)return;
  seen={};
  b.querySelector('.b-found').innerHTML='<h4>'+esc(T('found'))+'</h4><div class="prow">'+d.pages.map(pageCard).join('')+'</div>';
  b.classList.add('has-found');
  tm.firstPaintMs=Math.round(performance.now()-t0);tm.pagesServerMs=d.ms;painted=true;scrollTo(b);
 }).catch(function(){});
 var body={q:q,lang:l,history:history.slice(-6)};
 var stalled=function(e){return e&&(e.name==='AbortError'||e.status===504)};
 var onText=function(t){if(!tm.firstTextMs)tm.firstTextMs=Math.round(performance.now()-t0);drawDraft(b,t,l)};
 var onReset=function(){b.querySelector('.b-answer').innerHTML='';typing(b,T('typing'))};
 stream(body,25000,onText,onReset).catch(function(e){
  if(stalled(e)||e.message==='incomplete'){typing(b,T('slow'));b.querySelector('.b-answer').innerHTML='';return stream(body,40000,onText,onReset)}
  throw e;
 }).then(function(d){
  tm.completeMs=Math.round(performance.now()-t0);tm.replyServerMs=d.ms;tm.declined=!!d.declined;
  b.dataset.done='1';render(b,d,q,l);
  history.push({role:'user',text:q});
  if(!d.declined)history.push({role:'assistant',text:d.answer});
 },function(){
  b.dataset.done='1';
  b.querySelector('.b-typing').innerHTML='';
  b.querySelector('.b-answer').innerHTML='<div class="err"><p>'+esc(T('fail'))+'</p><button type="button" class="retry">'+esc(T('retry'))+'</button></div>';
  b.querySelector('.retry').onclick=function(){b.previousSibling.remove();b.remove();busy=false;ask(q)};
 }).then(function(){busy=false;csend.disabled=false;scrollTo(thread.lastChild)});
}
function render(b,d,q,l){
 seen={};
 b.querySelector('.b-typing').innerHTML='';
 var dir=d.dir||'ltr',ans=b.querySelector('.b-answer');
 if(d.declined){
  b.querySelector('.b-found').innerHTML='';b.classList.remove('has-found');
  ans.innerHTML='<div class="text"><p>'+esc(T('declined'))+'</p></div>';
  b.querySelector('.b-next').innerHTML='<h4>'+esc(T('next'))+'</h4><div class="drow one">'+destCard({key:'contact',url:d.contact&&d.contact.url||'https://www.university.edu.au/contact-us'},l)+'</div>';
  return;
 }
 ans.innerHTML='<div class="text" dir="'+dir+'" lang="'+(l==='zh'?'zh-Hans':l)+'">'+md(d.answer)+'</div>'+(d.lang_ok===false?'<div class="note">'+esc(T('notlang'))+'</div>':'');
 // Sources the answer actually cited replace the stage-1 "pages found" row.
 b.querySelector('.b-found').innerHTML='';b.classList.remove('has-found');
 b.querySelector('.b-src').innerHTML='<h4>'+esc(T('sources'))+'</h4><div class="prow">'+d.sources.map(function(s){var c=pageCard(s);return c.replace('<a class="pcard"','<a class="pcard" id="'+'t'+turnSeq+'-src-'+s.n+'"')}).join('')+'</div>';
 ans.querySelectorAll('sup.c a').forEach(function(a){
  a.setAttribute('href','#');
  a.addEventListener('click',function(e){e.preventDefault();var n=a.textContent.trim();var el=b.querySelector('.b-src .pcard:nth-child('+n+')');if(el){el.scrollIntoView({behavior:'smooth',block:'nearest'});el.classList.add('flash');setTimeout(function(){el.classList.remove('flash')},1400)}});
 });
 if(d.dests&&d.dests.length){
  b.querySelector('.b-next').innerHTML='<h4>'+esc(T('next'))+'</h4>'+(d.dest_mode==='cited'?'<p class="cap">'+esc(T('nextCited'))+'</p>':'')+'<div class="drow n'+d.dests.length+'">'+d.dests.map(function(x){return destCard(x,l)}).join('')+'</div>';
 }
}


composer.addEventListener('submit',function(e){e.preventDefault();var v=cq.value;cq.value='';ask(v)});
document.querySelectorAll('#langs button').forEach(function(b){b.onclick=function(){curLang=b.dataset.lang;var u=new URL(location.href);u.searchParams.set('lang',curLang);history_replace(u);chrome()}});
function history_replace(u){try{window.history.replaceState(null,'',u)}catch(e){}}
$('newchat').onclick=function(){if(busy)return;thread.innerHTML='';history=[];$('empty').hidden=false;var u=new URL(location.href);u.searchParams.delete('q');history_replace(u);chrome();cq.focus()};
// How this works: the same reveal document the home page shows.
var modal=$('modal');
function closeM(){modal.hidden=true;document.body.style.overflow=''}
$('how-btn').onclick=function(){modal.hidden=false;document.body.style.overflow='hidden';fetch('/static/reveal.html').then(function(r){return r.text()}).then(function(t){$('modal-content').innerHTML=t})};
$('modal-close').onclick=closeM;modal.addEventListener('click',function(e){if(e.target===modal)closeM()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeM()});
chrome();
var q0=(params.get('q')||'').trim();
if(q0)ask(q0);
})();
