"use strict";
(() => {
  const list = document.getElementById("publications-list");
  const cards = [...list.querySelectorAll(".pub-card")];
  const search = document.getElementById("pubSearch");
  const sort = document.getElementById("pubSort");
  const buttons = [...document.querySelectorAll("[data-filter]")];
  const count = document.getElementById("pubCount");
  const normalize = text => text.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const searchable = new Map(cards.map(card => [card, normalize(card.querySelector(".pub-body").textContent + " " + card.dataset.year)]));
  let kind = "all";

  function applyFilters() {
    const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    const ordered = [...cards].sort((a, b) => {
      if (sort.value === "title") return a.querySelector("h2").textContent.localeCompare(b.querySelector("h2").textContent);
      // Undated work stays after dated publications in either year ordering.
      const first = Number(a.dataset.year), second = Number(b.dataset.year);
      if (!first || !second) return (!first ? 1 : 0) - (!second ? 1 : 0);
      return sort.value === "oldest" ? first - second : second - first;
    });
    let visible = 0;
    const fragment = document.createDocumentFragment();
    for (const card of ordered) {
      const matches = (kind === "all" || card.dataset.kind === kind) && terms.every(term => searchable.get(card).includes(term));
      card.hidden = !matches;
      if (matches) visible++;
      fragment.append(card);
    }
    list.append(fragment);
    count.textContent = `${visible} of ${cards.length} works`;
    document.getElementById("noResults").hidden = visible !== 0;
  }
  search.addEventListener("input", applyFilters);
  sort.addEventListener("change", applyFilters);
  buttons.forEach(button => button.addEventListener("click", () => {
    kind = button.dataset.filter;
    buttons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    applyFilters();
  }));
  document.getElementById("resetSearch").addEventListener("click", () => {
    search.value = ""; sort.value = "newest"; kind = "all";
    buttons.forEach(item => item.setAttribute("aria-pressed", String(item.dataset.filter === "all")));
    applyFilters(); search.focus();
  });

  function manualCitation(card, button) {
    let panel = card.querySelector(".citation-panel");
    if (!panel) {
      panel = document.createElement("div"); panel.className = "citation-panel";
      const label = document.createElement("label"); label.htmlFor = `citation-${card.id}`;
      label.textContent = "Copy this citation (Ctrl+C on Windows, ⌘C on Mac):";
      const field = document.createElement("textarea"); field.id = label.htmlFor;
      field.readOnly = true; field.value = card.dataset.citation;
      const close = document.createElement("button"); close.type = "button"; close.textContent = "Close citation";
      close.addEventListener("click", () => { panel.remove(); button.focus(); });
      panel.append(label, field, close); card.append(panel);
    }
    const field = panel.querySelector("textarea"); field.focus(); field.select();
    document.getElementById("citationStatus").textContent = "Automatic copy is unavailable. The citation is selected for manual copying.";
  }
  list.addEventListener("click", async event => {
    const button = event.target.closest(".cite-btn");
    if (!button) return;
    const card = button.closest(".pub-card");
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(card.dataset.citation);
      button.textContent = "✓ Citation copied";
      document.getElementById("citationStatus").textContent = "Citation copied to clipboard.";
      window.setTimeout(() => { button.textContent = "Copy citation"; }, 2000);
    } catch { manualCitation(card, button); }
  });
  applyFilters();
  document.documentElement.classList.add("publications-enhanced");
})();
