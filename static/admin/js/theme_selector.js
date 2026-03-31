/**
 * Jazzmin Theme Switcher for LCMS Admin
 * Allows users to switch between Bootswatch themes and persists selection via localStorage
 */

(function() {
    'use strict';

    // Only run on admin pages
    if (!window.location.pathname.startsWith('/admin/')) {
        return;
    }

    const STORAGE_KEY = 'lcms_admin_theme';
    const DEFAULT_THEME = 'flatly';
    const BOOTSWATCH_CDN = 'https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/';

    const THEMES = [
        { value: 'cerulean', label: 'Cerulean' },
        { value: 'cosmo', label: 'Cosmo' },
        { value: 'cyborg', label: 'Cyborg' },
        { value: 'darkly', label: 'Darkly' },
        { value: 'flatly', label: 'Flatly' },
        { value: 'journal', label: 'Journal' },
        { value: 'litera', label: 'Litera' },
        { value: 'lumen', label: 'Lumen' },
        { value: 'lux', label: 'Lux' },
        { value: 'materia', label: 'Materia' },
        { value: 'minty', label: 'Minty' },
        { value: 'morph', label: 'Morph' },
        { value: 'pulse', label: 'Pulse' },
        { value: 'quartz', label: 'Quartz' },
        { value: 'sandstone', label: 'Sandstone' },
        { value: 'simplex', label: 'Simplex' },
        { value: 'sketchy', label: 'Sketchy' },
        { value: 'slate', label: 'Slate' },
        { value: 'solar', label: 'Solar' },
        { value: 'spacelab', label: 'Spacelab' },
        { value: 'superhero', label: 'Superhero' },
        { value: 'united', label: 'United' },
        { value: 'vapor', label: 'Vapor' },
        { value: 'yeti', label: 'Yeti' },
        { value: 'zephyr', label: 'Zephyr' },
    ];

    function getSavedTheme() {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved || DEFAULT_THEME;
    }

    function inferBootswatchPath(theme) {
        // Jazzmin loads Bootswatch CSS, but we manage the theme via our own switcher
        return `${BOOTSWATCH_CDN}${theme}/bootstrap.min.css`;
    }

    function applyTheme(theme) {
        // Remove existing Bootswatch theme link if present
        const existingLink = document.querySelector('link[data-bootswatch-theme]');
        if (existingLink) {
            existingLink.remove();
        }

        // Create and inject new theme link
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = inferBootswatchPath(theme);
        link.dataset.bootswatchTheme = theme;
        document.head.appendChild(link);

        // Save preference
        localStorage.setItem(STORAGE_KEY, theme);
    }

    function mountSelector() {
        // Create container
        const container = document.createElement('div');
        container.id = 'lcms-theme-switcher';

        // Create select element
        const select = document.createElement('select');
        select.setAttribute('aria-label', 'Theme selector');

        // Add options
        THEMES.forEach(theme => {
            const option = document.createElement('option');
            option.value = theme.value;
            option.textContent = theme.label;
            select.appendChild(option);
        });

        // Set current theme
        const currentTheme = getSavedTheme();
        select.value = currentTheme;

        // Handle change
        select.addEventListener('change', (e) => {
            applyTheme(e.target.value);
        });

        // Append to container and body
        container.appendChild(select);
        document.body.appendChild(container);

        // Apply saved theme on page load
        applyTheme(currentTheme);
    }

    // Mount when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mountSelector);
    } else {
        mountSelector();
    }
})();
