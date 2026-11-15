(function(){
'use strict';
var toast=document.getElementById('rs-toast'),tm;
function say(msg){toast.textContent=msg;toast.hidden=false;clearTimeout(tm);tm=setTimeout(function(){toast.hidden=true},1600)}
function fallback(text){var t=document.createElement('textarea');t.value=text;t.setAttribute('readonly','');t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();var ok=false;try{ok=document.execCommand('copy')}catch(e){}document.body.removeChild(t);return ok}
Array.prototype.forEach.call(document.querySelectorAll('.rs-copy'),function(b){
 b.addEventListener('click',function(){
  var text=b.getAttribute('data-copy');
  function done(ok){b.textContent=ok?'Copied':'Copy failed';say(ok?'Copied':'Copy failed: select the text by hand');setTimeout(function(){b.textContent='Copy'},1600)}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).then(function(){done(true)},function(){done(fallback(text))})}
  else done(fallback(text));
 });
});
})();
