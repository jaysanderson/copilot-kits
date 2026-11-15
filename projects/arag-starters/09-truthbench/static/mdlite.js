/* THE markdown renderer for answer text in this app. One implementation, imported by every surface
   (home app.js, /page page.js, /wander wander.js, and any new surface). The embeddable widget keeps
   its own self-contained copy because it ships to other origins; tests/md_check.py holds both to
   the same fixture.

     MuMd.md(text, opts)      block render: headings, nested bullet and numbered lists, paragraphs
     MuMd.inline(text, opts)  inline render: links, mailto, bare URLs, bold, italic, escapes
     MuMd.esc(text)           HTML-escape

   opts.h      heading tag level every markdown heading maps to (default 4)
   opts.cites  citation markers from our servers become superscript links (default on; false leaves them)
   Right-to-left text: Latin and numeric runs (phone numbers, names, times) are wrapped in <bdi dir="ltr">
   automatically whenever the text contains Arabic or Hebrew, so they cannot scramble visually. */
(function(){
var ESC0='',ESC1='';
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var RTL=/[֐-ࣿ]/;
var RUN=/[A-Za-z0-9+(][A-Za-z0-9 ,.:+\-–\/%$&'@()]*[A-Za-z0-9%)]|[A-Za-z0-9]/g;
function isolate(html){
 // Only text nodes: leave tags and entities alone.
 return html.split(/(<[^>]*>|&[a-zA-Z#0-9]+;)/).map(function(part,i){
  if(i%2||!part)return part;
  return part.replace(RUN,function(run){
   var nowrap=/\d/.test(run)&&run.length<=28?' style="white-space:nowrap"':'';
   return '<bdi dir="ltr"'+nowrap+'>'+run+'</bdi>';
  });
 }).join('');
}
function inline(s,o){
 o=o||{};
 var rtl=o.rtl===undefined?RTL.test(s):o.rtl;
 s=esc(s);
 var codes=[];
 s=s.replace(/`([^`\n]+)`/g,function(_,c){codes.push(c);return '\uE002'+String.fromCharCode(0xE200+codes.length-1)+'\uE003'});
 s=s.replace(/\\([*_#\[\]()`>~|\-.!+])/g,function(_,c){return ESC0+String.fromCharCode(0xE100+c.charCodeAt(0))+ESC1});
 s=s.replace(/&lt;(https?:\/\/[^\s&]+?)&gt;/g,'<a href="$1" target="_blank" rel="noopener">$1</a>');
 s=s.replace(/\[([^\]]+)\]\(mailto:([^)\s?]+)[^)]*\)/g,'<a href="mailto:$2">$1</a>');
 s=s.replace(/\[([^\]]+)\]\(tel:(\+?[\d]+)\)/g,'<a href="tel:$2">$1</a>');
 s=s.replace(/\[([^\]]+)\]\((?!https?:\/\/|mailto:|tel:)[^)]*\)/g,'$1');
 s=s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
 s=s.replace(/(^|[\s(])(https?:\/\/[^\s<)\u27E6]+[^\s<).,;:!?\u27E6\u27E7])/g,'$1<a href="$2" target="_blank" rel="noopener">$2</a>');
 s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
 s=s.replace(/\*([^*\n]+)\*/g,'<em>$1</em>');
 if(o.cites!==false){
  s=s.replace(/⟦([\d,]+)⟧/g,function(_,n){
   return '<sup class="c">'+n.split(',').map(function(x){return '<a href="#src-'+x+'" aria-label="Source '+x+'">'+x+'</a>'}).join('')+'</sup>';
  });
 }
 if(rtl)s=isolate(s);
 s=s.replace(/\uE002([\uE200-\uE2FF])\uE003/g,function(_,i){return codes[i.charCodeAt(0)-0xE200]});
 return s.replace(new RegExp(ESC0+'([\\uE100-\\uE1FF])'+ESC1,'g'),function(_,n){return esc(String.fromCharCode(n.charCodeAt(0)-0xE100))});
}
// The model sometimes writes a bullet list on ONE line: "...including: * One. * Two" (and after full-width
// stops: "。* Two"). A "*" that follows whitespace or sentence punctuation and is itself followed by
// whitespace is a list marker, not emphasis (emphasis hugs its text), so break the line there.
function splitInlineBullets(t){
 return t.split('\n').map(function(l){
  if(/^\s*[*+\-]\s/.test(l)&&!/\s\*\s+\S.*\s\*\s+\S/.test(l))return l;
  return l.replace(/([\s\u3002\uFF01\uFF1F\uFF1A\uFF1B\uFF09:;.!?)\u201D\u06D4\u061F])\*(?!\*)\s+(?=\S)/g,function(m,p,off,str){
   var before=str.slice(0,off+1).replace(/\s+$/,'').slice(-1),after=str.charAt(off+m.length);
   if(/\d/.test(before)&&/\d/.test(after))return m; // "2 * 3" is arithmetic
   var pre=str.slice(0,off),opens=(pre.match(/(^|[\s(])\*(?=[^\s*])/g)||[]).length,closes=(pre.match(/[^\s*]\*(?=[\s.,;:!?)]|$)/g)||[]).length;
   if(opens>closes)return m; // inside an open *emphasis* span: this star closes it
   return (/\s/.test(p)?'':p)+'\n* ';
  });
 }).join('\n');
}
function md(text,o){
 o=o||{};var h='h'+(o.h||4);
 o=Object.assign({},o,{rtl:RTL.test(String(text))});
 var out=[],stack=[],lines=splitInlineBullets(String(text).replace(/\r/g,'')).split('\n');
 function closeTo(n){while(stack.length>n){out.push('</li></'+stack.pop().t+'>')}}
 lines.forEach(function(l){
  var m;
  if(!l.trim()){closeTo(0);return}
  if(/^\s*(-{3,}|\*{3,})\s*$/.test(l)){closeTo(0);out.push('<hr>');return}
  if((m=l.match(/^\s*#{1,6}\s+(.*)/))){closeTo(0);out.push('<'+h+'>'+inline(m[1],o)+'</'+h+'>');return}
  var li=l.match(/^(\s*)([*+\-]|\d+[.)])\s+(.*)/);
  if(li){
   var ind=li[1].replace(/\t/g,'    ').length,t=/\d/.test(li[2])?'ol':'ul';
   while(stack.length&&stack[stack.length-1].ind>ind)out.push('</li></'+stack.pop().t+'>');
   if(stack.length&&stack[stack.length-1].ind===ind&&stack[stack.length-1].t===t){out.push('</li><li>')}
   else if(stack.length&&stack[stack.length-1].ind===ind){out.push('</li></'+stack.pop().t+'><'+t+'><li>');stack.push({ind:ind,t:t})}
   else{out.push('<'+t+'><li>');stack.push({ind:ind,t:t})}
   out.push(inline(li[3],o));return;
  }
  closeTo(0);out.push('<p>'+inline(l,o)+'</p>');
 });
 closeTo(0);return out.join('');
}
window.MuMd={md:md,inline:inline,esc:esc};
})();
