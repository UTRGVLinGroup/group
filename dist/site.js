"use strict";
document.documentElement.classList.add("js");
const menuButton = document.querySelector(".nav-toggle");
const navigation = document.getElementById("primary-links");
function closeMenu(restoreFocus = false) {
  navigation.classList.remove("is-open");
  menuButton.setAttribute("aria-expanded", "false");
  menuButton.textContent = "Menu +";
  if (restoreFocus) menuButton.focus();
}
menuButton.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") !== "true";
  menuButton.setAttribute("aria-expanded", String(open));
  menuButton.textContent = open ? "Close −" : "Menu +";
  navigation.classList.toggle("is-open", open);
});
document.addEventListener("keydown", event => {
  if (event.key !== "Escape") return;
  const resource = document.querySelector(".resource-menu[open]");
  if (resource) { resource.open = false; resource.querySelector("summary").focus(); }
  else if (navigation.classList.contains("is-open")) closeMenu(true);
});
document.addEventListener("click", event => {
  document.querySelectorAll(".resource-menu[open]").forEach(menu => {
    if (!menu.contains(event.target)) menu.open = false;
  });
  if (!event.target.closest(".navbar")) closeMenu();
});
window.matchMedia("(min-width: 821px)").addEventListener("change", () => closeMenu());
document.querySelectorAll(".footer [data-year]").forEach(el => el.textContent = new Date().getFullYear());
