(function(){var b=document.getElementById('burger'),n=document.getElementById('mainnav');if(!b||!n)return;
b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false')});})();
