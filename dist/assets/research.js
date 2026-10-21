"use strict";
(() => {
  if (!("HTMLDialogElement" in window) || !HTMLDialogElement.prototype.showModal) return;
  const models = JSON.parse(document.getElementById("molecule-data").textContent);
  const viewers = new Map();
  let libraryPromise;
  const loadLibrary = () => {
    if (window.$3Dmol) return Promise.resolve(window.$3Dmol);
    if (!libraryPromise) libraryPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "assets/vendor/3Dmol-2.0.4.min.js";
      const timeout = setTimeout(() => { script.remove(); reject(new Error("Viewer timed out")); }, 12000);
      script.onload = () => { clearTimeout(timeout); window.$3Dmol ? resolve(window.$3Dmol) : reject(new Error("Viewer unavailable")); };
      script.onerror = () => { clearTimeout(timeout); script.remove(); reject(new Error("Viewer unavailable")); };
      document.head.append(script);
    }).catch(error => { libraryPromise = undefined; throw error; });
    return libraryPromise;
  };
  const dialog = document.createElement("dialog"); dialog.className = "project-dialog";
  const close = document.createElement("button"); close.className = "close"; close.type = "button";
  close.setAttribute("aria-label", "Close project details"); close.textContent = "×"; dialog.append(close); document.body.append(dialog);
  let active, placeholder, trigger;
  close.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => {
    const rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
  });
  dialog.addEventListener("close", () => {
    document.body.classList.remove("no-scroll");
    active.classList.remove("in-dialog"); placeholder.replaceWith(active);
    trigger.focus(); active = null;
  });
  async function initialize(section) {
    const containers = [...section.querySelectorAll(".mol-container")];
    for (const container of containers) {
      if (viewers.has(container)) { viewers.get(container).resize(); viewers.get(container).render(); continue; }
      const status = container.querySelector(".model-status");
      status.textContent = "Loading molecular structure…";
      try {
        const library = await loadLibrary();
        if (!dialog.open || active !== section) return;
        const sdf = models[container.dataset.model];
        if (!sdf) throw new Error("Structure unavailable");
        const viewer = library.createViewer(container, { backgroundColor: "white" });
        viewer.addModel(sdf, "sdf");
        viewer.setStyle({}, {stick: {radius: 0.17, colorscheme: "Jmol"}, sphere: {scale: 0.25}});
        viewer.zoomTo(); viewer.render(); viewers.set(container, viewer); status.hidden = true;
        const controls = container.parentElement.querySelector(".viewer-controls"); controls.hidden = false;
        controls.addEventListener("click", event => {
          const action = event.target.closest("[data-view]")?.dataset.view;
          if (action === "left") viewer.rotate(-20, "y");
          if (action === "right") viewer.rotate(20, "y");
          if (action === "in") viewer.zoom(1.2);
          if (action === "out") viewer.zoom(0.8);
          if (action === "reset") { viewer.setView(initialView); }
          viewer.render();
        });
        const initialView = viewer.getView();
      } catch {
        container.querySelectorAll("canvas").forEach(canvas => canvas.remove());
        status.hidden = false;
        status.textContent = "The interactive viewer is unavailable in this browser. Use the research figure above, download the structure, or open its PubChem record below.";
      }
    }
  }
  document.querySelectorAll("[data-project]").forEach(link => link.addEventListener("click", event => {
    const section = document.getElementById(link.dataset.project);
    if (!section || dialog.open) return;
    event.preventDefault(); trigger = link; active = section;
    placeholder = document.createComment("Project details location"); section.replaceWith(placeholder);
    section.classList.add("in-dialog"); dialog.append(section);
    dialog.setAttribute("aria-labelledby", section.getAttribute("aria-labelledby"));
    dialog.showModal(); dialog.scrollTop = 0; document.body.classList.add("no-scroll"); close.focus();
    requestAnimationFrame(() => initialize(section));
  }));
  window.addEventListener("resize", () => {
    if (active) active.querySelectorAll(".mol-container").forEach(container => {
      const viewer = viewers.get(container); if (viewer) { viewer.resize(); viewer.render(); }
    });
  });
  document.documentElement.classList.add("research-enhanced");
  if (/^#modal[1-5]$/.test(location.hash)) document.querySelector(`[data-project="${location.hash.slice(1)}"]`)?.click();
})();
