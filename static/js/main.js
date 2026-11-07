/**
 * MakeitDoc — Editorial Utility Studio
 * Client-side Controller: Theme, Mobile Navigation, Tool Search, and Processing States
 */

document.addEventListener("DOMContentLoaded", () => {

    // ==========================================
    // 1. THEME MANAGEMENT (LIGHT & DARK MODES)
    // ==========================================
    const themeToggle = document.getElementById("themeToggle");
    const themeLabel = document.getElementById("themeLabel");
    const themeColorMeta = document.getElementById("themeColorMeta");

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
        const isDark = theme === "dark";

        if (themeLabel) {
            themeLabel.textContent = isDark ? "Light" : "Dark";
        }
        if (themeToggle) {
            themeToggle.setAttribute(
                "aria-label",
                isDark ? "Switch to light mode" : "Switch to dark mode"
            );
        }
        if (themeColorMeta) {
            themeColorMeta.setAttribute(
                "content",
                isDark ? "#141A16" : "#F7F8F4"
            );
        }
    }

    // Determine default theme: saved preference -> system dark mode preference -> light
    let preferredTheme = "light";
    try {
        const stored = localStorage.getItem("makeitdoc-theme") || localStorage.getItem("toolnest-theme");
        if (stored === "light" || stored === "dark") {
            preferredTheme = stored;
        } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            preferredTheme = "dark";
        }
    } catch (e) {
        // Storage restricted
    }

    applyTheme(preferredTheme);

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const current = document.documentElement.dataset.theme;
            const nextTheme = current === "dark" ? "light" : "dark";
            applyTheme(nextTheme);
            try {
                localStorage.setItem("makeitdoc-theme", nextTheme);
                localStorage.setItem("toolnest-theme", nextTheme);
            } catch (e) {}
        });
    }

    // ==========================================
    // 2. MOBILE DRAWER NAVIGATION
    // ==========================================
    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add("is-open");
        if (sidebarBackdrop) sidebarBackdrop.classList.add("is-active");
        if (menuToggle) menuToggle.setAttribute("aria-expanded", "true");
        document.body.style.overflow = "hidden";
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove("is-open");
        if (sidebarBackdrop) sidebarBackdrop.classList.remove("is-active");
        if (menuToggle) menuToggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
    }

    if (menuToggle) {
        menuToggle.addEventListener("click", () => {
            const isOpen = sidebar && sidebar.classList.contains("is-open");
            if (isOpen) closeSidebar();
            else openSidebar();
        });
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener("click", closeSidebar);
    }

    if (sidebar) {
        sidebar.querySelectorAll(".nav-link").forEach(link => {
            link.addEventListener("click", () => {
                if (window.innerWidth <= 880) closeSidebar();
            });
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && sidebar && sidebar.classList.contains("is-open")) {
            closeSidebar();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 880 && sidebar && sidebar.classList.contains("is-open")) {
            closeSidebar();
        }
    });

    // ==========================================
    // 3. OVERVIEW SEARCH & CATEGORY FILTER TABS
    // ==========================================
    const searchInput = document.getElementById("toolSearch");
    const searchClearBtn = document.getElementById("searchClearBtn");
    const searchStatus = document.getElementById("searchStatus");
    const emptySearch = document.getElementById("emptySearch");
    const resetSearchBtn = document.getElementById("resetSearchBtn");
    const categoryTabs = document.querySelectorAll(".category-tab");
    const toolCards = [...document.querySelectorAll(".tool-card")];
    const toolSections = [...document.querySelectorAll(".tool-section")];

    let currentCategory = "all";

    function filterOverviewTools() {
        const query = searchInput ? searchInput.value.trim().toLowerCase() : "";
        let visibleCount = 0;

        if (searchClearBtn) {
            searchClearBtn.style.display = query ? "block" : "none";
        }

        toolCards.forEach(card => {
            const cardCat = card.dataset.category || "";
            const matchesCat = currentCategory === "all" || cardCat === currentCategory;

            const searchableContent = (
                (card.innerText || "") + " " + (card.dataset.tool || "")
            ).toLowerCase();
            const matchesQuery = !query || searchableContent.includes(query);

            const isVisible = matchesCat && matchesQuery;
            card.hidden = !isVisible;
            if (isVisible) visibleCount++;
        });

        // Hide section container if all cards within it are filtered out
        toolSections.forEach(section => {
            const sectionCat = section.dataset.category || "";
            const cardsInSection = section.querySelectorAll(".tool-card");
            const hasVisibleCard = [...cardsInSection].some(c => !c.hidden);
            const matchesCategory = currentCategory === "all" || sectionCat === currentCategory;
            section.hidden = !hasVisibleCard || !matchesCategory;
        });

        if (emptySearch) {
            emptySearch.hidden = visibleCount !== 0;
        }

        if (searchStatus) {
            if (query || currentCategory !== "all") {
                searchStatus.textContent = `${visibleCount} tool${visibleCount === 1 ? "" : "s"} found`;
            } else {
                searchStatus.textContent = "";
            }
        }
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterOverviewTools);

        // Keyboard Shortcut: Cmd/Ctrl + K or / to focus search
        window.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            } else if (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }

    if (searchClearBtn) {
        searchClearBtn.addEventListener("click", () => {
            if (searchInput) {
                searchInput.value = "";
                filterOverviewTools();
                searchInput.focus();
            }
        });
    }

    if (resetSearchBtn) {
        resetSearchBtn.addEventListener("click", () => {
            if (searchInput) searchInput.value = "";
            currentCategory = "all";
            categoryTabs.forEach(tab => tab.classList.toggle("active", tab.dataset.filter === "all"));
            filterOverviewTools();
            if (searchInput) searchInput.focus();
        });
    }

    categoryTabs.forEach(tab => {
        tab.addEventListener("click", function () {
            categoryTabs.forEach(t => {
                t.classList.remove("active");
                t.setAttribute("aria-selected", "false");
            });
            this.classList.add("active");
            this.setAttribute("aria-selected", "true");
            currentCategory = this.dataset.filter || "all";
            filterOverviewTools();
        });
    });

    // ==========================================
    // 4. MINIMALIST PROCESSING OVERLAY & INLINE SPINNERS
    // ==========================================
    const loadingOverlay = document.getElementById("globalLoadingOverlay");
    const loadingTitle = document.getElementById("loadingTitle");
    const loadingSubtitle = document.getElementById("loadingSubtitle");

    window.showMakeitDocLoader = function (title, subtitle) {
        if (!loadingOverlay) return;
        if (loadingTitle && title) loadingTitle.textContent = title;
        if (loadingSubtitle && subtitle) loadingSubtitle.textContent = subtitle;
        loadingOverlay.classList.add("is-active");
    };

    window.hideMakeitDocLoader = function () {
        if (!loadingOverlay) return;
        loadingOverlay.classList.remove("is-active");
    };

    if (loadingOverlay) {
        loadingOverlay.addEventListener("click", (e) => {
            if (e.target === loadingOverlay) {
                window.hideMakeitDocLoader();
            }
        });
    }

    // Auto-hook tool form submissions
    const forms = document.querySelectorAll("form");
    forms.forEach(form => {
        // Skip quick_notes or forms without file actions if any
        if (form.id === "notesForm") return;

        form.addEventListener("submit", function () {
            const submitBtn = this.querySelector("button[type='submit'], input[type='submit']");
            if (submitBtn && !submitBtn.disabled) {
                if (!submitBtn.querySelector(".btn-spinner")) {
                    const sp = document.createElement("span");
                    sp.className = "btn-spinner";
                    sp.setAttribute("aria-hidden", "true");
                    submitBtn.prepend(sp);
                }
                submitBtn.disabled = true;
            }

            let actionText = "Processing Document...";
            const h1 = document.querySelector("h1");
            if (h1) {
                actionText = `${h1.textContent.trim()} in progress...`;
            }

            window.showMakeitDocLoader(
                actionText,
                "MakeitDoc is securely processing your document."
            );

            // Safety timeout to reset buttons if download initiates without full reload
            setTimeout(() => {
                window.hideMakeitDocLoader();
                if (submitBtn) {
                    submitBtn.disabled = false;
                    const sp = submitBtn.querySelector(".btn-spinner");
                    if (sp) sp.remove();
                }
            }, 5000);
        });
    });

});
