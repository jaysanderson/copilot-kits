/* The Wadjemup kiosk - a standing public screen and the same page on a
   phone. One JS file drives both contexts; the difference is a handful of
   context checks (isPhone), never a fork in the composition logic.

   Every screen (heading, cards, the next question) comes from one real
   retrieval + generation call per step - see POST /api/kiosk/next in app.py.
   This file never invents content; it only renders what that call returns
   and drives the loop (collect an answer, ask again, repeat, hand off).

   State model: `state.step` always equals the step used to produce the
   screen currently on display. Answering a question pushes {q, a} and
   increments step, then re-composes. Switching language re-composes the
   SAME step/answers with a new lang - it never restarts the plan. */
(function () {
  const $ = (id) => document.getElementById(id);

  function el(html) {
    const t = document.createElement("template");
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }

  function qp(name, dflt) {
    const v = new URLSearchParams(location.search).get(name);
    return v === null || v === "" ? dflt : v;
  }

  // ---------- network resilience -----------------------------------------
  // A bare `fetch()` with no timeout never REJECTS on a stalled connection -
  // the promise just never settles, so `catch` never fires and the caller
  // sits on its loading state forever (the exact failure this factory found
  // on a sibling build, Clinic, 29 Sep 2026 - about 1 call in 30 stalls
  // on an otherwise-healthy backend). Every fetch in this file goes through
  // this helper. Shape: a SHORT first attempt so a genuine stall fails fast,
  // then ONE longer retry so a merely-slow (not broken) backend still gets
  // served - never more than one retry, and never a fake progress bar while
  // waiting; callers say honestly that a retry is happening.
  //
  // A real 4xx/5xx is a resolved response, not a rejected promise - this
  // helper never sees it and never retries it (the caller's own `res.ok`
  // check decides what to do, per the standing rule: show a real error,
  // never retry a genuine server rejection). Only a stall (AbortError) or an
  // outright network failure (TypeError - offline, DNS, connection refused)
  // triggers the one retry.
  function fetchWithTimeout(url, options, timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    return fetch(url, Object.assign({}, options, { signal: controller.signal })).finally(() =>
      clearTimeout(timer)
    );
  }

  async function fetchResilient(url, options, cfg) {
    const shortMs = (cfg && cfg.shortMs) || 6000;
    const longMs = (cfg && cfg.longMs) || 20000;
    const onRetrying = cfg && cfg.onRetrying;
    try {
      return await fetchWithTimeout(url, options, shortMs);
    } catch (e) {
      if (e.name !== "AbortError" && !(e instanceof TypeError)) throw e;
      if (onRetrying) onRetrying();
      return await fetchWithTimeout(url, options, longMs);
    }
  }

  // ---------- context: kiosk vs phone ----------------------------------
  // A kiosk is a shared standing device that must forget you; a phone is a
  // personal one that should remember. mode= forces it either way (used by
  // the QR handoff, and handy for testing); otherwise infer it from the
  // hardware (Field Rule: real 390px mobile QA drives this path).
  const modeParam = qp("mode", "");
  const isPhone =
    modeParam === "phone" ||
    (modeParam !== "kiosk" &&
      window.matchMedia("(pointer: coarse)").matches &&
      window.innerWidth < 820);

  const LANGS = (window.RWLang && RWLang.LANGS) || ["en", "zh", "ja", "fr"];
  // Endonyms only, sized for a big tappable kiosk button - the fuller
  // "中文 Mandarin"-style labels in i18n.js are built for a compact dropdown,
  // not a large standing screen.
  const ENDONYMS = { en: "English", zh: "中文", ja: "日本語", fr: "Français" };

  // ---------- static UI copy, every language ------------------------------
  // Multilingual coverage gap found live, 30 Sep 2026 (independent-test
  // Blocker 2): the language switcher genuinely re-composes the generated
  // beat (heading/intro/cards - see _translate_card_copy in app.py for the
  // card half of that fix), but every FIXED piece of chrome around it -
  // button labels, error/retry wording, the handoff and payment panels, the
  // footer - stayed hardcoded English regardless of the selected language.
  // A UI that visibly offers 4 languages and silently leaves most of its own
  // surface untranslated is claiming a capability it doesn't perform (the
  // no-fake gate binds to UI chrome, not only to generated content). Static
  // strings only - the generated beat is handled server-side, in-language,
  // by the real /ask call, same discipline the rest of this build already
  // applies to real content vs UI chrome.
  const KIOSK_COPY = {
    en: {
      attractPulse: "Touch to start",
      localTime: "Local time",
      daylightLeftSuffix: "m of daylight left",
      sunset: "sunset",
      // The pill's other two regimes (class fix, 30 Sep 2026) - a real time,
      // never a "0m" countdown that has nothing left to count.
      sunriseAt: "Sunrise",
      sunsetWas: "Sunset",
      beforeSunriseFallback: "before sunrise",
      afterSunsetFallback: "after sunset",
      conciergeReady: (name) => `${name} is ready when you are`,
      howThisWorks: "How this works",
      headingPlaceholder: "Let's find your afternoon",
      introPlaceholder: "Answer a couple of questions and the island will put together what genuinely fits from where you are standing.",
      headingFallbackWithCards: "Here's what fits",
      headingFallbackNoCards: "Let's find another way",
      waitPhrases: [
        { at: 0, text: "Reading what's genuinely nearby..." },
        { at: 2200, text: "Working out what actually fits your afternoon..." },
        { at: 7000, text: "Nearly there..." },
      ],
      statusRetrying: "That's taking longer than usual - still trying...",
      waitPhoneOffer: "Start this on your phone instead",
      waitPhoneNote: "Scan to start this on your phone. This screen resets straight away - nothing about you is kept on it.",
      statusError: "Kwoka had trouble putting that together.",
      tryAgain: "Try again",
      contextUnavailable: "location details unavailable right now",
      contextRetrying: "still finding your location...",
      contextRetry: "try again",
      handTitleCards: "Take this with you",
      handTitleNoCards: "Ask at the Visitor Centre",
      handBody: "Scan to carry this same plan on your phone. Nothing about you is kept on this screen.",
      handoffEarlyTitle: "Prefer your phone?",
      handoffEarlyBody: "Scan to start this plan on your phone instead. Nothing about you is kept on this screen.",
      qrPreparing: "Preparing your QR code...",
      qrStillPreparing: "Still preparing...",
      qrUnavailable: "QR code unavailable right now -",
      qrRetry: "try again",
      qrUnavailableSuffix: ", or ask the Visitor Centre to help you continue on your phone.",
      payDefaultItemName: "Demo add-on",
      payRealLink: "Book the real ferry with the operator",
      simBar: "SIMULATED PAYMENT - DEMO ONLY, NOTHING IS CHARGED",
      simulatedDemoItemSuffix: "(simulated demo item)",
      payBtn: "Simulate purchase",
      payBtnDone: "Purchased (simulated)",
      paySimulating: "Simulating...",
      payStillSimulating: "Still simulating...",
      payResult: (ref) => `Simulated - reference ${ref}. No real payment was made.`,
      payFail: "The simulation didn't go through - nothing was charged either way. Try again.",
      bigText: "Larger text",
      contrast: "High contrast",
      listen: "Listen",
      stop: "Stop",
      listenLoading: "Loading...",
      listenStillLoading: "Still loading...",
      listenFail: "Couldn't play - tap to retry",
      reset: "Start again",
      footNote: "Synthetic demo build - content sourced from holidayisleisland.com",
      readOnSite: "Read this on the island's site",
      fitsDaylight: (m) => `Fits your daylight &middot; ${m} min`,
      tightDaylight: (m) => `Tight for daylight &middot; ${m} min`,
      stepFreeFriendly: "Step-free friendly",
      languageGroupLabel: "Language",
      // The header strap's connective, per language (defect (b), header-strap
      // audit, 30 Sep 2026). `near` already arrives from the server
      // pre-translated (KIOSK_NEAR_I18N in app.py) - English is the one
      // language that needs an explicit "near " prefix added here; Mandarin
      // and Japanese already end in their own word for "near"/"nearby", so
      // adding one here would say it twice (found live: "near 主码头和游客中心附近").
      // French needs its own prefix, in French, not the English word.
      nearLabel: (near) => `near ${near}`,
    },
    zh: {
      attractPulse: "点击开始",
      localTime: "当地时间",
      daylightLeftSuffix: "分钟日照剩余",
      sunset: "日落",
      sunriseAt: "日出",
      sunsetWas: "日落",
      beforeSunriseFallback: "日出之前",
      afterSunsetFallback: "日落之后",
      conciergeReady: (name) => `${name} 随时为您服务`,
      howThisWorks: "运作方式",
      headingPlaceholder: "为您寻找今天下午的安排",
      introPlaceholder: "回答几个简单的问题，岛上会根据您所在的位置为您安排真正合适的行程。",
      headingFallbackWithCards: "为您推荐",
      headingFallbackNoCards: "换个方式看看",
      waitPhrases: [
        { at: 0, text: "正在查看附近真实的内容..." },
        { at: 2200, text: "正在计算真正适合您下午的安排..." },
        { at: 7000, text: "马上就好..." },
      ],
      statusRetrying: "这次比平时慢一些，仍在努力中...",
      waitPhoneOffer: "改在您的手机上开始",
      waitPhoneNote: "扫码在您的手机上开始查看。本屏幕将立即重置 - 不会保留您的任何信息。",
      statusError: "Kwoka 在整理内容时遇到了问题。",
      tryAgain: "重试",
      contextUnavailable: "暂时无法获取位置信息",
      contextRetrying: "仍在查找您的位置...",
      contextRetry: "重试",
      handTitleCards: "带走这份行程",
      handTitleNoCards: "请咨询游客中心",
      handBody: "扫码在您的手机上继续查看这份行程。本屏幕不会保留您的任何信息。",
      handoffEarlyTitle: "更想用手机吗？",
      handoffEarlyBody: "扫码改在您的手机上开始这份行程。本屏幕不会保留您的任何信息。",
      qrPreparing: "正在生成二维码...",
      qrStillPreparing: "仍在生成中...",
      qrUnavailable: "二维码暂时无法生成 -",
      qrRetry: "重试",
      qrUnavailableSuffix: "，或请游客中心协助您在手机上继续。",
      payDefaultItemName: "演示附加项目",
      payRealLink: "向运营商预订真实渡轮",
      simBar: "模拟支付 - 仅供演示，不会产生任何实际扣款",
      simulatedDemoItemSuffix: "（模拟演示商品）",
      payBtn: "模拟购买",
      payBtnDone: "已购买（模拟）",
      paySimulating: "正在模拟...",
      payStillSimulating: "仍在模拟中...",
      payResult: (ref) => `模拟成功 - 参考编号 ${ref}。未产生任何实际付款。`,
      payFail: "模拟未完成 - 未产生任何扣款。请重试。",
      bigText: "放大文字",
      contrast: "高对比度",
      listen: "朗读",
      stop: "停止",
      listenLoading: "加载中...",
      listenStillLoading: "仍在加载...",
      listenFail: "播放失败 - 点击重试",
      reset: "重新开始",
      footNote: "本演示为虚构内容，素材来源于 holidayisleisland.com",
      readOnSite: "在官方网站上阅读",
      fitsDaylight: (m) => `符合剩余日照 &middot; ${m} 分钟`,
      tightDaylight: (m) => `日照时间较紧 &middot; ${m} 分钟`,
      stepFreeFriendly: "无障碍友好",
      languageGroupLabel: "语言",
      // No prefix needed - the server's own zh phrase already ends in 附近
      // ("nearby"); prepending anything here would say "near" twice.
      nearLabel: (near) => near,
    },
    ja: {
      attractPulse: "タップしてスタート",
      localTime: "現地時間",
      daylightLeftSuffix: "分の日照が残っています",
      sunset: "日没",
      sunriseAt: "日の出",
      sunsetWas: "日没",
      beforeSunriseFallback: "日の出前",
      afterSunsetFallback: "日没後",
      conciergeReady: (name) => `${name} がいつでもお待ちしています`,
      howThisWorks: "仕組みを見る",
      headingPlaceholder: "今日の午後のプランを探しましょう",
      introPlaceholder: "いくつかの質問に答えると、今いる場所から本当に合うプランを組み立てます。",
      headingFallbackWithCards: "こちらがおすすめです",
      headingFallbackNoCards: "別の方法を探しましょう",
      waitPhrases: [
        { at: 0, text: "近くの本当の情報を確認しています..." },
        { at: 2200, text: "午後にぴったりの内容を検討しています..." },
        { at: 7000, text: "もうすぐです..." },
      ],
      statusRetrying: "いつもより時間がかかっています - 引き続き試しています...",
      waitPhoneOffer: "スマートフォンで始める",
      waitPhoneNote: "スキャンしてスマートフォンで新しく始められます。この画面はすぐにリセットされます - お客様の情報は保存されません。",
      statusError: "Kwoka がうまくまとめられませんでした。",
      tryAgain: "もう一度試す",
      contextUnavailable: "現在、位置情報を取得できません",
      contextRetrying: "引き続き位置情報を確認しています...",
      contextRetry: "再試行",
      handTitleCards: "このプランを持ち帰る",
      handTitleNoCards: "ビジターセンターにお尋ねください",
      handBody: "スキャンしてスマートフォンで同じプランを引き続きご覧いただけます。この画面にはお客様の情報は保存されません。",
      handoffEarlyTitle: "スマートフォンの方がよければ",
      handoffEarlyBody: "スキャンしてスマートフォンでこのプランを新しく始められます。この画面にはお客様の情報は保存されません。",
      qrPreparing: "QRコードを準備しています...",
      qrStillPreparing: "引き続き準備中...",
      qrUnavailable: "現在QRコードを生成できません -",
      qrRetry: "再試行",
      qrUnavailableSuffix: "、またはビジターセンターでスマートフォンでの続行をお手伝いします。",
      payDefaultItemName: "デモ追加商品",
      payRealLink: "運営会社で本物のフェリーを予約する",
      simBar: "模擬決済 - デモ専用、実際の請求は発生しません",
      simulatedDemoItemSuffix: "（模擬デモ商品）",
      payBtn: "購入をシミュレート",
      payBtnDone: "購入済み（模擬）",
      paySimulating: "シミュレート中...",
      payStillSimulating: "引き続きシミュレート中...",
      payResult: (ref) => `模擬完了 - 参照番号 ${ref}。実際の支払いは発生していません。`,
      payFail: "シミュレーションが完了しませんでした - いずれにせよ請求は発生していません。もう一度お試しください。",
      bigText: "文字を大きく",
      contrast: "高コントラスト",
      listen: "読み上げ",
      stop: "停止",
      listenLoading: "読み込み中...",
      listenStillLoading: "引き続き読み込み中...",
      listenFail: "再生できませんでした - タップして再試行",
      reset: "最初からやり直す",
      footNote: "本デモは架空の内容です - 素材は holidayisleisland.com より取得",
      readOnSite: "島の公式サイトで読む",
      fitsDaylight: (m) => `残り日照時間に対応 &middot; ${m}分`,
      tightDaylight: (m) => `日照時間的にはやや厳しい &middot; ${m}分`,
      stepFreeFriendly: "段差なし対応",
      languageGroupLabel: "言語",
      // No prefix needed - the server's own ja phrase already ends in 近く
      // ("near"/"nearby"); prepending anything here would say it twice.
      nearLabel: (near) => near,
    },
    fr: {
      attractPulse: "Touchez pour commencer",
      localTime: "Heure locale",
      daylightLeftSuffix: " min de lumière du jour restante",
      sunset: "coucher du soleil",
      sunriseAt: "Lever du soleil",
      sunsetWas: "Coucher du soleil",
      beforeSunriseFallback: "avant le lever du soleil",
      afterSunsetFallback: "après le coucher du soleil",
      conciergeReady: (name) => `${name} est prêt à vous aider`,
      howThisWorks: "Comment ça marche",
      headingPlaceholder: "Trouvons votre après-midi",
      introPlaceholder: "Répondez à quelques questions et l'île composera un programme qui vous convient vraiment, là où vous vous trouvez.",
      headingFallbackWithCards: "Voici ce qui convient",
      headingFallbackNoCards: "Cherchons une autre approche",
      waitPhrases: [
        { at: 0, text: "Recherche de ce qui est vraiment à proximité..." },
        { at: 2200, text: "Détermination de ce qui convient vraiment à votre après-midi..." },
        { at: 7000, text: "Presque terminé..." },
      ],
      statusRetrying: "C'est plus long que d'habitude - nouvelle tentative en cours...",
      waitPhoneOffer: "Commencer sur votre téléphone à la place",
      waitPhoneNote: "Scannez pour commencer sur votre téléphone. Cet écran se réinitialise immédiatement - aucune information vous concernant n'y est conservée.",
      statusError: "Kwoka a eu du mal à préparer cela.",
      tryAgain: "Réessayer",
      contextUnavailable: "détails de localisation indisponibles pour le moment",
      contextRetrying: "recherche de votre position toujours en cours...",
      contextRetry: "réessayer",
      handTitleCards: "Emportez ceci avec vous",
      handTitleNoCards: "Demandez à l'Office de tourisme",
      handBody: "Scannez pour continuer ce même programme sur votre téléphone. Aucune information vous concernant n'est conservée sur cet écran.",
      handoffEarlyTitle: "Vous préférez votre téléphone ?",
      handoffEarlyBody: "Scannez pour commencer ce programme sur votre téléphone à la place. Aucune information vous concernant n'est conservée sur cet écran.",
      qrPreparing: "Préparation de votre QR code...",
      qrStillPreparing: "Toujours en préparation...",
      qrUnavailable: "QR code indisponible pour le moment -",
      qrRetry: "réessayer",
      qrUnavailableSuffix: ", ou demandez à l'Office de tourisme de vous aider à continuer sur votre téléphone.",
      payDefaultItemName: "Article de démonstration",
      payRealLink: "Réserver le vrai ferry auprès de l'opérateur",
      simBar: "PAIEMENT SIMULÉ - DÉMONSTRATION UNIQUEMENT, AUCUN DÉBIT RÉEL",
      simulatedDemoItemSuffix: "(article de démonstration simulé)",
      payBtn: "Simuler l'achat",
      payBtnDone: "Acheté (simulé)",
      paySimulating: "Simulation en cours...",
      payStillSimulating: "Simulation toujours en cours...",
      payResult: (ref) => `Simulé - référence ${ref}. Aucun paiement réel n'a été effectué.`,
      payFail: "La simulation n'a pas abouti - aucun débit n'a été effectué. Réessayez.",
      bigText: "Texte plus grand",
      contrast: "Contraste élevé",
      listen: "Écouter",
      stop: "Arrêter",
      listenLoading: "Chargement...",
      listenStillLoading: "Chargement toujours en cours...",
      listenFail: "Échec de lecture - touchez pour réessayer",
      reset: "Recommencer",
      footNote: "Démonstration synthétique - contenu provenant de holidayisleisland.com",
      readOnSite: "Lire sur le site de l'île",
      fitsDaylight: (m) => `Convient à la lumière du jour restante &middot; ${m} min`,
      tightDaylight: (m) => `Un peu juste pour la lumière du jour &middot; ${m} min`,
      stepFreeFriendly: "Accessible sans marche",
      languageGroupLabel: "Langue",
      // The server's own fr phrase (e.g. "la jetée principale et l'Office de
      // tourisme") carries no built-in "near" equivalent, unlike zh/ja - so
      // French needs its own prefix, in French.
      nearLabel: (near) => `près de ${near}`,
    },
  };

  function t(key) {
    const dict = KIOSK_COPY[state.lang] || KIOSK_COPY.en;
    return key in dict ? dict[key] : KIOSK_COPY.en[key];
  }

  const SESSION_KEY = "rw_kiosk_phone_session"; // sessionStorage, phone only, never localStorage

  const state = {
    loc: qp("loc", "thomson-bay"),
    lang: qp("lang", "en"),
    answers: [], // [{q, a}]
    step: 0,
    ferryResourceId: null,
    simItem: null,
  };

  // ---------- idle / attract loop (kiosk only) ---------------------------
  const IDLE_MS = 90000;
  let idleTimer = null;

  function armIdleTimer() {
    if (isPhone) return; // phones keep their session; only the shared kiosk forgets you
    clearTimeout(idleTimer);
    idleTimer = setTimeout(showAttract, IDLE_MS);
  }

  function showAttract() {
    $("kAttract").classList.add("on");
    $("kAttract").setAttribute("aria-hidden", "false");
    stopListening();
    resetSession(true);
  }

  function hideAttractAndStart() {
    if (!$("kAttract").classList.contains("on")) return;
    $("kAttract").classList.remove("on");
    $("kAttract").setAttribute("aria-hidden", "true");
    armIdleTimer();
  }

  if (!isPhone) {
    ["pointerdown", "touchstart", "keydown"].forEach((evt) =>
      document.addEventListener(evt, () => {
        hideAttractAndStart();
        armIdleTimer();
      })
    );
    armIdleTimer();
  }

  // ---------- language bar ----------------------------------------------
  function renderLangBar() {
    const bar = $("kLangs");
    bar.innerHTML = "";
    bar.setAttribute("aria-label", t("languageGroupLabel"));
    LANGS.forEach((l) => {
      const btn = el(
        `<button type="button" class="k-lang" data-lang="${l}" aria-pressed="${l === state.lang}">${ENDONYMS[l] || l.toUpperCase()}</button>`
      );
      btn.addEventListener("click", () => onLanguageChange(l));
      bar.appendChild(btn);
    });
  }

  // Every static piece of chrome around the generated beat - button labels,
  // the footer, default/fallback copy - re-rendered in the current
  // language. Called on boot and on every language change; the generated
  // heading/intro/cards are handled separately, server-side, by the real
  // /ask call (see composeNext / _translate_card_copy).
  function applyStaticCopy() {
    $("kAttractPulse").textContent = t("attractPulse");
    if (window.RWLang) {
      $("kAttractSub").textContent = t("conciergeReady")(RWLang.getConciergeName(state.lang));
    }
    $("kRevealLabel").textContent = t("howThisWorks");
    // Real content overwrites this the moment composeNext() resolves - but
    // the static HTML placeholder is genuinely visible for a brief window
    // on first load (the first screen is usually cache-fast, not always),
    // so it must be in the current language too, not just the generated
    // heading/intro that follows it.
    if (!state.answers.length && !$("kCards").children.length) {
      $("kHead").textContent = t("headingPlaceholder");
      $("kIntro").textContent = t("introPlaceholder");
    }
    $("kBig").textContent = t("bigText");
    $("kCon").textContent = t("contrast");
    if (!listening) $("kListen").textContent = t("listen");
    $("kReset").textContent = t("reset");
    $("kFootNote").textContent = t("footNote");
    $("kPayRealLink").textContent = t("payRealLink");
    $("kSimBar").textContent = t("simBar");
    if (!$("kPayBtn").disabled) $("kPayBtn").textContent = t("payBtn");
  }

  async function onLanguageChange(l) {
    if (l === state.lang) return;
    state.lang = l;
    Array.from($("kLangs").children).forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.lang === l))
    );
    applyStaticCopy();
    if ($("kAttract").classList.contains("on")) return; // nothing composed yet
    // Header-strap fix, defect (a) (audit 30 Sep 2026): a language switch used
    // to re-compose the generated beat (heading/intro/cards) but never
    // re-fetched /api/kiosk/context, so the "near ..." strap - and the
    // translated sim-item name loadContext also paints - kept whatever
    // language the page loaded in. Run both in parallel; each already
    // handles its own failure without blocking the other.
    await Promise.all([loadContext(), composeNext()]);
  }

  // ---------- context (place + real computed daylight) -------------------
  async function loadContext() {
    try {
      const res = await fetchResilient(
        `/api/kiosk/context?loc=${encodeURIComponent(state.loc)}&lang=${encodeURIComponent(state.lang)}`,
        undefined,
        { onRetrying: () => ($("kNear").textContent = t("contextRetrying")) }
      );
      if (!res.ok) throw new Error("context failed");
      const ctx = await res.json();
      $("kPlace").textContent = ctx.location.label;
      // Header-strap fix, defect (b) (audit 30 Sep 2026): the connective used
      // to be a hardcoded English "near " prefixed onto an already-translated
      // phrase - correct in English, wrong everywhere else (zh/ja already end
      // in their own word for "near"/"nearby"; a bare prefix said it twice).
      // nearLabel() supplies each language's own correct construction.
      $("kNear").textContent = t("nearLabel")(ctx.location.near);
      paintDaylight(ctx.local_time, ctx.daylight_minutes, ctx.daylight_state, ctx.sunrise, ctx.sunset);
      state.ferryResourceId = ctx.ferry_resource_id;
      state.simItem = ctx.sim_item;
      if (state.simItem) {
        $("kPayItemName").textContent = state.simItem.name;
        $("kPayItemPrice").textContent = state.simItem.amount + " " + t("simulatedDemoItemSuffix");
      }
      if (state.ferryResourceId) {
        $("kPayRealLink").href = "/go/" + state.ferryResourceId;
      }
    } catch (e) {
      // Non-blocking (composeNext still runs the real, critical beat), but
      // never silent - a visitor should know this bit didn't load rather
      // than wondering why "near ..." is just missing. Real working retry,
      // not just a message: a click re-runs loadContext itself.
      $("kNear").innerHTML =
        `${t("contextUnavailable")} - <button type="button" class="k-inline-retry" id="kContextRetry">${t("contextRetry")}</button>`;
      const retryBtn = $("kContextRetry");
      if (retryBtn) retryBtn.addEventListener("click", loadContext);
    }
  }

  // Class fix (lead's gate, 30 Sep 2026): the pill was the THIRD surface to
  // independently get `mins == 0` wrong (after the model prompt and the
  // per-card chip) - it kept reading "0m of daylight left" after sunset,
  // a stuck-looking countdown under a heading that had already said the sun
  // had set. `mins` alone cannot tell "before dawn" from "after dusk" apart
  // - `daylight_state` (app.py's `_daylight_state`, the one place that
  // ambiguity is resolved) is now REQUIRED and switched on directly, so
  // this function can no longer render a regime it wasn't told about.
  function paintDaylight(localTime, mins, state, sunrise, sunset) {
    const light = $("kLight");
    if (mins == null || !state) {
      light.hidden = true;
      return;
    }
    let segment;
    if (state === "before_sunrise") {
      // Honest substitute for a countdown that doesn't exist yet - same
      // register as the BEFORE DAWN model prompt: speak about what's coming,
      // never a number counting up from zero.
      segment = sunrise
        ? `${t("sunriseAt")} <b>${sunrise}</b>`
        : `<b>${t("beforeSunriseFallback")}</b>`;
    } else if (state === "after_sunset") {
      // Mirror of the above - the day's daylight is a finished fact, not a
      // live figure, so state when it ended rather than repeating "0m".
      segment = sunset
        ? `${t("sunsetWas")} <b>${sunset}</b>`
        : `<b>${t("afterSunsetFallback")}</b>`;
    } else {
      const h = Math.floor(mins / 60);
      const m = mins % 60;
      const daylightStr = (h ? h + "h " : "") + m + t("daylightLeftSuffix");
      segment = `<b>${daylightStr}</b>${sunset ? " &middot; " + t("sunset") + " " + sunset : ""}`;
    }
    light.innerHTML = `<span>${t("localTime")} <b>${localTime}</b></span> &middot; <span>${segment}</span>`;
    light.hidden = false;
  }

  // ---------- the composition loop ---------------------------------------
  // A GENUINE first screen is served from a server-side cache (near-instant -
  // see the backend's _KIOSK_FIRST_SCREEN_CACHE), so this wait mostly shows
  // up on a real answered step, which always has to be a live call - nothing
  // about what a visitor is told after they've answered is ever served
  // stale. Measured live, 29 Sep 2026: retrieval reliably lands under 2s,
  // composition is the real 8-12s. These phrases narrate that REAL two-phase
  // pipeline in its real order and rough real timing - never a fabricated
  // percentage or a progress bar with no genuine progress behind it (the
  // no-fake gate binds here too: a percentage would claim a precision about
  // the remaining wait that nothing on this screen actually knows).
  let waitTimer = null;
  let waitPhoneTimer = null;
  // Bumped on every fresh composeNext() call AND on every reset - any
  // in-flight response whose captured generation no longer matches the
  // current one is stale and gets silently discarded rather than painted.
  // This is what makes the mid-wait phone handoff safe (an abandoned
  // attempt's late answer never lands on a public screen after the visitor
  // has said they're moving to their phone) and, as a side benefit, closes
  // the same class of bug for an ordinary idle-reset firing mid-request.
  let composeGeneration = 0;
  // Patience threshold for the mid-wait phone offer - independent of
  // fetchResilient's own short/long ladder below. Sized to when a STANDING
  // visitor would reasonably disengage, not to when the platform gives up;
  // per the lead's ruling, those are different moments and the offer has to
  // open at the first one, not only the second.
  const WAIT_PHONE_OFFER_MS = 22000;
  // How long the mid-wait QR stays up before this kiosk resets itself for
  // the next visitor - long enough to genuinely scan a code, short enough
  // that a stranger's in-progress question doesn't sit exposed on a shared
  // screen for anywhere near the length of the normal idle timeout.
  const WAIT_PHONE_RESET_MS = 15000;

  function hideWaitPhoneOffer() {
    $("kWaitPhone").classList.add("k-hidden");
    $("kWaitPhoneQrWrap").classList.add("k-hidden");
    $("kWaitPhoneQr").innerHTML = "";
  }

  function showWaitPhoneOffer(myGen) {
    if (myGen !== composeGeneration) return; // superseded - never resurrect a stale offer
    const btn = $("kWaitPhoneBtn");
    btn.disabled = false;
    btn.textContent = t("waitPhoneOffer");
    btn.onclick = () => handWaitOffToPhone(myGen);
    $("kWaitPhone").classList.remove("k-hidden");
    $("kWaitPhoneQrWrap").classList.add("k-hidden");
  }

  async function handWaitOffToPhone(myGen) {
    if (myGen !== composeGeneration) return;
    // The tap itself is the strongest signal this build can actually
    // observe that the visitor is moving to their own phone - a camera
    // reading the QR code generates no event here at all. Advancing the
    // generation counter now means this kiosk-side attempt's eventual
    // result (success or failure) is discarded on arrival, never painted.
    composeGeneration++;
    const btn = $("kWaitPhoneBtn");
    btn.disabled = true;
    try {
      // Carries the CURRENT step explicitly (never assumed) - a mid-wait
      // handoff is not necessarily a completed plan the way the done-state
      // QR always is. The phone starts a fresh request from this point; it
      // does not, and cannot, pick up the kiosk's own in-flight attempt.
      const resumePath =
        `/kiosk?loc=${encodeURIComponent(state.loc)}&lang=${encodeURIComponent(state.lang)}` +
        `&mode=phone&resume=${encodeURIComponent(JSON.stringify(state.answers))}&resumeStep=${state.step}`;
      const qrRes = await fetchResilient(
        `/api/kiosk/qr?path=${encodeURIComponent(resumePath)}&host=${encodeURIComponent(location.origin)}`
      );
      if (!qrRes.ok) throw new Error("qr failed");
      const qrData = await qrRes.json();
      $("kWaitPhoneQr").innerHTML = qrData.svg;
      $("kWaitPhoneNote").textContent = t("waitPhoneNote");
      $("kWaitPhoneQrWrap").classList.remove("k-hidden");
    } catch (e) {
      /* even the QR failed - fall straight through to the reset below rather
         than leave a broken, unusable offer standing on a public screen */
    }
    // Reset for the next visitor once there has been a genuine chance to
    // scan - never wait out the rest of the original idle window, which is
    // precisely the exposure gap this whole feature exists to close.
    setTimeout(() => resetSession(true), WAIT_PHONE_RESET_MS);
  }

  function setLoading(on) {
    $("kStatus").hidden = !on;
    if (waitTimer) {
      waitTimer.forEach((id) => clearTimeout(id));
      waitTimer = null;
    }
    if (waitPhoneTimer) {
      clearTimeout(waitPhoneTimer);
      waitPhoneTimer = null;
    }
    hideWaitPhoneOffer();
    if (!on) return;
    $("kStatus").classList.add("k-status-live");
    waitTimer = t("waitPhrases").map((p) =>
      setTimeout(() => {
        $("kStatus").textContent = p.text;
      }, p.at)
    );
  }

  function showError(retryFn) {
    setLoading(false);
    $("kStatus").classList.remove("k-status-live");
    $("kStatus").hidden = false;
    $("kStatus").innerHTML =
      `${t("statusError")} <button type="button" class="k-btn k-btn-ghost" id="kRetry" style="min-height:auto;padding:.35rem .9rem;margin-left:.5rem;">${t("tryAgain")}</button>`;
    $("kRetry").addEventListener("click", retryFn);
  }

  async function composeNext() {
    const myGen = ++composeGeneration;
    setLoading(true);
    $("kQ").classList.add("k-hidden");
    waitPhoneTimer = setTimeout(() => showWaitPhoneOffer(myGen), WAIT_PHONE_OFFER_MS);
    try {
      const res = await fetchResilient(
        "/api/kiosk/next",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            answers: state.answers,
            lang: state.lang,
            loc: state.loc,
            step: state.step,
          }),
        },
        {
          // Re-sized 30 Sep 2026 against real measured data (no interception):
          // /api/kiosk/next ran 9.0-14.6s across 7 organic samples, median
          // ~10s - so the short attempt now sits comfortably above the real
          // normal ceiling instead of firing on essentially every call (the
          // independent test's own finding on the previous 6s value: 9/9
          // organic requests triggered the retry message, making "taking
          // longer than usual" the normal experience rather than the honest
          // exception it's supposed to be). The long attempt covers the
          // platform's observed 36-81s spike regime with real margin - the
          // mid-wait offer above is what actually protects a standing
          // visitor's patience against a wait this long, not this ceiling.
          shortMs: 18000,
          longMs: 90000,
          // Honest wording during the one retry - never a fake progress
          // percentage (no-fake gate binds here: nothing on this screen
          // actually knows how much longer it will take).
          onRetrying: () => {
            if (myGen !== composeGeneration) return;
            if (waitTimer) waitTimer.forEach((id) => clearTimeout(id));
            $("kStatus").textContent = t("statusRetrying");
          },
        }
      );
      // Superseded by a newer request or a hand-off to phone - the visitor
      // has moved on, so this result (whatever it turns out to be) is never
      // painted. This is the same generation check that also protects an
      // ordinary idle-reset landing mid-request.
      if (myGen !== composeGeneration) return;
      if (!res.ok) throw new Error("composition failed");
      const data = await res.json();
      if (myGen !== composeGeneration) return;
      setLoading(false);
      $("kStatus").classList.remove("k-status-live");
      renderScreen(data);
      saveSessionIfPhone();
    } catch (e) {
      if (myGen !== composeGeneration) return;
      showError(composeNext);
    }
  }

  function renderScreen(data) {
    // renderScreen only ever runs once composeNext has already confirmed its
    // own generation is still current (see the `if (myGen !== composeGeneration)
    // return;` guards above), so composeGeneration itself IS that same current
    // generation at this point - captured here to guard the early handoff's
    // own async QR fetch below the same way the mid-wait offer is guarded.
    const myGen = composeGeneration;
    // state.step/state.answers already reflect the screen `data` represents
    // (answer() advances both BEFORE calling composeNext), so this correctly
    // turns the hero on only for a genuine first screen and off the instant
    // the visitor answers the first question, on every path (fresh visit,
    // phone-session restore, QR resume).
    applyFirstScreenHero();
    const hasCards = data.cards && data.cards.length;
    $("kHead").textContent = data.heading || (hasCards ? t("headingFallbackWithCards") : t("headingFallbackNoCards"));
    $("kIntro").textContent = data.intro || (hasCards ? "" : data.handoff || "");
    if (data.daylight_minutes != null) {
      // Previously hardcoded a `null` sunset here, so a composed screen's
      // pill never showed sunset time even in daytime mode - fixed as part
      // of the same pass that added daylight_state/sunrise/sunset to this
      // payload (app.py's _compose_kiosk_screen / _with_fresh_daylight).
      paintDaylight(data.local_time, data.daylight_minutes, data.daylight_state, data.sunrise, data.sunset);
    }
    renderCards(data.cards || []);

    if (data.done) {
      // The done state gets the fuller "take this with you" presentation
      // only (showHandoff below) - the compact persistent card steps aside
      // rather than showing twice.
      $("kQ").classList.add("k-hidden");
      hideHandoffEarly();
      showHandoff(data);
    } else {
      if (data.next_question) {
        renderQuestion(data.next_question);
        $("kHand").classList.add("k-hidden");
        $("kPay").classList.add("k-hidden");
      }
      // GM finding, 30 Sep 2026 (DAM 355f91cf32c84ff59083861155b4c89b): show
      // the compact phone-handoff door on every non-done screen, not only
      // the fourth one - it coexists with the question flow rather than
      // replacing it.
      showHandoffEarly(myGen);
    }
  }

  // ---------- persistent phone handoff (visible from the first screen) ---
  // GM finding, 30 Sep 2026 (DAM 355f91cf32c84ff59083861155b4c89b): the QR
  // that lets a visitor move to their phone previously existed only on the
  // done screen (showHandoff below) and behind the 22s mid-wait timer
  // (showWaitPhoneOffer above), so in ordinary fast use it was never visible
  // at all. This renders a compact, always-available door from the FIRST
  // composed screen onward. Same honesty rule as the mid-wait offer: the
  // phone starts a FRESH request from the current step/answers, so the copy
  // (handoffEarlyTitle/handoffEarlyBody) never says "continue" or "resume" -
  // it has to read correctly whether this is the first question or the
  // last, so it is written step-agnostic rather than claiming completion.
  function hideHandoffEarly() {
    $("kHandEarly").classList.add("k-hidden");
    $("kHandEarlyQr").innerHTML = "";
  }

  async function showHandoffEarly(myGen) {
    $("kHandEarlyTitle").textContent = t("handoffEarlyTitle");
    $("kHandEarlyBody").textContent = t("handoffEarlyBody");
    $("kHandEarly").classList.remove("k-hidden");
    const qrTarget = $("kHandEarlyQr");
    qrTarget.innerHTML = `<span class="k-qr-status">${t("qrPreparing")}</span>`;
    try {
      // Same resume-path shape as the done-state handoff (below), carrying
      // the CURRENT step/answers explicitly.
      const resumePath =
        `/kiosk?loc=${encodeURIComponent(state.loc)}&lang=${encodeURIComponent(state.lang)}` +
        `&mode=phone&resume=${encodeURIComponent(JSON.stringify(state.answers))}&resumeStep=${state.step}`;
      const qrRes = await fetchResilient(
        `/api/kiosk/qr?path=${encodeURIComponent(resumePath)}&host=${encodeURIComponent(location.origin)}`
      );
      // Superseded by a newer request, a reset, or a mid-wait hand-off to
      // phone while this fetch was in flight - never paint a stale code onto
      // whatever screen (or blank kiosk) is showing now.
      if (myGen !== composeGeneration) return;
      if (!qrRes.ok) throw new Error("qr failed");
      const qrData = await qrRes.json();
      if (myGen !== composeGeneration) return;
      qrTarget.innerHTML = qrData.svg;
    } catch (e) {
      if (myGen !== composeGeneration) return;
      qrTarget.innerHTML = `<span class="k-qr-status">${t("qrUnavailable")}</span>`;
    }
  }

  function renderCards(cards) {
    const wrap = $("kCards");
    wrap.innerHTML = "";
    const wantsStepFree = state.answers.some((a) => a.a === "Step-free / wheelchair");
    cards.forEach((c) => {
      // fits_daylight is null after sunset (server-side, app.py) - daylight
      // is no longer a real constraint once the sun has set, so there is
      // nothing honest to compare a card's duration against, and the chip
      // is omitted entirely rather than rendered as a comparison that can
      // only read "tight" (real defect found live by the lead's gate,
      // 19:30 local, 30 Sep 2026: every evening card read "Tight for
      // daylight" under a heading that had already said the sun had set).
      const daylightChip =
        c.fits_daylight == null
          ? ""
          : `<span class="k-chip ${c.fits_daylight ? "k-fits" : "k-tight"}">${
              c.fits_daylight ? t("fitsDaylight")(c.minutes) : t("tightDaylight")(c.minutes)
            }</span>`;
      const accessChip =
        wantsStepFree && c.step_free
          ? `<span class="k-chip k-access">${t("stepFreeFriendly")}</span>`
          : "";
      // Real imagery, structurally bound to the same resource_id this card's
      // own "read on site" link already carries (kiosk imagery build, 30 Sep
      // 2026) - never a model choice, never a hand-maintained title-to-image
      // map. `has_photo` is DECIDED SERVER-SIDE, at composition (app.py's
      // _resource_photo_bytes, the exact same check /api/thumbnail itself
      // enforces) - real defect found live by the lead's gate, 30 Sep 2026:
      // composition used to select cards without checking this, so the
      // client built an <img> for a resource the endpoint was always going
      // to refuse, logging a guaranteed 404 on every load. "Never make a
      // call that cannot succeed": no <img> element is emitted at all when
      // has_photo is false, so the browser never issues that request in
      // the first place - the honest text-only degrade, with zero wasted
      // round trips and zero console errors, not just a hidden broken image.
      const thumbImg = c.has_photo
        ? `<img class="k-thumb" src="/api/thumbnail/${c.resource_id}" alt="${c.title || ""}" loading="lazy" />`
        : "";
      const card = el(`
        <article class="k-card">
          ${thumbImg}
          <div class="k-card-body">
            <h3>${c.title || ""}</h3>
            <p class="k-why">${c.why || ""}</p>
            <div class="k-meta">
              ${daylightChip}
              ${accessChip}
            </div>
            <div class="k-acts">
              <a class="k-btn k-btn-primary" href="/go/${c.resource_id}" target="_blank" rel="noopener">${t("readOnSite")}</a>
            </div>
          </div>
        </article>
      `);
      wrap.appendChild(card);
    });
  }

  function renderQuestion(q) {
    $("kQPrompt").textContent = q.prompt;
    // The one code-guaranteed question (mobility/access) carries a stable
    // English `value` per option alongside its translated `label`, so the
    // wire value sent back to the server never changes with display
    // language (see _localized_mobility_question in app.py) - every other
    // question in the loop is freely model-generated and its options are
    // plain strings, already correctly localized. Handle both shapes.
    const promptValue = q.prompt_value || q.prompt;
    const opts = $("kOpts");
    opts.innerHTML = "";
    (q.options || []).forEach((opt) => {
      const isObj = opt && typeof opt === "object";
      const label = isObj ? opt.label : opt;
      const value = isObj ? opt.value : opt;
      const btn = el(`<button type="button" class="k-opt">${label}</button>`);
      btn.addEventListener("click", () => answer(promptValue, value));
      opts.appendChild(btn);
    });
    $("kQ").classList.remove("k-hidden");
  }

  async function answer(promptText, optionText) {
    state.answers.push({ q: promptText, a: optionText });
    state.step += 1;
    await composeNext();
  }

  // ---------- take it with you (QR handoff) -------------------------------
  let lastHandoffData = null;
  async function showHandoff(data) {
    lastHandoffData = data;
    const hasCards = data.cards && data.cards.length;
    $("kHand").classList.remove("k-hidden");
    $("kPay").classList.toggle("k-hidden", !hasCards);
    $("kHandTitle").textContent = hasCards ? t("handTitleCards") : t("handTitleNoCards");
    $("kHandBody").textContent = hasCards
      ? t("handBody")
      : data.handoff || t("handTitleNoCards");
    const qrTarget = $("kQr");
    qrTarget.innerHTML = `<span class="k-qr-status">${t("qrPreparing")}</span>`;
    try {
      const resumePath =
        `/kiosk?loc=${encodeURIComponent(state.loc)}&lang=${encodeURIComponent(state.lang)}` +
        `&mode=phone&resume=${encodeURIComponent(JSON.stringify(state.answers))}&resumeStep=${state.step}`;
      const qrRes = await fetchResilient(
        `/api/kiosk/qr?path=${encodeURIComponent(resumePath)}&host=${encodeURIComponent(location.origin)}`,
        undefined,
        { onRetrying: () => (qrTarget.innerHTML = `<span class="k-qr-status">${t("qrStillPreparing")}</span>`) }
      );
      if (!qrRes.ok) throw new Error("qr failed");
      const qrData = await qrRes.json();
      qrTarget.innerHTML = qrData.svg;
    } catch (e) {
      // Non-blocking (the handoff card's own text still stands), but visible
      // rather than a silently empty box where a QR code was expected - and
      // a real working retry, not just a workaround message.
      qrTarget.innerHTML =
        `<span class="k-qr-status">${t("qrUnavailable")} <button type="button" class="k-inline-retry" id="kQrRetry">${t("qrRetry")}</button>${t("qrUnavailableSuffix")}</span>`;
      const retryBtn = $("kQrRetry");
      if (retryBtn) retryBtn.addEventListener("click", () => showHandoff(lastHandoffData));
    }
  }

  // ---------- payment simulation ------------------------------------------
  $("kPayBtn").addEventListener("click", async () => {
    const btn = $("kPayBtn");
    btn.disabled = true;
    const resultEl = $("kPayResult");
    resultEl.hidden = false;
    resultEl.textContent = t("paySimulating");
    try {
      const res = await fetchResilient(
        "/api/kiosk/pay-sim",
        { method: "POST" },
        { onRetrying: () => (resultEl.textContent = t("payStillSimulating")) }
      );
      if (!res.ok) throw new Error("pay-sim failed");
      const data = await res.json();
      resultEl.textContent = t("payResult")(data.reference);
      btn.textContent = t("payBtnDone");
    } catch (e) {
      // Button re-enables itself - a live tap on it IS the retry path.
      resultEl.textContent = t("payFail");
      btn.disabled = false;
    }
  });

  // ---------- accessibility controls --------------------------------------
  function toggleBody(cls, btn) {
    const on = document.body.classList.toggle(cls);
    btn.setAttribute("aria-pressed", String(on));
    return on;
  }
  $("kBig").addEventListener("click", () => toggleBody("k-large", $("kBig")));
  $("kCon").addEventListener("click", () => toggleBody("k-contrast", $("kCon")));

  // Listen narrates the current screen through the real voice endpoint,
  // stopping cleanly on a second press.
  const kioskAudio = new Audio();
  let listening = false;
  function setListening(on) {
    listening = on;
    $("kListen").setAttribute("aria-pressed", String(on));
    $("kListen").textContent = on ? t("stop") : t("listen");
    if (!on) {
      kioskAudio.pause();
      kioskAudio.currentTime = 0;
    }
  }
  function stopListening() {
    if (listening) setListening(false);
  }
  kioskAudio.addEventListener("ended", () => setListening(false));

  function currentScreenText() {
    const parts = [$("kHead").textContent, $("kIntro").textContent];
    $("kCards")
      .querySelectorAll(".k-card")
      .forEach((c) => {
        const title = c.querySelector("h3");
        const why = c.querySelector(".k-why");
        if (title) parts.push(title.textContent);
        if (why) parts.push(why.textContent);
      });
    if (!$("kQ").classList.contains("k-hidden")) {
      parts.push($("kQPrompt").textContent);
    }
    return parts.filter(Boolean).join(". ");
  }

  $("kListen").addEventListener("click", async () => {
    if (listening) {
      setListening(false);
      return;
    }
    const text = currentScreenText();
    if (!text) return;
    const listenBtn = $("kListen");
    listenBtn.disabled = true;
    listenBtn.textContent = t("listenLoading");
    try {
      const vr = await fetchResilient(
        "/api/voice",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, lang: state.lang }),
        },
        { onRetrying: () => (listenBtn.textContent = t("listenStillLoading")) }
      );
      if (!vr.ok) throw new Error("voice failed");
      const blob = await vr.blob();
      kioskAudio.src = URL.createObjectURL(blob);
      listenBtn.disabled = false;
      setListening(true);
      await kioskAudio.play();
    } catch (e) {
      // Visible failure, not a silent revert to "Listen" (real defect found
      // by the independent tester's review - the old catch reset state with
      // no sign anything went wrong). Button re-enables immediately, so
      // tapping it again IS the working retry. setListening() writes its own
      // textContent, so it must run BEFORE the failure message is set, or it
      // would immediately overwrite it back to "Listen".
      setListening(false);
      listenBtn.disabled = false;
      listenBtn.textContent = t("listenFail");
      setTimeout(() => {
        if (!listening) listenBtn.textContent = t("listen");
      }, 3000);
    }
  });

  $("kReset").addEventListener("click", () => resetSession(false));

  function resetSession(toEnglish) {
    stopListening();
    state.answers = [];
    state.step = 0;
    // Every reset lands back on the first screen - apply its hero
    // immediately rather than waiting out the composeNext() call below,
    // same "clear it now, don't wait" discipline as the rest of this
    // function (kCards/kHand/handoff all clear synchronously here too).
    applyFirstScreenHero();
    if (toEnglish) {
      state.lang = "en";
      renderLangBar();
      applyStaticCopy();
    }
    $("kCards").innerHTML = "";
    $("kQ").classList.add("k-hidden");
    $("kHand").classList.add("k-hidden");
    // Clear the persistent handoff's QR/text BEFORE the async composeNext()
    // below resolves - otherwise a prior visitor's resume code would keep
    // rendering on this shared screen for the whole of that wait, which is
    // exactly the exposure window this reset exists to close.
    hideHandoffEarly();
    $("kPay").classList.add("k-hidden");
    $("kPayResult").hidden = true;
    $("kPayBtn").disabled = false;
    $("kPayBtn").textContent = t("payBtn");
    clearSessionIfPhone();
    if (!$("kAttract").classList.contains("on")) composeNext();
  }

  // ---------- phone session persistence (sessionStorage only) ------------
  function saveSessionIfPhone() {
    if (!isPhone) return;
    try {
      sessionStorage.setItem(
        SESSION_KEY,
        JSON.stringify({ answers: state.answers, step: state.step, lang: state.lang, loc: state.loc })
      );
    } catch (e) {
      /* ignore quota errors - the session simply won't survive a reload */
    }
  }
  function clearSessionIfPhone() {
    if (!isPhone) return;
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch (e) {
      /* ignore */
    }
  }
  function loadPhoneSession() {
    if (!isPhone) return null;
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  // ---------- the "how this works" reveal ---------------------------------
  // Fetched on demand only (never embedded in the page) - same discipline
  // shared.js uses on every other route, reimplemented here because the
  // kiosk deliberately doesn't load the standard site chrome.
  const revealOverlay = el(`
    <div class="arag-reveal-overlay" id="kRevealOverlay">
      <div class="arag-reveal-modal" id="kRevealModal"></div>
    </div>
  `);
  document.body.appendChild(revealOverlay);
  let revealBuilt = false;

  async function buildReveal() {
    const modal = $("kRevealModal");
    modal.innerHTML = '<div style="padding:40px;text-align:center;">Loading...</div>';
    let reveal;
    try {
      const res = await fetchResilient(
        "/api/reveal/kiosk",
        undefined,
        { onRetrying: () => (modal.innerHTML = '<div style="padding:40px;text-align:center;">Still loading...</div>') }
      );
      if (!res.ok) throw new Error("reveal failed");
      reveal = await res.json();
    } catch (e) {
      reveal = {
        title: "How this kiosk works",
        flow: [{ label: "Your answers" }, { label: "App proxy" }, { label: "Composed screen" }],
        what: "This kiosk is powered by Progress Agentic RAG underneath the Holidayisle Island Authority's own visitor experience.",
        why: "A genuinely personalised screen builds visitor trust in a way a fixed menu never can.",
      };
    }
    modal.innerHTML = `
      <div class="arag-reveal-head">
        <h2>${reveal.title}</h2>
        <button class="arag-reveal-close" id="kRevealClose" aria-label="Close">&#10005;</button>
      </div>
      <div class="arag-reveal-body">
        <div class="arag-reveal-section">
          <h3>What this screen does</h3>
          <p>${reveal.what}</p>
        </div>
        <div class="arag-reveal-section">
          <h3>The real technical flow</h3>
          <div class="arag-flow" id="kRevealFlow">
            ${reveal.flow
              .map(
                (s, i) => `
              ${i > 0 ? '<span class="arag-flow-arrow">&rarr;</span>' : ""}
              <div class="arag-flow-step" data-step="${i}">
                <div class="arag-flow-num">${i + 1}</div>
                <div><strong>${s.label}</strong></div>
                ${s.detail ? `<div style="margin-top:4px;opacity:0.75;">${s.detail}</div>` : ""}
              </div>`
              )
              .join("")}
          </div>
        </div>
        <div class="arag-reveal-section">
          <h3>Why it matters</h3>
          <p>${reveal.why}</p>
        </div>
        ${
          reveal.gaps
            ? `<div class="arag-reveal-section"><h3>Honest limits</h3><p>${reveal.gaps}</p><span class="arag-reveal-badge arag-badge-gap">Disclosed platform gap - not silently routed around</span></div>`
            : ""
        }
      </div>
    `;
    $("kRevealClose").addEventListener("click", () => revealOverlay.classList.remove("rw-open"));
  }

  async function openReveal() {
    revealOverlay.classList.add("rw-open");
    if (!revealBuilt) {
      await buildReveal();
      revealBuilt = true;
    }
  }
  $("kRevealBtn").addEventListener("click", openReveal);
  revealOverlay.addEventListener("click", (e) => {
    if (e.target === revealOverlay) revealOverlay.classList.remove("rw-open");
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") revealOverlay.classList.remove("rw-open");
  });

  // ---------- boot ----------------------------------------------------------
  // Real photography on the idle/attract screen (kiosk imagery build, 30 Sep
  // 2026) - a single fixed background, server-cropped and server-owned (see
  // ATTRACT_BACKGROUND_RESOURCE_ID + /api/kiosk/attract-background in
  // app.py), never regenerated per visitor and never re-fetched per language
  // change (unlike loadContext, it doesn't depend on lang/loc). The gradient
  // is layered in front of the photo purely for text legibility over
  // whatever the photo's own colours are - it adds no content, it only
  // darkens what is already there. Fire-and-forget: on failure the flat
  // `background-color` already on .k-attract is the honest fallback, so
  // nothing here needs a catch handler of its own.
  function setAttractBackground() {
    $("kAttract").style.backgroundImage =
      "linear-gradient(180deg, rgba(7,55,70,.45) 0%, rgba(7,55,70,.65) 55%, rgba(7,55,70,.85) 100%), " +
      "url(/api/kiosk/attract-background)";
  }

  // First-screen hero background (kiosk imagery build, 30 Sep 2026 - GM
  // decision via the lead's gate, after measuring 6 of 12 sampled first-
  // screen compositions landed zero image-bearing cards). FIRST SCREEN
  // ONLY: this is the one composition that depends on nothing the visitor
  // has told the kiosk yet, so it's a layout decision, not a retrieval
  // one - every later screen is personalised and its own cards carry the
  // imagery. Applied to <body> as a background (see the CSS comment on
  // .k-hero-first for why a background, never a new element, is what keeps
  // the card row's own top position provably unchanged), and re-evaluated
  // on every render so it turns itself off the moment the visitor answers
  // the first question and the screen stops being the first one.
  function applyFirstScreenHero() {
    const isFirstScreen = state.step === 0 && state.answers.length === 0;
    if (isFirstScreen) {
      // Scrim strength set by MEASUREMENT, not by eye (build report, 30 Sep
      // 2026): the first attempt (.55/.72/.92) measured 3.28-4.47:1 against
      // the actual worst (lightest) rendered pixel behind the text on all
      // four locations - passing for the heading only under WCAG's relaxed
      // "large text" 3:1 threshold, and failing the intro's real 4.5:1
      // requirement everywhere. Raised until every location's own worst
      // pixel cleared 4.5:1 for BOTH the heading and the smaller intro text.
      document.body.style.backgroundImage =
        "linear-gradient(180deg, rgba(7,55,70,.82) 0%, rgba(7,55,70,.90) 45%, rgba(7,55,70,.96) 100%), " +
        `url(/api/kiosk/hero-background?loc=${encodeURIComponent(state.loc)})`;
      document.body.classList.add("k-hero-first");
    } else {
      document.body.classList.remove("k-hero-first");
      document.body.style.backgroundImage = "";
    }
  }

  async function boot() {
    renderLangBar();
    applyStaticCopy();
    setAttractBackground();
    await loadContext();

    const resumeRaw = qp("resume", "");
    if (resumeRaw) {
      try {
        const answers = JSON.parse(resumeRaw);
        if (Array.isArray(answers) && answers.length) {
          state.answers = answers;
          // The step now always travels explicitly with the QR (a mid-wait
          // handoff is not necessarily a completed plan the way the
          // done-state QR always was) - default to 3 only for backward
          // compatibility with a code generated before this existed.
          const resumeStep = parseInt(qp("resumeStep", "3"), 10);
          state.step = Number.isFinite(resumeStep) ? resumeStep : 3;
          renderLangBar();
          applyStaticCopy();
          await composeNext();
          return;
        }
      } catch (e) {
        /* malformed resume payload - fall through to a fresh start */
      }
    }

    const saved = loadPhoneSession();
    if (saved && Array.isArray(saved.answers)) {
      state.answers = saved.answers;
      state.step = saved.step || 0;
      state.lang = saved.lang || state.lang;
      renderLangBar();
      applyStaticCopy();
      await composeNext();
      return;
    }

    await composeNext();
  }

  boot();
})();
