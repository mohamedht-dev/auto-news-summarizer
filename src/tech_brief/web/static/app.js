(() => {
  const root = document.documentElement;
  const storedTheme = localStorage.getItem("tech-brief-theme");
  const preferredDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = storedTheme || (preferredDark ? "dark" : "light");

  document.querySelector("[data-theme-toggle]")?.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    localStorage.setItem("tech-brief-theme", next);
  });

  document.querySelectorAll("[data-language]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-language]").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll("[data-panel]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelector(`[data-panel="${button.dataset.language}"]`)?.classList.add("active");
    });
  });

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => button.closest(".flash")?.remove());
  });

  window.setTimeout(() => document.querySelector(".flash")?.remove(), 6500);
})();
