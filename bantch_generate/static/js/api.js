import {
  clearTaskCards,
  createStoredTaskCard,
  createTaskCard,
  renderEmptyTasks,
  renderError,
  renderSuccess,
} from "./ui.js";

let recentTaskRefreshTimer = null;

function formatErrorMessage(result, fallbackText = "生成失败。") {
  if (!result || typeof result !== "object") {
    return fallbackText;
  }
  const parts = [];
  if (result.error) parts.push(result.error);
  if (result.request_id) parts.push(`request_id=${result.request_id}`);
  if (result.task_id) parts.push(`task_id=${result.task_id}`);
  return parts.join(" | ") || fallbackText;
}

async function submitGenerate(event, form, promptInput) {
  event.preventDefault();
  window.__setMessage("");

  const generationMode = form.querySelector("#generationMode").value;
  const activeImages = window.__getActiveImages?.() || [];
  if (generationMode === "custom" && !promptInput.value.trim()) {
    window.__setMessage("自定义模式必须输入提示词。", true);
    promptInput.focus();
    return;
  }
  const missingFixedSlot = generationMode !== "custom" && activeImages.some((file) => !file);
  if (!activeImages.length || missingFixedSlot) {
    window.__setMessage("请上传当前模式要求的全部图片。", true);
    return;
  }

  const model = window.__getSelectedValue(form, "model");
  const imageSize = window.__getSelectedValue(form, "image_size");
  const aspectRatio = window.__getSelectedValue(form, "aspect_ratio");
  const skipImageSize = model === "gpt-image-2-c";
  const payload = new FormData();
  payload.append("generation_mode", generationMode);
  payload.append("prompt", promptInput.value);
  payload.append("model", model);
  if (!skipImageSize) payload.append("image_size", imageSize);
  if (aspectRatio) payload.append("aspect_ratio", aspectRatio);
  activeImages.forEach((file) => payload.append("images[]", file));

  const task = createTaskCard({
    model,
    imageSize: skipImageSize ? "" : imageSize,
    imageCount: activeImages.length,
    aspectRatio,
  });

  try {
    const response = await fetch("/api/generate", { method: "POST", body: payload });
    let result;
    try {
      result = await response.json();
    } catch {
      renderError(task, `服务返回了非 JSON 响应（HTTP ${response.status}）。`);
      return;
    }
    if (!response.ok || !result.ok) {
      renderError(task, formatErrorMessage(result));
      setTimeout(loadRecentTasks, 300);
      return;
    }
    renderSuccess(task, result.data || []);
    setTimeout(loadRecentTasks, 300);
  } catch (error) {
    renderError(task, error.message);
  }
}

async function loadRecentTasks() {
  try {
    const response = await fetch("/api/tasks/recent", { headers: { Accept: "application/json" } });
    const result = await response.json();
    if (!response.ok || !result.ok) return;

    clearTaskCards();
    if (!result.data?.length) {
      renderEmptyTasks();
      return;
    }
    result.data.slice().reverse().forEach((item) => createStoredTaskCard(item));

    const hasProcessingTask = result.data.some((item) => item.status === "processing");
    if (hasProcessingTask) {
      clearTimeout(recentTaskRefreshTimer);
      recentTaskRefreshTimer = setTimeout(loadRecentTasks, 3000);
    }
  } catch {
    // A temporary refresh failure must not disturb tasks already visible on the page.
  }
}

export { loadRecentTasks, submitGenerate };
