(function(){
'use strict';
// Home page entry to the chat. The hero keeps its ask box; submitting (or choosing a starter question)
// navigates to /answers?q=...&lang=..., where the answer streams as a conversation. Nothing is answered here.
var S={
 en:{start:'Ask a question about studying at University',send:'Ask',hint:'This is a conversation. Ask, follow up, and we will point you to the right page.'},
 zh:{start:'询问有关在大学学习的问题',send:'提问',hint:'这是一场对话。提问、追问，我们会带您前往合适的页面。'},
 ar:{start:'اطرح سؤالاً عن الدراسة في جامعة مردوخ',send:'اسأل',hint:'هذه محادثة. اسأل ثم تابع أسئلتك وسنوجّهك إلى الصفحة المناسبة.'},
 id:{start:'Ajukan pertanyaan tentang kuliah di University',send:'Tanya',hint:'Ini percakapan. Tanyakan, lanjutkan, dan kami arahkan ke halaman yang tepat.'}
};
var $=function(id){return document.getElementById(id)};
var form=$('ask-form'),hq=$('q');
if(!form||!hq)return;
function lang(){var b=document.querySelector('#langs [aria-checked="true"]');return b?b.dataset.lang:'en'}
function go(q){q=(q||'').trim();if(!q)return;location.href='/answers?q='+encodeURIComponent(q)+'&lang='+lang()}
var card=form.parentNode,lead=card.querySelector('.lead');
var hint=document.createElement('p');hint.className='chathint';if(lead)lead.parentNode.insertBefore(hint,lead.nextSibling);
// The hero's own form is replaced by one composer, so there is a single input.
var comp=document.createElement('form');comp.className='composer in-hero';comp.autocomplete='off';
comp.innerHTML='<label class="sr" for="cq"></label><input id="cq" maxlength="500" required><button type="submit"></button>';
form.parentNode.insertBefore(comp,form.nextSibling);
var cq=comp.querySelector('input'),btn=comp.querySelector('button');
function chrome(){var s=S[lang()];hint.textContent=s.hint;cq.placeholder=s.start;comp.querySelector('label').textContent=s.start;btn.textContent=s.send;comp.setAttribute('dir',lang()==='ar'?'rtl':'ltr')}
document.querySelectorAll('#langs button').forEach(function(b){b.addEventListener('click',function(){setTimeout(chrome,0)})});
comp.addEventListener('submit',function(e){e.preventDefault();go(cq.value)});
form.addEventListener('submit',function(e){e.preventDefault();e.stopImmediatePropagation();go(hq.value)},true);
$('chips').addEventListener('click',function(e){var t=e.target.closest('button');if(!t)return;e.stopPropagation();e.preventDefault();go(t.textContent)},true);
chrome();
})();
