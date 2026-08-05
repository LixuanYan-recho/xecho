const formMessage = document.querySelector("#formMessage");
const tasks = document.querySelector("#tasks");
const taskCount = document.querySelector("#taskCount");
const MAX_VISIBLE_TASKS = 10;

let selectedImages = [];
let previewUrls = [];

function setMessage(message, isError = false) {
  formMessage.textContent = message;
  formMessage.classList.toggle("error", isError);
}

function getSelectedValue(form, name) {
  const checked = form.querySelector(`input[name="${name}"]:checked`);
  if (checked) {
    return checked.value;
  }
  const field = form.querySelector(`[name="${name}"]`);
  return field ? field.value : "";
}

function renderImageList(imageList) {
  previewUrls.forEach((url) => URL.revokeObjectURL(url));
  previewUrls = [];
  imageList.innerHTML = "";
  imageList.classList.toggle("is-empty", selectedImages.length === 0);

  if (!selectedImages.length) {
    imageList.innerHTML = "<p>还没有选择图片。</p>";
    return;
  }

  selectedImages.forEach((file, index) => {
    const previewUrl = URL.createObjectURL(file);
    previewUrls.push(previewUrl);

    const item = document.createElement("div");
    item.className = "image-item";
    item.innerHTML = `
      <div class="preview-frame">
        <img src="${previewUrl}" alt="图${index + 1} 预览">
        <div class="slot-index">图${index + 1}</div>
        <button class="remove-slot" type="button" title="删除这张图片">×</button>
      </div>
      <div class="file-name" title="${file.name}">${file.name}</div>
    `;

    item.querySelector("button").addEventListener("click", () => {
      selectedImages.splice(index, 1);
      renderImageList(imageList);
    });

    imageList.append(item);
  });
}

function updateTaskCount() {
  taskCount.textContent = `${tasks.querySelectorAll(".task").length} 个任务`;
}

function trimTaskList() {
  while (tasks.querySelectorAll(".task").length > MAX_VISIBLE_TASKS) {
    const taskCards = tasks.querySelectorAll(".task");
    taskCards[taskCards.length - 1]?.remove();
  }
}

function createTaskCard(meta, options = {}) {
  tasks.classList.remove("empty-state");

  if (tasks.firstElementChild?.tagName === "P") {
    tasks.innerHTML = "";
  }

  const task = document.createElement("article");
  task.className = "task";

  const metaParts = [meta.model, meta.imageSize].filter(Boolean);
  if (Number.isInteger(meta.imageCount) && meta.imageCount > 0) {
    metaParts.push(`${meta.imageCount} 张图`);
  }
  if (meta.aspectRatio) {
    metaParts.push(meta.aspectRatio);
  }

  task.innerHTML = `
    <div class="task-head">
      <div class="task-title">${options.title || new Date().toLocaleString("zh-CN")}</div>
      <div class="task-status">${options.statusText || "生成中"}</div>
    </div>
    <div class="task-meta">
      ${metaParts.map((part) => `<span>${part}</span>`).join("")}
    </div>
    <div class="task-body">
      ${options.showSpinner === false ? "" : '<div class="spinner" aria-label="生成中"></div>'}
    </div>
  `;

  tasks.prepend(task);
  trimTaskList();
  updateTaskCount();
  return task;
}

function clearTaskCards() {
  tasks.innerHTML = "";
  tasks.classList.remove("empty-state");
}

function renderEmptyTasks() {
  tasks.classList.add("empty-state");
  tasks.innerHTML = "<p>生成后，任务卡片会出现在这里。</p>";
  updateTaskCount();
}

function createStoredTaskCard(item) {
  const requestedAt = item.requested_at ? new Date(item.requested_at).toLocaleString("zh-CN") : "";
  const isProcessing = item.status === "processing";
  const task = createTaskCard(
    {
      model: item.model,
      imageSize: "",
      imageCount: null,
      aspectRatio: "",
    },
    {
      title: requestedAt || `请求 ${item.request_id.slice(0, 8)}`,
      statusText: isProcessing ? "生成中" : item.status === "success" ? "已完成" : "失败",
      showSpinner: isProcessing,
    },
  );
  task.dataset.requestId = item.request_id;
  if (item.status === "success") {
    renderSuccess(task, item.data || []);
  } else if (item.status === "failed") {
    renderError(task, item.error || "生成失败。");
  }
  return task;
}

function getResultUrl(item) {
  if (!item) {
    return "";
  }
  if (typeof item === "string") {
    return item;
  }
  if (typeof item !== "object") {
    return "";
  }
  return item.url || item.image_url?.url || item.image_url || "";
}

function isBase64Result(item) {
  return Boolean(item && typeof item === "object" && item.kind === "base64");
}

function renderResultImage(container, url, index, clickUrl = "") {
  const image = document.createElement("img");
  image.className = "result-image";
  image.src = url;
  image.alt = `生成结果 ${index + 1}`;

  if (clickUrl) {
    const link = document.createElement("a");
    link.href = clickUrl;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.append(image);
    container.append(link);
  } else {
    container.append(image);
  }
}

function renderSuccess(task, data) {
  const status = task.querySelector(".task-status");
  const body = task.querySelector(".task-body");
  body.innerHTML = "";

  if (!data.length) {
    body.textContent = "接口返回成功，但没有图片。";
    return;
  }

  status.textContent = "图片加载中";
  let completedCount = 0;
  let successCount = 0;

  data.forEach((item, index) => {
    const url = getResultUrl(item);
    if (!url) {
      completedCount += 1;
      return;
    }

    if (isBase64Result(item)) {
      const wrapper = document.createElement("div");
      wrapper.className = "result-frame";
      renderResultImage(wrapper, url, index);
      body.append(wrapper);
      successCount += 1;
      completedCount += 1;
      if (completedCount >= data.length) {
        task.dataset.loaded = "true";
        status.textContent = successCount ? "已显示" : "部分失败";
      }
      return;
    }

    const link = document.createElement("a");
    link.className = "result-link";
    link.href = url;
    link.target = "_blank";
    link.rel = "noreferrer";

    const wrapper = document.createElement("div");
    wrapper.className = "result-frame";
    renderResultImage(wrapper, url, index, url);
    link.append(wrapper);
    body.append(link);

    successCount += 1;
    completedCount += 1;
    if (completedCount >= data.length) {
      task.dataset.loaded = "true";
      status.textContent = successCount ? "已显示" : "部分失败";
    }
  });
}

function renderError(task, error) {
  task.classList.add("error");
  task.querySelector(".task-status").textContent = "失败";
  task.querySelector(".task-body").textContent = error || "生成失败。";
}

export {
  createTaskCard,
  createStoredTaskCard,
  clearTaskCards,
  getSelectedValue,
  renderError,
  renderImageList,
  renderEmptyTasks,
  renderSuccess,
  selectedImages,
  setMessage,
  updateTaskCount,
};
