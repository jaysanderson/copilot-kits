/* Language switcher - persists in localStorage, drives the ask widget's lang
   param and the voice endpoint. UI copy stays English (site chrome); only the
   assistant's question/answer/voice, and the concierge's own name, are
   language-matched.

   A single clean DROPDOWN is the one UI for switching the assistant's
   language everywhere it appears (chat widget, Home, Learn) - build it with
   MBLang.mountDropdown(), never a bespoke chip row per page, so there is
   exactly one switching pattern to get right instead of several to keep in
   sync.

   MBLang.onChange(cb) is the ONE canonical way for page code to react to a
   language switch - fires only after state is fully updated, so there is no
   listener-order race to get wrong. */
(function () {
  const LANGS = ["en", "ja", "ko", "zh", "fr"];
  const LANG_LABELS = { en: "English", ja: "日本語 Japanese", ko: "한국어 Korean", zh: "中文 Mandarin", fr: "Français" };
  // The concierge's own name, per language - "Sol" (from Bay-co, "sea and
  // sun") in English, a warm natural pet-style variant in each other
  // language rather than a literal transliteration.
  const CONCIERGE_NAMES = { en: "Sol", ja: "ソルちゃん", ko: "솔이", zh: "阳阳", fr: "Soleil" };

  const subscribers = [];

  function getLang() {
    const l = localStorage.getItem("mb_lang");
    return LANGS.includes(l) ? l : "en";
  }

  function getConciergeName(lang) {
    return CONCIERGE_NAMES[lang] || CONCIERGE_NAMES.en;
  }

  const dropdowns = [];

  function setLang(l) {
    if (!LANGS.includes(l)) return;
    localStorage.setItem("mb_lang", l);
    dropdowns.forEach((sel) => {
      if (sel.value !== l) sel.value = l;
    });
    subscribers.forEach((cb) => {
      try {
        cb(l);
      } catch (e) {
        console.error("MBLang subscriber error", e);
      }
    });
  }

  function onChange(cb) {
    subscribers.push(cb);
  }

  /* Mounts a <select> language dropdown into `container` (an existing
     element - its innerHTML is replaced) styled with `selectClass`. Returns
     nothing; wire everything through MBLang.getLang()/onChange(). */
  function mountDropdown(container, selectClass) {
    if (!container) return;
    const select = document.createElement("select");
    select.className = selectClass || "mb-lang-select";
    select.setAttribute("aria-label", "Choose a language");
    LANGS.forEach((l) => {
      const opt = document.createElement("option");
      opt.value = l;
      opt.textContent = LANG_LABELS[l];
      select.appendChild(opt);
    });
    select.value = getLang();
    select.addEventListener("change", () => setLang(select.value));
    dropdowns.push(select);
    container.innerHTML = "";
    container.appendChild(select);
  }

  window.MBLang = { getLang, setLang, onChange, mountDropdown, getConciergeName, LANGS, LANG_LABELS, CONCIERGE_NAMES };
})();
