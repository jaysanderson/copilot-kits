(function(){
'use strict';
var chipsEl=document.getElementById('sh-chips'),CH=window.SECTION_CHIPS||{};
function widget(){return document.querySelector('[data-ask-widget]')}
function paint(lang){
 var list=CH[lang]||CH.en||[];
 chipsEl.innerHTML='';chipsEl.dir=lang==='ar'?'rtl':'ltr';
 list.forEach(function(q){var b=document.createElement('button');b.type='button';b.textContent=q;
  b.onclick=function(){var w=widget();if(w&&w.askWidget)w.askWidget.ask(q)};chipsEl.appendChild(b)});
}
paint('en');
// The widget announces its language so the suggested questions follow it.
document.addEventListener('ask-lang',function(e){paint(e.detail)});
var modal=document.getElementById('modal');
function closeM(){modal.hidden=true;document.body.style.overflow=''}
document.getElementById('how-btn').onclick=function(){
 modal.hidden=false;document.body.style.overflow='hidden';
 fetch('/static/section-reveal.html').then(function(r){return r.text()}).then(function(t){document.getElementById('modal-content').innerHTML=t});
};
document.getElementById('modal-close').onclick=closeM;
modal.addEventListener('click',function(e){if(e.target===modal)closeM()});
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeM()});
})();
