import { getSelectedValue, renderImageList, selectedImages, setMessage } from "./ui.js";
import { loadRecentTasks, submitGenerate } from "./api.js";

const MAX_IMAGE_BYTES = 5 * 1024 * 1024;
const form = document.querySelector("#generateForm");
const promptInput = document.querySelector("#prompt");
const imageInput = document.querySelector("#imageInput");
const imageList = document.querySelector("#imageList");
const clearImagesButton = document.querySelector("#clearImagesButton");
const modelRadios = Array.from(document.querySelectorAll('input[name="model"]'));
const imageSizeGroup = document.querySelector("#imageSizeGroup");
const generationModeInput = document.querySelector("#generationMode");
const workflowTabs = Array.from(document.querySelectorAll(".workflow-tab"));
const workflowPanels = Array.from(document.querySelectorAll(".mode-panel"));
const outfitTabs = Array.from(document.querySelectorAll(".outfit-tab"));
const outfitPanels = Array.from(document.querySelectorAll(".outfit-panel"));
const fixedInputs = Array.from(document.querySelectorAll("[data-fixed-mode]"));

let activeWorkflow = "outfit";
let activeOutfitMode = "outfit_single";
const fixedFiles = {
  outfit_single: [null, null],
  outfit_multi: [null, null, null],
  white_background: [null],
};

function syncModelControls() {
  imageSizeGroup.hidden = getSelectedValue(form, "model") === "gpt-image-2-c";
}

function validateFile(file) {
  if (!file) return false;
  if (file.size > MAX_IMAGE_BYTES) {
    setMessage(`${file.name} 超过 5 MB，请压缩后重新上传。`, true);
    return false;
  }
  return true;
}

function updateGenerationMode() {
  generationModeInput.value = activeWorkflow === "outfit" ? activeOutfitMode : activeWorkflow;
}

function activateWorkflow(workflow) {
  activeWorkflow = workflow;
  workflowTabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.workflow === workflow));
  workflowPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === workflow));
  updateGenerationMode();
  setMessage("");
}

function activateOutfitMode(mode) {
  activeOutfitMode = mode;
  outfitTabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.outfitMode === mode));
  outfitPanels.forEach((panel) => panel.classList.toggle("active", panel.dataset.outfitPanel === mode));
  updateGenerationMode();
  setMessage("");
}

function renderFixedSlot(input, file) {
  const slot = input.closest(".fixed-upload-slot");
  const preview = slot.querySelector(".fixed-slot-preview");
  const fileLabel = slot.querySelector(".fixed-slot-file");
  const oldUrl = preview.dataset.previewUrl;
  if (oldUrl) URL.revokeObjectURL(oldUrl);

  if (!file) {
    preview.innerHTML = '<span class="upload-icon small">+</span>';
    delete preview.dataset.previewUrl;
    fileLabel.textContent = "未选择图片";
    slot.classList.remove("has-file");
    return;
  }

  const previewUrl = URL.createObjectURL(file);
  preview.dataset.previewUrl = previewUrl;
  preview.innerHTML = `<img src="${previewUrl}" alt="${slot.querySelector(".fixed-slot-title").textContent}预览">`;
  fileLabel.textContent = file.name;
  slot.classList.add("has-file");
}

function getActiveImages() {
  const mode = generationModeInput.value;
  return mode === "custom" ? selectedImages : fixedFiles[mode];
}

window.__getActiveImages = getActiveImages;
window.__setMessage = setMessage;
window.__getSelectedValue = (formNode, name) => getSelectedValue(formNode, name);

fixedInputs.forEach((input) => {
  input.addEventListener("change", () => {
    const file = input.files[0];
    input.value = "";
    if (!validateFile(file)) return;
    const mode = input.dataset.fixedMode;
    const index = Number(input.dataset.slotIndex);
    fixedFiles[mode][index] = file;
    renderFixedSlot(input, file);
    setMessage("");
  });
});

document.querySelectorAll(".fixed-slot-remove").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    const slot = button.closest(".fixed-upload-slot");
    const input = slot.querySelector("[data-fixed-mode]");
    const mode = input.dataset.fixedMode;
    const index = Number(input.dataset.slotIndex);
    fixedFiles[mode][index] = null;
    input.value = "";
    renderFixedSlot(input, null);
    setMessage("");
  });
});

imageInput.addEventListener("change", () => {
  const validFiles = [...imageInput.files].filter(validateFile);
  selectedImages.push(...validFiles);
  imageInput.value = "";
  if (validFiles.length) setMessage("");
  renderImageList(imageList);
});

clearImagesButton?.addEventListener("click", () => {
  selectedImages.length = 0;
  imageInput.value = "";
  setMessage("");
  renderImageList(imageList);
});

workflowTabs.forEach((tab) => tab.addEventListener("click", () => activateWorkflow(tab.dataset.workflow)));
outfitTabs.forEach((tab) => tab.addEventListener("click", () => activateOutfitMode(tab.dataset.outfitMode)));
modelRadios.forEach((radio) => radio.addEventListener("change", syncModelControls));
form.addEventListener("submit", (event) => submitGenerate(event, form, promptInput));

syncModelControls();
updateGenerationMode();
renderImageList(imageList);
loadRecentTasks();
