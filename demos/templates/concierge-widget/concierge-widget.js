/* Persistent multilingual concierge - present on every page. Genuinely
   multi-turn (threaded as ARAG's own /ask context), grounded + inline-cited
   (B33) + an honest decline when the real content doesn't cover something.
   State persists in sessionStorage so a conversation survives navigating
   between pages within one visit. */
(function () {
  const HISTORY_KEY = "sp_chat_history";
  const OPEN_KEY = "sp_chat_open";
  const LANG_KEY = "sp_chat_lang";
  const MAX_HISTORY = 12;

  const LANGS = { en: "English", zh: "中文", vi: "Tiếng Việt", hi: "हिन्दी" };

  const STARTERS = {
    en: ["What visa do I need to study in Perth?", "How much does it cost to live here as a student?", "Can I work while I study?"],
    zh: ["在珀斯留学需要什么签证？", "作为学生在这里生活大概要多少钱？", "我可以边学习边打工吗？"],
    vi: ["Tôi cần visa gì để du học tại Perth?", "Chi phí sinh hoạt cho sinh viên ở đây khoảng bao nhiêu?", "Tôi có thể vừa học vừa làm không?"],
    hi: ["पर्थ में पढ़ने के लिए मुझे कौन सा वीज़ा चाहिए?", "यहाँ छात्र के तौर पर रहने का खर्च कितना है?", "क्या मैं पढ़ाई के साथ काम कर सकता हूँ?"],
  };

  const WELCOME = {
    en: "G'day! I'm the Studycity concierge - ask me anything about studying, living or working in Perth. I only ever answer from Studycity's own real information, and I'll say so plainly if I don't know something.",
    zh: "你好！我是Studycity的AI助手 - 关于在珀斯学习、生活或工作的任何问题都可以问我。我只会根据Studycity的真实信息回答，如果不知道，我会如实告诉你。",
    vi: "Xin chào! Tôi là trợ lý Studycity - hãy hỏi tôi bất cứ điều gì về việc học tập, sinh sống hoặc làm việc tại Perth. Tôi chỉ trả lời dựa trên thông tin thực tế của Studycity, và sẽ nói thẳng nếu tôi không biết.",
    hi: "नमस्ते! मैं Studycity का सहायक हूँ - पर्थ में पढ़ाई, रहने या काम करने के बारे में कुछ भी पूछें। मैं केवल Studycity की असली जानकारी से जवाब देता हूँ, और अगर मुझे नहीं पता तो साफ़ बता दूँगा।",
  };

  function loadHistory() {
    try { return JSON.parse(sessionStorage.getItem(HISTORY_KEY) || "[]"); } catch (e) { return []; }
  }
  function saveHistory(h) {
    try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(h.slice(-MAX_HISTORY))); } catch (e) {}
  }
  function getLang() { return sessionStorage.getItem(LANG_KEY) || "en"; }
  function setLang(l) { try { sessionStorage.setItem(LANG_KEY, l); } catch (e) {} }

  let history = loadHistory();

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  const fab = el(`
    <button id="sp-chat-fab" class="sp-chat-fab" aria-label="Ask the Studycity concierge" type="button">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
    </button>
  `);
  const panel = el(`
    <div id="sp-chat-panel" class="sp-chat-panel" role="dialog" aria-label="Studycity concierge">
      <div class="sp-chat-head">
        <h4>Studycity Concierge</h4>
        <div style="display:flex;align-items:center;gap:8px;">
          <select class="sp-lang-select" id="sp-chat-lang">
            ${Object.entries(LANGS).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}
          </select>
          <button class="sp-chat-close" id="sp-chat-close" aria-label="Close">&times;</button>
        </div>
      </div>
      <div class="sp-chat-body" id="sp-chat-body"></div>
      <div class="sp-suggest-row" id="sp-chat-suggest"></div>
      <div class="sp-chat-input-row">
        <input id="sp-chat-input" placeholder="Ask about visas, fees, courses, life in Perth..." />
        <button class="sp-chat-send" id="sp-chat-send" aria-label="Send" type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
  `);
  document.body.appendChild(fab);
  document.body.appendChild(panel);

  function scrollBottom() {
    const b = document.getElementById("sp-chat-body");
    b.scrollTop = b.scrollHeight;
  }

  function renderStarters() {
    const wrap = document.getElementById("sp-chat-suggest");
    const q = STARTERS[getLang()] || STARTERS.en;
    wrap.innerHTML = q.map((s) => `<button class="sp-suggest-chip" type="button">${SPAnswer.escapeHtml(s)}</button>`).join("");
    wrap.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { document.getElementById("sp-chat-input").value = b.textContent; send(); }));
  }

  function renderHistory() {
    const body = document.getElementById("sp-chat-body");
    if (!history.length) {
      body.innerHTML = `<div class="sp-msg sp-msg-bot">${SPAnswer.escapeHtml(WELCOME[getLang()] || WELCOME.en)}</div>`;
      renderStarters();
      return;
    }
    document.getElementById("sp-chat-suggest").innerHTML = "";
    body.innerHTML = history.map((t, i) => {
      if (t.author === "USER") return `<div class="sp-msg sp-msg-user">${SPAnswer.escapeHtml(t.text)}</div>`;
      return `<div class="sp-msg sp-msg-bot" id="sp-msg-${i}">${SPAnswer.renderAnswer(t.text, t.citations)}${SPAnswer.renderCitationList(t.citations)}${SPAnswer.renderConfidenceBadge(t.confidence)}</div>`;
    }).join("");
    history.forEach((t, i) => { if (t.author !== "USER") { const elm = document.getElementById(`sp-msg-${i}`); if (elm) SPAnswer.wireCitationClicks(elm); } });
    scrollBottom();
  }

  async function send() {
    const input = document.getElementById("sp-chat-input");
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    const sendBtn = document.getElementById("sp-chat-send");
    sendBtn.disabled = true;
    history.push({ author: "USER", text: q });
    saveHistory(history);
    renderHistory();
    const body = document.getElementById("sp-chat-body");
    const typing = el(`<div class="sp-msg sp-msg-bot sp-typing"><span></span><span></span><span></span></div>`);
    body.appendChild(typing);
    scrollBottom();
    try {
      const prior = history.slice(0, -1).map((t) => ({ author: t.author, text: t.text }));
      const res = await fetch("/api/concierge", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, lang: getLang(), history: prior }),
      });
      const data = await res.json();
      typing.remove();
      history.push({ author: "NUCLIA", text: data.answer || "I couldn't form an answer to that - could you rephrase?", citations: data.citations || [], confidence: data.confidence || null });
      saveHistory(history);
      renderHistory();
    } catch (e) {
      typing.remove();
      history.push({ author: "NUCLIA", text: "Something went wrong on my end - please try again.", citations: [] });
      saveHistory(history);
      renderHistory();
    } finally {
      sendBtn.disabled = false;
    }
  }

  function setOpen(open) {
    panel.classList.toggle("sp-open", open);
    try { sessionStorage.setItem(OPEN_KEY, open ? "1" : "0"); } catch (e) {}
    if (open) { document.getElementById("sp-chat-input").focus(); scrollBottom(); }
  }

  fab.addEventListener("click", () => setOpen(!panel.classList.contains("sp-open")));
  document.getElementById("sp-chat-close").addEventListener("click", () => setOpen(false));
  document.getElementById("sp-chat-send").addEventListener("click", send);
  document.getElementById("sp-chat-input").addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });
  document.getElementById("sp-chat-lang").value = getLang();
  document.getElementById("sp-chat-lang").addEventListener("change", (e) => {
    setLang(e.target.value);
    history = [];
    saveHistory(history);
    renderHistory();
  });

  renderHistory();
  const onResourceViewer = window.location.pathname.startsWith("/r/");
  if (!onResourceViewer && sessionStorage.getItem(OPEN_KEY) === "1") setOpen(true);

  // Exposed so a page's own "ask a quick question" chips can open the widget
  // pre-filled rather than duplicating the ask call.
  window.SPConcierge = {
    open() { setOpen(true); },
    askInWidget(q) {
      setOpen(true);
      document.getElementById("sp-chat-input").value = q;
      send();
    },
  };
})();
