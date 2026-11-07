
document.addEventListener("DOMContentLoaded", () => {
        // Theme Management

    const themeToggle = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const themeLabel = document.getElementById("themeLabel");
    const themeColorMeta = document.getElementById("themeColorMeta");

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;

        const isDark = theme === "dark";

        if (themeIcon) {
            themeIcon.textContent = isDark ? "☀" : "☾";
        }

        if (themeLabel) {
            themeLabel.textContent = isDark ? "Light mode" : "Dark mode";
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
                isDark ? "#0b0d12" : "#f5f6f8"
            );
        }
    }

    let savedTheme = "dark";

    try {
        const storedTheme = localStorage.getItem("toolnest-theme");

        if (storedTheme === "light" || storedTheme === "dark") {
            savedTheme = storedTheme;
        }
    } catch (error) {
        // Use dark mode if browser storage is unavailable.
    }

    applyTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener("click", () => {
            const currentTheme = document.documentElement.dataset.theme;
            const newTheme = currentTheme === "dark" ? "light" : "dark";

            applyTheme(newTheme);

            try {
                localStorage.setItem("toolnest-theme", newTheme);
            } catch (error) {
                // Theme still works for the current page.
            }
        });
    }
    const searchInput = document.getElementById("toolSearch");
    const searchStatus = document.getElementById("searchStatus");
    const emptySearch = document.getElementById("emptySearch");
    const toolCards = [...document.querySelectorAll(".tool-card")];
    const toolSections = [...document.querySelectorAll(".tool-section")];

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const query = searchInput.value.trim().toLowerCase();
            let visibleCount = 0;

            toolCards.forEach((card) => {
                const searchableText = (
                    card.innerText + " " + (card.dataset.tool || "")
                ).toLowerCase();

                const matches = searchableText.includes(query);

                card.hidden = !matches;

                if (matches) {
                    visibleCount++;
                }
            });

            toolSections.forEach((section) => {
                const cards = section.querySelectorAll(".tool-card");
                const hasVisibleCard = [...cards].some(
                    (card) => !card.hidden
                );

                section.hidden = !hasVisibleCard;
            });

            if (emptySearch) {
                emptySearch.hidden = visibleCount !== 0;
            }

            if (searchStatus) {
                searchStatus.textContent = query
                    ? `${visibleCount} tool${visibleCount === 1 ? "" : "s"} found`
                    : "";
            }
        });
    }

    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");

    function closeSidebar() {
        if (!sidebar || !menuToggle) return;

        sidebar.classList.remove("is-open");
        menuToggle.setAttribute("aria-expanded", "false");
    }

    if (sidebar && menuToggle) {
        menuToggle.addEventListener("click", () => {
            const isOpen = sidebar.classList.toggle("is-open");

            menuToggle.setAttribute(
                "aria-expanded",
                String(isOpen)
            );
        });

        sidebar.querySelectorAll("a").forEach((link) => {
            link.addEventListener("click", closeSidebar);
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeSidebar();
            }
        });

        document.addEventListener("click", (event) => {
            if (
                window.innerWidth <= 760 &&
                sidebar.classList.contains("is-open") &&
                !sidebar.contains(event.target) &&
                !menuToggle.contains(event.target)
            ) {
                closeSidebar();
            }
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 760) {
                closeSidebar();
            }
        });
    }
});
