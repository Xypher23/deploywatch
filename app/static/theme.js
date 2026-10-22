const themeStorageKey = "deploywatch-theme";
const themes = ["system", "dark", "light"];

let currentTheme = "system";

try {
  const savedTheme = window.localStorage.getItem(themeStorageKey);
  if (themes.includes(savedTheme)) {
    currentTheme = savedTheme;
  }
} catch (error) {
  console.warn("Could not read the saved DeployWatch theme preference.", error);
}

function applyTheme(theme) {
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.classList.remove('dark');
  if (theme === 'dark') {
    root.classList.add('dark');
  } else if (theme === 'system') {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      root.classList.add('dark');
    }
  }
}

applyTheme(currentTheme);

let systemMediaQuery = null;

document.addEventListener("DOMContentLoaded", () => {
  const themeSelect = document.getElementById("theme-select");
  if (!(themeSelect instanceof HTMLSelectElement)) {
    console.error("DeployWatch theme selector is missing from the page.");
    return;
  }

  themeSelect.value = currentTheme;

  const updateSystemListener = () => {
    if (systemMediaQuery) {
      systemMediaQuery.removeEventListener('change', handleSystemChange);
    }
    if (currentTheme === 'system') {
      systemMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      systemMediaQuery.addEventListener('change', handleSystemChange);
    }
  };

  const handleSystemChange = () => {
    applyTheme('system');
  };

  themeSelect.addEventListener("change", () => {
    if (!themes.includes(themeSelect.value)) {
      console.error("Ignoring an unsupported DeployWatch theme preference.");
      themeSelect.value = currentTheme;
      return;
    }

    currentTheme = themeSelect.value;
    applyTheme(currentTheme);

    try {
      window.localStorage.setItem(themeStorageKey, currentTheme);
    } catch (error) {
      console.warn("Could not save the DeployWatch theme preference.", error);
    }
    updateSystemListener();
  });

  updateSystemListener();
});
