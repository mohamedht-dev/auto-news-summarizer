(() => {
  const root = document.documentElement;
  const bookmarkKey = "tech-brief-saved";
  let installPrompt;

  const readBookmarks = () => {
    try {
      const value = JSON.parse(localStorage.getItem(bookmarkKey) || "[]");
      return new Set(Array.isArray(value) ? value.map(String) : []);
    } catch {
      return new Set();
    }
  };

  let bookmarks = readBookmarks();

  const persistBookmarks = () => {
    localStorage.setItem(bookmarkKey, JSON.stringify([...bookmarks]));
  };

  const refreshBookmarks = () => {
    document.querySelectorAll("[data-bookmark]").forEach((button) => {
      const saved = bookmarks.has(String(button.dataset.bookmark));
      button.classList.toggle("is-saved", saved);
      button.setAttribute("aria-pressed", String(saved));
      const icon = button.querySelector("[aria-hidden='true']");
      if (icon) icon.textContent = saved ? "♥" : "♡";
    });

    document.querySelectorAll("[data-saved-count]").forEach((counter) => {
      counter.textContent = bookmarks.size;
      counter.hidden = bookmarks.size === 0;
    });

    const savedCards = [...document.querySelectorAll("[data-saved-only]")];
    if (savedCards.length) {
      let visible = 0;
      savedCards.forEach((card) => {
        const saved = bookmarks.has(String(card.dataset.articleKey));
        card.hidden = !saved;
        if (saved) visible += 1;
      });
      const grid = document.querySelector("[data-saved-grid]");
      const empty = document.querySelector("[data-saved-empty]");
      const total = document.querySelector("[data-saved-total]");
      if (grid) grid.hidden = visible === 0;
      if (empty) empty.hidden = visible > 0;
      if (total) total.textContent = visible;
    }
  };

  const showToast = (message) => {
    const toast = document.querySelector("[data-toast]");
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    window.setTimeout(() => { toast.hidden = true; }, 2600);
  };

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

  document.querySelectorAll("[data-bookmark]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const articleId = String(button.dataset.bookmark);
      if (bookmarks.has(articleId)) bookmarks.delete(articleId);
      else bookmarks.add(articleId);
      persistBookmarks();
      refreshBookmarks();
    });
  });

  document.querySelector("[data-clear-saved]")?.addEventListener("click", () => {
    bookmarks = new Set();
    persistBookmarks();
    refreshBookmarks();
  });

  document.querySelector("[data-share]")?.addEventListener("click", async (event) => {
    const button = event.currentTarget;
    const shareData = { title: button.dataset.title, url: window.location.href };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
        showToast("تم نسخ رابط الخبر");
      }
    } catch (error) {
      if (error.name !== "AbortError") showToast("تعذرت المشاركة الآن");
    }
  });

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPrompt = event;
    const button = document.querySelector("[data-install-app]");
    if (button) button.hidden = false;
  });

  document.querySelector("[data-install-app]")?.addEventListener("click", async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    await installPrompt.userChoice;
    installPrompt = undefined;
  });

  window.addEventListener("appinstalled", () => {
    const button = document.querySelector("[data-install-app]");
    if (button) button.hidden = true;
    installPrompt = undefined;
  });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js"));
  }

  refreshBookmarks();

  window.setTimeout(() => document.querySelector(".flash")?.remove(), 6500);
})();
