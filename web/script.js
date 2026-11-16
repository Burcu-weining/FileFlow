
const fileInput = document.getElementById("fileInput");
const browseButton = document.getElementById("browseButton");
const dropArea = document.getElementById("dropArea");

const selectedFileBox = document.getElementById("selectedFile");
const fileName = document.getElementById("fileName");
const removeButton = document.getElementById("removeButton");

const outputFormat = document.getElementById("outputFormat");
const convertButton = document.getElementById("convertButton");
const statusMessage = document.getElementById("statusMessage");

const resultSection = document.getElementById("resultSection");
const previewContainer = document.getElementById("previewContainer");
const resultPreview = document.getElementById("resultPreview");
const noPreviewMessage = document.getElementById("noPreviewMessage");
const downloadButton = document.getElementById("downloadButton");

const MAX_UPLOAD_SIZE = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".pdf"];

let selectedFile = null;
let resultUrl = null;
let converting = false;


function clearResult() {
    resultSection.hidden = true;
    previewContainer.hidden = true;
    noPreviewMessage.hidden = true;
    resultPreview.removeAttribute("src");
    downloadButton.removeAttribute("href");

    if (resultUrl) {
        URL.revokeObjectURL(resultUrl);
        resultUrl = null;
    }
}


function updateFormatOptions() {
    const isPdf = selectedFile &&
        selectedFile.name.toLowerCase().endsWith(".pdf");

    for (const option of outputFormat.options) {
        option.disabled = Boolean(
            isPdf && !["JPG", "PNG"].includes(option.value)
        );
    }

    if (isPdf && !["JPG", "PNG"].includes(outputFormat.value)) {
        outputFormat.value = "JPG";
    }
}


function selectFile(file) {
    if (converting || !file) return;

    clearResult();
    statusMessage.textContent = "";

    const name = file.name.toLowerCase();
    const valid = ALLOWED_EXTENSIONS.some(
        extension => name.endsWith(extension)
    );

    if (!valid) {
        statusMessage.textContent = "Unsupported file type.";
        return;
    }

    if (file.size > MAX_UPLOAD_SIZE) {
        statusMessage.textContent = "Maximum file size is 10 MB.";
        return;
    }

    selectedFile = file;
    fileName.textContent = `Selected: ${file.name}`;
    selectedFileBox.hidden = false;

    updateFormatOptions();
}


function removeFile() {
    if (converting) return;

    selectedFile = null;
    fileInput.value = "";

    selectedFileBox.hidden = true;
    statusMessage.textContent = "";
    clearResult();

    updateFormatOptions();
}


// Browse files
browseButton.addEventListener("click", () => {
    if (!converting) fileInput.click();
});

fileInput.addEventListener("change", () => {
    selectFile(fileInput.files[0]);
});


// Drag and drop
dropArea.addEventListener("dragover", event => {
    event.preventDefault();
    if (!converting) dropArea.classList.add("drag-over");
});

dropArea.addEventListener("dragleave", () => {
    dropArea.classList.remove("drag-over");
});

dropArea.addEventListener("drop", event => {
    event.preventDefault();
    dropArea.classList.remove("drag-over");

    if (!converting) {
        selectFile(event.dataTransfer.files[0]);
    }
});

removeButton.addEventListener("click", removeFile);

outputFormat.addEventListener("change", () => {
    if (!converting) {
        clearResult();
        statusMessage.textContent = "";
    }
});


// Convert file
convertButton.addEventListener("click", async () => {
    if (converting) return;

    if (!selectedFile) {
        statusMessage.textContent = "Please select a file first.";
        return;
    }

    converting = true;
    clearResult();

    convertButton.disabled = true;
    removeButton.disabled = true;
    outputFormat.disabled = true;
    browseButton.disabled = true;

    convertButton.textContent = "Converting...";
    statusMessage.textContent = "Converting your file...";

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("output_format", outputFormat.value);

    try {
        const response = await fetch("/convert", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            let message = "Conversion failed.";

            try {
                const error = await response.json();
                message = error.detail || message;
            } catch (_) {
                // Use the default message
            }

            throw new Error(message);
        }

        const blob = await response.blob();
        resultUrl = URL.createObjectURL(blob);

        const isZip = response.headers
            .get("content-type")
            ?.includes("application/zip");

        const format = outputFormat.value.toLowerCase();

        let extension = format === "jpeg" ? "jpg" : format;

        if (isZip) {
            extension = "zip";
        }

        const baseName = selectedFile.name.replace(/\.[^.]+$/, "");
        const downloadName = `${baseName}.${extension}`;

        downloadButton.href = resultUrl;
        downloadButton.download = downloadName;

        const isImage = !isZip &&
            ["jpg", "jpeg", "png", "webp"].includes(extension);

        if (isImage) {
            resultPreview.src = resultUrl;
            previewContainer.hidden = false;
        } else {
            noPreviewMessage.hidden = false;
        }

        resultSection.hidden = false;
        statusMessage.textContent = "";

    } catch (error) {
        statusMessage.textContent = error.message;
    } finally {
        converting = false;

        convertButton.disabled = false;
        removeButton.disabled = false;
        outputFormat.disabled = false;
        browseButton.disabled = false;

        convertButton.textContent = "Convert File";
    }
});
