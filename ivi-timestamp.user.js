// ==UserScript==
// @name         IVI TS
// @namespace    http://tampermonkey.net/
// @version      1.4
// @description  Press ` to save video timestamp
// @author       you
// @match        *://*ivi.ru/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

function inject() {
    var code =
        "console.log('[IVI TS] injected');" +
        "document.addEventListener('keydown',function(e){" +
        "if(e.key!=='`')return;" +
        "if(e.target.closest('input,textarea,select,[contenteditable]'))return;" +
        "e.preventDefault();e.stopPropagation();" +
        "var v=document.querySelector('video');" +
        "if(!v){alert('[IVI TS] No video');return};" +
        "var t=v.currentTime;" +
        "var n=(document.querySelector('h1')||{}).textContent||document.title;" +
        "var h=Math.floor(t/3600),m=Math.floor(t%3600/60),s=Math.floor(t%60);" +
        "var fmt=(h<10?'0':'')+h+':'+(m<10?'0':'')+m+':'+(s<10?'0':'')+s;" +
        "fetch('http://localhost:8765/',{" +
        "method:'POST',headers:{'Content-Type':'application/json'}," +
        "body:JSON.stringify({video_name:n,timestamp:t,url:location.href})" +
        "}).then(function(r){return r.json()}).then(function(){" +
        "var el=document.createElement('div');" +
        "el.textContent=fmt+' saved';" +
        "el.style.cssText='position:fixed;bottom:80px;right:20px;z-index:999999;padding:10px 18px;background:rgba(0,0,0,0.85);color:#0f0;border-radius:6px;font:bold 16px monospace;pointer-events:none;';" +
        "document.body.appendChild(el);" +
        "setTimeout(function(){el.style.opacity='0';setTimeout(function(){el.remove()},300)},1500)" +
        "}).catch(function(e){alert('[IVI TS] Error: '+e.message)})" +
        "},true);";

    var s = document.createElement("script");
    s.textContent = code;
    document.documentElement.appendChild(s);
    s.remove();
}

inject();

var observer = new MutationObserver(inject);
observer.observe(document.body, { childList: true, subtree: true });
