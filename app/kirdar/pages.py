# -*- coding: utf-8 -*-
"""Kirdar page — single-file HTML/CSS/JS. Chats live in the user's
browser (localStorage); the server only runs the AI calls."""

KIRDAR_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kirdar کردار — Free AI character chat, Urdu-first</title>
<style>
:root{--bg:#faf7f2;--card:#fff;--ink:#241d18;--mut:#7a6a5c;--line:#eadfd2;--acc:#7c4a1e;--acc2:#b45309;--soft:#f3e8d8;--green:#166534}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink)}
header{background:#241d18;color:#f5ead9;padding:14px 18px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
header h1{margin:0;font-size:22px}
header h1 span{font-weight:400;opacity:.85}
header p{margin:2px 0 0;font-size:13px;opacity:.85}
.badge{background:#3f3226;border:1px solid #6b563e;border-radius:999px;padding:5px 12px;font-size:12px}
.badge.ok{background:#14532d;border-color:#166534}
.wrap{display:grid;grid-template-columns:300px 1fr;gap:0;min-height:calc(100vh - 64px)}
aside{border-right:1px solid var(--line);background:#fff;padding:14px;overflow-y:auto}
main{padding:16px 18px;max-width:900px;width:100%;margin:0 auto}
h2{font-size:15px;margin:18px 0 8px}
h2:first-child{margin-top:0}
.char-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.char{border:1px solid var(--line);border-radius:12px;padding:10px;cursor:pointer;background:#fff;text-align:left}
.char:hover{border-color:var(--acc)}
.char.sel{border-color:var(--acc);background:var(--soft)}
.char .em{font-size:26px}
.char b{display:block;font-size:13px;margin-top:2px}
.char small{color:var(--mut);font-size:11.5px;line-height:1.35;display:block}
.chatlist button{display:block;width:100%;text-align:left;border:1px solid var(--line);background:#fff;border-radius:10px;padding:8px 10px;margin-bottom:6px;cursor:pointer;font-size:13px}
.chatlist button.sel{background:var(--soft);border-color:var(--acc)}
.chatlist button small{color:var(--mut);display:block;font-size:11px}
.btn{border:1px solid var(--acc);background:var(--acc);color:#fff;border-radius:999px;padding:9px 16px;cursor:pointer;font-size:14px}
.btn.ghost{background:#fff;color:var(--acc)}
.btn.small{padding:5px 11px;font-size:12.5px}
.btn:disabled{opacity:.5;cursor:wait}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
select,input[type=text],textarea{border:1px solid var(--line);border-radius:10px;padding:9px 10px;font-size:14px;font-family:inherit;background:#fff}
textarea{width:100%;min-height:70px;resize:vertical}
.chathead{display:flex;gap:12px;align-items:center;border:1px solid var(--line);background:#fff;border-radius:14px;padding:12px}
.chathead .em{font-size:34px}
.chathead b{font-size:17px}
.chathead small{color:var(--mut);display:block;font-size:12.5px}
#mem{border:1px solid #d9c9a8;background:#fff8e6;border-radius:12px;padding:10px 12px;margin:12px 0}
#mem h3{margin:0 0 6px;font-size:13px}
#mem ul{margin:6px 0;padding-left:18px;font-size:13.5px}
#mem li{margin:3px 0}
#mem li button{border:none;background:none;cursor:pointer;font-size:12px;color:var(--acc)}
.fact-sug{background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:6px 8px;margin:4px 0;font-size:13px}
.fact-sug button{margin-left:6px}
#msgs{margin:14px 0}
.msg{max-width:82%;padding:10px 13px;border-radius:14px;margin:9px 0;line-height:1.55;font-size:15px;white-space:pre-wrap;word-wrap:break-word}
.msg.user{margin-left:auto;background:#e8e0d2;border-bottom-right-radius:4px}
.msg.char{background:#fff;border:1px solid var(--line);border-bottom-left-radius:4px}
.msg .tools{margin-top:6px;display:flex;gap:6px}
.msg .tools button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:3px 9px;font-size:11.5px;cursor:pointer}
.msg.sys{max-width:100%;background:none;color:var(--mut);font-size:12.5px;text-align:center;padding:2px}
#composer{display:flex;gap:8px;margin-top:10px}
#composer input{flex:1}
#status{font-size:13px;color:var(--mut);min-height:18px;margin-top:6px}
.limits{border-top:1px solid var(--line);margin-top:26px;padding-top:12px;font-size:13px;color:var(--mut);line-height:1.6}
.limits b{color:var(--ink)}
#createForm{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fff;margin-top:10px}
#createForm label{font-size:12.5px;color:var(--mut);display:block;margin:8px 0 3px}
#createForm input,#createForm textarea,#createForm select{width:100%}
.hidden{display:none}
@media(max-width:760px){.wrap{grid-template-columns:1fr}aside{border-right:none;border-bottom:1px solid var(--line)}.msg{max-width:94%}}
</style>
</head>
<body>
<header>
  <div><h1>Kirdar <span>کردار</span></h1>
  <p>Free AI character chat — no ads, no credits, no account. Urdu-first.</p></div>
  <div class="row"><span class="badge" id="aiBadge">AI status…</span></div>
</header>
<div class="wrap">
  <aside>
    <h2>Kirdar chunein</h2>
    <div class="char-grid" id="charGrid"></div>
    <button class="btn ghost small" id="newCharBtn" style="margin-top:10px">+ Apna kirdar banao</button>
    <div id="createForm" class="hidden">
      <label>Naam (2–40 harf)</label><input type="text" id="fName" maxlength="40" placeholder="e.g. Ustaad Bilal">
      <label>Role (2–80 harf)</label><input type="text" id="fRole" maxlength="80" placeholder="e.g. Maths tutor">
      <label>Personality (kam se kam 10 harf)</label><textarea id="fPers" placeholder="Kaisa bolta hai, kya janta hai, kis lehje mein…"></textarea>
      <label>Pehla message (greeting)</label><textarea id="fGreet" placeholder="Assalam-o-Alaikum! Main…"></textarea>
      <label>Emoji</label><input type="text" id="fEmoji" maxlength="4" value="🎭">
      <label>Language</label>
      <select id="fLang"><option value="roman">Roman-Urdu</option><option value="en">English</option><option value="ur">Urdu script</option></select>
      <div class="row" style="margin-top:10px">
        <button class="btn small" id="createSave">Save aur chat shuru karo</button>
        <button class="btn ghost small" id="createCancel">Cancel</button>
      </div>
      <p id="createErr" style="color:#b91c1c;font-size:13px"></p>
      <p style="font-size:12px;color:var(--mut)">Rule: asli shakhsiyat (mashhoor insaan) ki naqal nahi banti — sirf original kirdar.</p>
    </div>
    <h2>Meri chats</h2>
    <div class="chatlist" id="chatList"></div>
    <div class="row" style="margin-top:8px">
      <button class="btn ghost small" id="exportBtn">Export chat</button>
      <button class="btn ghost small" id="importBtn">Import chat</button>
      <input type="file" id="importFile" accept=".json" class="hidden">
    </div>
  </aside>
  <main>
    <div id="chatView">
      <div class="chathead"><span class="em" id="chEmoji">🎭</span>
        <div><b id="chName">Kirdar chunein</b><small id="chRole"></small></div>
        <span style="flex:1"></span>
        <label style="font-size:12.5px;color:var(--mut)">Language
          <select id="langSel"><option value="en">English</option><option value="roman">Roman-Urdu</option><option value="ur">Urdu</option></select>
        </label>
        <button class="btn ghost small" id="newChatBtn">Nayi chat</button>
      </div>
      <div id="mem"></div>
      <div id="msgs"></div>
      <div id="composer">
        <input type="text" id="msgInput" placeholder="Yahan likhein…" maxlength="2000">
        <button class="btn" id="sendBtn">Bhejo</button>
      </div>
      <div class="row" style="margin-top:8px">
        <button class="btn ghost small" id="regenBtn">↻ Dobara jawab</button>
        <button class="btn ghost small" id="speakAllBtn">🔊 Poori baat-cheet suno</button>
        <button class="btn ghost small" id="delChatBtn" style="color:#b91c1c;border-color:#f0c4c4">Chat delete karo</button>
      </div>
      <p id="status"></p>
    </div>
    <div class="limits">
      <b>Honest limits:</b> AI replies ke liye <b>GEMINI_API_KEY</b> chahiye (owner's free quota). Bina key ke roster, memory card, demo chat aur export/import phir bhi kaam karte hain.
      Kirdar ke kirdar AI hain — asli insaan nahi, aur kabhi asli insaan hone ka dawa nahi karte.
      <b>Dr. Sana</b> sirf aam maloomat deti hain — diagnosis ya dawa kabhi nahi; alamat ho to doctor ko dikhayein.
      Sirf wholesome baat-cheet: no romance, no sexual content. Agar koi khud ko nuqsan ki baat kare to hum pyaar se kehte hain ke kisi bharosemand shakhs ya professional se baat karein.
      AI kabhi kabhi bhool sakta hai ya repeat kar sakta hai — is liye memory card aap ke samne hai; koi fact ghalat ho to ek tap mein delete kar dein.
      Lambhi chats ka summary AI banata hai — pinned facts kabhi summary mein nahi gumm hote.
    </div>
  </main>
</div>
<script>
const LS="kirdar-v1";
let BUILTINS=[];
let state={chats:[],customs:[],activeId:null,summarizedUpTo:{}};
let AI=false;

function load(){try{const s=JSON.parse(localStorage.getItem(LS));if(s&&s.chats){state=s;}}catch(e){}}
function save(){localStorage.setItem(LS,JSON.stringify(state));}
function esc(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function uid(){return "c"+Date.now().toString(36)+Math.floor(Math.random()*1e4);}
function charById(id){return BUILTINS.find(c=>c.id===id)||state.customs.find(c=>c.id===id);}
function activeChat(){return state.chats.find(c=>c.id===state.activeId);}
function speak(text){try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);const v=speechSynthesis.getVoices().find(v=>v.lang&&v.lang.toLowerCase().startsWith("ur"))||speechSynthesis.getVoices().find(v=>v.lang&&v.lang.startsWith("en"));if(v)u.voice=v;speechSynthesis.speak(u);}catch(e){}}

async function api(path,body){
  const r=await fetch("/kirdar/api/"+path,{method:body?"POST":"GET",headers:{"Content-Type":"application/json"},body:body?JSON.stringify(body):undefined});
  return r.json();
}

function renderChars(){
  const g=document.getElementById("charGrid");g.innerHTML="";
  [...BUILTINS,...state.customs].forEach(c=>{
    const d=document.createElement("button");d.className="char";
    d.innerHTML=`<span class="em">${esc(c.emoji||"🎭")}</span><b>${esc(c.name)}</b><small>${esc(c.role)} — ${esc(c.tagline||"")}</small>`;
    d.onclick=()=>startChat(c.id);
    g.appendChild(d);
  });
}
function renderChatList(){
  const el=document.getElementById("chatList");el.innerHTML="";
  state.chats.forEach(ch=>{
    const c=charById(ch.character_id);if(!c)return;
    const b=document.createElement("button");if(ch.id===state.activeId)b.className="sel";
    b.innerHTML=`<b>${esc(ch.title)}</b><small>${esc(c.emoji||"")} ${esc(c.name)} · ${ch.messages.length} messages</small>`;
    b.onclick=()=>{state.activeId=ch.id;save();renderAll();};
    el.appendChild(b);
  });
  if(!state.chats.length)el.innerHTML="<p style='font-size:13px;color:var(--mut)'>Abhi koi chat nahi — upar se kirdar chunein.</p>";
}
function renderMem(){
  const ch=activeChat();const el=document.getElementById("mem");
  if(!ch){el.innerHTML="";return;}
  const c=charById(ch.character_id);
  let h=`<h3>🧠 ${esc(c?c.name:"")} ko kya yaad hai? <span style="font-weight:400;color:var(--mut)">(memory card — aap dekh, edit aur delete kar sakte hain)</span></h3>`;
  if(ch.summary)h+=`<p style="font-size:13px;margin:4px 0"><b>Pehli baaton ka summary:</b> ${esc(ch.summary)}</p>`;
  if(ch.memory_card&&ch.memory_card.length){
    h+="<ul>"+ch.memory_card.map((f,i)=>`<li>${f.pinned?"📌 ":""}${esc(f.fact)} <button data-act="pin" data-i="${i}">${f.pinned?"unpin":"pin"}</button> <button data-act="del" data-i="${i}">✕</button></li>`).join("")+"</ul>";
  }else h+="<p style='font-size:13px;color:var(--mut)'>Abhi kuch yaad nahi — baat-cheet se facts yahan aayenge.</p>";
  if(ch.pending&&ch.pending.length){
    h+="<p style='font-size:13px'><b>AI ne ye yaad rakhne ko kaha:</b></p>"+ch.pending.map((f,i)=>`<div class="fact-sug">${esc(f)} <button data-act="accept" data-i="${i}">Yaad rakho</button><button data-act="reject" data-i="${i}">Nahi</button></div>`).join("");
  }
  el.innerHTML=h;
  el.querySelectorAll("button").forEach(b=>b.onclick=()=>{
    const i=+b.dataset.i,act=b.dataset.act;
    if(act==="del")ch.memory_card.splice(i,1);
    if(act==="pin")ch.memory_card[i].pinned=!ch.memory_card[i].pinned;
    if(act==="accept"){ch.memory_card=addFacts(ch.memory_card,[ch.pending[i]]);ch.pending.splice(i,1);}
    if(act==="reject")ch.pending.splice(i,1);
    save();renderMem();
  });
}
function addFacts(card,facts){
  const seen=new Set(card.map(f=>f.fact.toLowerCase()));
  facts.forEach(f=>{if(f&&f.length<=120&&!seen.has(f.toLowerCase())){seen.add(f.toLowerCase());card.push({fact:f,pinned:false});}});
  while(card.length>20){const i=card.findIndex(f=>!f.pinned);card.splice(i<0?0:i,1);}
  return card;
}
function renderMsgs(){
  const ch=activeChat();const el=document.getElementById("msgs");
  if(!ch){el.innerHTML="<p style='color:var(--mut)'>Kirdar chunein ya apna banayein — phir baat-cheet yahan hogi.</p>";return;}
  const c=charById(ch.character_id);
  let h="";
  ch.messages.forEach((m,i)=>{
    if(m.role==="user")h+=`<div class="msg user" dir="auto">${esc(m.text)}</div>`;
    else h+=`<div class="msg char" dir="auto">${esc(m.text)}<div class="tools"><button data-say="${i}">🔊 Suno</button><button data-del="${i}">Delete</button></div></div>`;
  });
  el.innerHTML=h;
  el.querySelectorAll("[data-say]").forEach(b=>b.onclick=()=>speak(ch.messages[+b.dataset.say].text));
  el.querySelectorAll("[data-del]").forEach(b=>b.onclick=()=>{ch.messages.splice(+b.dataset.del,1);save();renderAll();});
  document.getElementById("chEmoji").textContent=c?c.emoji:"🎭";
  document.getElementById("chName").textContent=c?c.name:"";
  document.getElementById("chRole").textContent=c?c.role:"";
  document.getElementById("langSel").value=ch.language||(c?c.language:"roman");
  el.scrollTop=el.scrollHeight;
}
function renderAll(){renderChars();renderChatList();renderMem();renderMsgs();}

function startChat(charId){
  const c=charById(charId);if(!c)return;
  const ch={id:uid(),character_id:charId,title:c.name+" se baat",language:c.language||"roman",
    messages:c.greeting?[{role:"character",text:c.greeting}]:[],memory_card:[],summary:"",pending:[]};
  state.chats.unshift(ch);state.activeId=ch.id;state.summarizedUpTo[ch.id]=0;save();renderAll();
  document.getElementById("msgInput").focus();
}
async function maybeSummarize(ch){
  const upto=state.summarizedUpTo[ch.id]||0;
  if(ch.messages.length-upto<=14)return;
  const old=ch.messages.slice(upto,ch.messages.length-10);
  if(!old.length)return;
  const c=charById(ch.character_id);
  const res=await api("summarize",{character:c,turns:old,language:ch.language});
  if(res.ok){ch.summary=(ch.summary?ch.summary+" ":"")+res.summary;state.summarizedUpTo[ch.id]=ch.messages.length-10;save();}
}
async function send(text,regen){
  const ch=activeChat();if(!ch)return;
  const c=charById(ch.character_id);if(!c)return;
  const status=document.getElementById("status");
  if(!AI){status.textContent="AI key set nahi hai — chat ke liye GEMINI_API_KEY chahiye (owner's quota).";return;}
  if(!regen){
    if(!text.trim())return;
    ch.messages.push({role:"user",text:text.trim()});
    if(ch.messages.filter(m=>m.role==="user").length===1)ch.title=ch.messages.find(m=>m.role==="user").text.split(" ").slice(0,6).join(" ").slice(0,60);
    document.getElementById("msgInput").value="";
  }else{
    const lastUser=[...ch.messages].reverse().find(m=>m.role==="user");
    if(!lastUser){status.textContent="Dobara jawab ke liye pehle kuch likhein.";return;}
    const idx=ch.messages.lastIndexOf(lastUser);
    ch.messages=ch.messages.slice(0,idx+1);
  }
  save();renderAll();
  status.textContent=c.name+" likh raha hai…";
  document.getElementById("sendBtn").disabled=true;
  const res=await api("chat",{character:c,memory_card:ch.memory_card,summary:ch.summary,
    history:ch.messages,language:ch.language,
    message:ch.messages.filter(m=>m.role==="user").slice(-1)[0].text});
  document.getElementById("sendBtn").disabled=false;
  if(!res.ok){status.textContent="Error: "+(res.error||"kuch ghalat hua");return;}
  ch.messages.push({role:"character",text:res.result.reply});
  ch.pending=(res.result.remember||[]);
  status.textContent="";
  save();renderAll();
  await maybeSummarize(ch);save();renderAll();
}

document.getElementById("sendBtn").onclick=()=>send(document.getElementById("msgInput").value,false);
document.getElementById("msgInput").addEventListener("keydown",e=>{if(e.key==="Enter")send(e.target.value,false);});
document.getElementById("regenBtn").onclick=()=>send("",true);
document.getElementById("speakAllBtn").onclick=()=>{const ch=activeChat();if(ch)speak(ch.messages.map(m=>m.text).join(" "));};
document.getElementById("newChatBtn").onclick=()=>{const ch=activeChat();if(ch)startChat(ch.character_id);};
document.getElementById("delChatBtn").onclick=()=>{const ch=activeChat();if(!ch)return;if(!confirm("Ye chat delete kar dein?"))return;state.chats=state.chats.filter(x=>x.id!==ch.id);state.activeId=state.chats[0]?state.chats[0].id:null;save();renderAll();};
document.getElementById("langSel").onchange=e=>{const ch=activeChat();if(ch){ch.language=e.target.value;save();}};
document.getElementById("newCharBtn").onclick=()=>document.getElementById("createForm").classList.toggle("hidden");
document.getElementById("createCancel").onclick=()=>document.getElementById("createForm").classList.add("hidden");
document.getElementById("createSave").onclick=async()=>{
  const body={character:{name:document.getElementById("fName").value,role:document.getElementById("fRole").value,
    personality:document.getElementById("fPers").value,greeting:document.getElementById("fGreet").value,
    emoji:document.getElementById("fEmoji").value,language:document.getElementById("fLang").value,category:"custom"}};
  const res=await api("validate-character",body);
  if(!res.ok){document.getElementById("createErr").textContent=res.error;return;}
  state.customs.push(res.character);
  document.getElementById("createForm").classList.add("hidden");
  document.getElementById("createErr").textContent="";
  save();startChat(res.character.id);
};
document.getElementById("exportBtn").onclick=async()=>{
  const ch=activeChat();if(!ch)return;
  const res=await fetch("/kirdar/api/export-chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({chat:{app:"kirdar",version:1,title:ch.title,character:charById(ch.character_id),language:ch.language,messages:ch.messages,memory_card:ch.memory_card,summary:ch.summary}})});
  const blob=await res.blob();const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="kirdar-chat.json";a.click();
};
document.getElementById("importBtn").onclick=()=>document.getElementById("importFile").click();
document.getElementById("importFile").onchange=async e=>{
  const f=e.target.files[0];if(!f)return;
  const text=await f.text();
  const res=await api("import-chat",{json:text});
  if(!res.ok){document.getElementById("status").textContent="Import error: "+res.error;return;}
  const ch=res.chat;ch.id=uid();ch.pending=[];
  if(ch.character&&ch.character.id&&!charById(ch.character.id)&&ch.character.id.startsWith("custom-"))state.customs.push(ch.character);
  if(ch.character&&ch.character.id)ch.character_id=ch.character.id;
  state.chats.unshift(ch);state.activeId=ch.id;save();renderAll();
  document.getElementById("status").textContent="Chat import ho gayi: "+ch.title;
};

(async()=>{
  load();
  try{const r=await api("ai-status");AI=!!r.ai_available;
    document.getElementById("aiBadge").textContent=AI?"● AI ready":"○ AI key nahi hai — demo mode";
    document.getElementById("aiBadge").classList.toggle("ok",AI);}catch(e){}
  try{const r=await api("characters");if(r.ok)BUILTINS=r.characters;}catch(e){}
  if(!state.chats.length){
    try{const r=await api("demo");if(r.ok){const d=r.chat;const ch={id:uid(),character_id:d.character_id,title:d.title,language:d.language,messages:d.messages,memory_card:d.memory_card,summary:d.summary||"",pending:[]};state.chats.push(ch);state.activeId=ch.id;state.summarizedUpTo[ch.id]=0;save();}}catch(e){}
  }
  renderAll();
})();
</script>
</body>
</html>'''
