(function () {
    const STORAGE_KEY = "lcms_admin_theme";
    const DEFAULT_THEME = "flatly";
    const THEMES = [
        "flatly",
        "cosmo",
        "lumen",
        "minty",
        "yeti",
        "united",
        "pulse",
        "sandstone",
        "simplex",
        "spacelab",
        "darkly",
        "slate",
    ];

    function inferBootswatchPath() {
        const links = Array.from(document.querySelectorAll("link[href]"));

        for (const link of links) {
            const href = link.getAttribute("href") || "";
            const match = href.match(/(.*\/vendor\/bootswatch\/)([^/]+)\/bootstrap\.min\.css(?:\?.*)?$/);
            if (match) {
                return {
                    basePath: match[1],
                    currentTheme: match[2],
                };
            }
        }

        return {
            basePath: "/static/vendor/bootswatch/",
            currentTheme: DEFAULT_THEME,
        };
    }

    function themeLabel(themeName) {
        return themeName.charAt(0).toUpperCase() + themeName.slice(1);
    }

    function ensureThemeLink() {
        let link = document.getElementById("lcms-theme-override");
        if (!link) {
            link = document.createElement("link");
            link.id = "lcms-theme-override";
            link.rel = "stylesheet";
            document.head.appendChild(link);
        }
        return link;
    }

    function applyTheme(selectedTheme, defaultTheme, basePath) {
        const link = ensureThemeLink();

        if (!selectedTheme || selectedTheme === "default" || selectedTheme === defaultTheme) {
            link.removeAttribute("href");
            return;
        }

        link.href = `${basePath}${selectedTheme}/bootstrap.min.css`;
    }

    function mountSelector(initialTheme, onThemeChange) {
        if (document.getElementById("lcms-theme-switcher")) {
            return;
        }

        const wrapper = document.createElement("div");
        wrapper.id = "lcms-theme-switcher";

        const label = document.createElement("label");
        label.setAttribute("for", "lcms-theme-select");
        label.textContent = "Theme";

        const select = document.createElement("select");
        select.id = "lcms-theme-select";
        select.className = "form-control";

        const defaultOption = document.createElement("option");
        defaultOption.value = "default";
        defaultOption.textContent = "Default";
        select.appendChild(defaultOption);

        THEMES.forEach((theme) => {
            const option = document.createElement("option");
            option.value = theme;
            option.textContent = themeLabel(theme);
            select.appendChild(option);
        });

        select.value = initialTheme;

        select.addEventListener("change", function (event) {
            const newTheme = event.target.value;
            if (newTheme === "default") {
                localStorage.removeItem(STORAGE_KEY);
            } else {
                localStorage.setItem(STORAGE_KEY, newTheme);
            }
            onThemeChange(newTheme);
        });

        wrapper.appendChild(label);
        wrapper.appendChild(select);
        document.body.appendChild(wrapper);
    }

    document.addEventListener("DOMContentLoaded", function () {
        if (!window.location.pathname.startsWith("/admin/")) {
            return;
        }

        const { basePath, currentTheme } = inferBootswatchPath();
        const savedTheme = localStorage.getItem(STORAGE_KEY);
        const initialTheme = savedTheme && THEMES.includes(savedTheme) ? savedTheme : "default";

        mountSelector(initialTheme, function (theme) {
            applyTheme(theme, currentTheme || DEFAULT_THEME, basePath);
        });

        applyTheme(initialTheme, currentTheme || DEFAULT_THEME, basePath);
    });
})();
