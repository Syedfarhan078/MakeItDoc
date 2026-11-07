
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("imagePdfForm");
    if (!form) return;

    const input = document.getElementById("imageInput");
    const dropZone = document.getElementById("uploadZone");
    const grid = document.getElementById("imageGrid");
    const emptyState = document.getElementById("emptyImages");
    const countLabel = document.getElementById("imageCount");
    const convertButton = document.getElementById("convertButton");
    const buttonText = document.getElementById("convertButtonText");
    const status = document.getElementById("conversionStatus");

    const MAX_FILES = 20;
    const MAX_FILE_SIZE = 10 * 1024 * 1024;
    const MAX_TOTAL_SIZE = 40 * 1024 * 1024;
    const ALLOWED_TYPES = ["image/jpeg", "image/png"];

    let selectedFiles = [];
    let previewUrls = [];

    function setStatus(message, isError = false) {
        status.textContent = message;
        status.classList.toggle("status-error", isError);
    }

    function releasePreviews() {
        previewUrls.forEach((url) => URL.revokeObjectURL(url));
        previewUrls = [];
    }

    function validateFiles(files) {
        if (files.length > MAX_FILES) {
            return `Choose no more than ${MAX_FILES} images.`;
        }

        let totalSize = 0;

        for (const file of files) {
            if (!ALLOWED_TYPES.includes(file.type)) {
                return `${file.name}: select a JPG, JPEG, or PNG image.`;
            }

            if (file.size === 0) {
                return `${file.name} is empty.`;
            }

            if (file.size > MAX_FILE_SIZE) {
                return `${file.name} exceeds the 10 MB limit.`;
            }

            totalSize += file.size;
        }

        if (totalSize > MAX_TOTAL_SIZE) {
            return "Your images must total 40 MB or less.";
        }

        return "";
    }

    function syncInputFiles() {
        const transfer = new DataTransfer();

        selectedFiles.forEach((file) => transfer.items.add(file));
        input.files = transfer.files;
    }

    function renderImages() {
        releasePreviews();
        grid.replaceChildren();

        selectedFiles.forEach((file, index) => {
            const url = URL.createObjectURL(file);
            previewUrls.push(url);

            const card = document.createElement("article");
            card.className = "image-preview-card";

            const image = document.createElement("img");
            image.src = url;
            image.alt = `Preview of ${file.name}`;

            const details = document.createElement("div");
            details.className = "image-preview-details";

            const name = document.createElement("span");
            name.className = "image-preview-name";
            name.textContent = file.name;
            name.title = file.name;

            const size = document.createElement("span");
            size.className = "image-preview-size";
            size.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;

            details.append(name, size);

            const controls = document.createElement("div");
            controls.className = "image-preview-controls";

            const moveUp = document.createElement("button");
            moveUp.type = "button";
            moveUp.textContent = "↑";
            moveUp.title = "Move image up";
            moveUp.setAttribute("aria-label", `Move ${file.name} up`);
            moveUp.disabled = index === 0;
            moveUp.addEventListener("click", () => moveImage(index, -1));

            const moveDown = document.createElement("button");
            moveDown.type = "button";
            moveDown.textContent = "↓";
            moveDown.title = "Move image down";
            moveDown.setAttribute("aria-label", `Move ${file.name} down`);
            moveDown.disabled = index === selectedFiles.length - 1;
            moveDown.addEventListener("click", () => moveImage(index, 1));

            const remove = document.createElement("button");
            remove.type = "button";
            remove.textContent = "×";
            remove.title = "Remove image";
            remove.setAttribute("aria-label", `Remove ${file.name}`);
            remove.classList.add("remove-image-button");
            remove.addEventListener("click", () => removeImage(index));

            controls.append(moveUp, moveDown, remove);
            card.append(image, details, controls);
            grid.append(card);
        });

        const count = selectedFiles.length;
        countLabel.textContent = `${count} ${count === 1 ? "image" : "images"}`;
        emptyState.hidden = count !== 0;
        grid.hidden = count === 0;
        convertButton.disabled = count === 0;

        syncInputFiles();
    }

    function addFiles(files) {
        const combined = [...selectedFiles, ...files];

        if (combined.length > MAX_FILES) {
            setStatus(`You can select up to ${MAX_FILES} images.`, true);
            return;
        }

        const error = validateFiles(combined);

        if (error) {
            setStatus(error, true);
            return;
        }

        selectedFiles = combined;
        renderImages();
        setStatus(`${selectedFiles.length} image(s) ready for conversion.`);
    }

    function removeImage(index) {
        selectedFiles.splice(index, 1);
        renderImages();
        setStatus("Image removed.");
    }

    function moveImage(index, direction) {
        const newIndex = index + direction;

        if (newIndex < 0 || newIndex >= selectedFiles.length) return;

        [selectedFiles[index], selectedFiles[newIndex]] =
            [selectedFiles[newIndex], selectedFiles[index]];

        renderImages();
        setStatus("Image order updated.");
    }

    input.addEventListener("change", () => {
        addFiles([...input.files]);
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("is-dragging");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("is-dragging");
        });
    });

    dropZone.addEventListener("drop", (event) => {
        addFiles([...event.dataTransfer.files]);
    });

    form.addEventListener("submit", (event) => {
        syncInputFiles();

        const error = validateFiles(selectedFiles);

        if (selectedFiles.length === 0 || error) {
            event.preventDefault();
            setStatus(error || "Select at least one image.", true);
            return;
        }

        convertButton.disabled = true;
        buttonText.textContent = "Generating PDF...";
        setStatus("Uploading images and generating your PDF...");
    });

    window.addEventListener("pagehide", releasePreviews);

    renderImages();
});
