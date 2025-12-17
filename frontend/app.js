const $ = (id) => document.getElementById(id);

const apiBase = window.location.origin;
$("apiBase").textContent = apiBase;

const els = {
  uploadForm: $("uploadForm"),
  fileInput: $("fileInput"),
  uploadBtn: $("uploadBtn"),
  jobIdInput: $("jobIdInput"),
  pollBtn: $("pollBtn"),
  stopBtn: $("stopBtn"),
  statusDot: $("statusDot"),
  statusText: $("statusText"),
  statusMeta: $("statusMeta"),
  log: $("log"),
  result: $("result"),
};

let pollTimer = null;

function now() {
  return new Date().toLocaleTimeString();
}

function log(line) {
  els.log.textContent = `[${now()}] ${line}\n` + els.log.textContent;
}

function setStatus(status, meta = "") {
  els.statusText.textContent = status || "unknown";
  els.statusMeta.textContent = meta;

  const dot = els.statusDot;
  const s = (status || "").toLowerCase();
  if (s === "done") dot.style.background = "rgba(24, 194, 156, 0.95)";
  else if (s === "failed") dot.style.background = "rgba(255, 92, 122, 0.95)";
  else if (s === "processing") dot.style.background = "rgba(251, 191, 36, 0.95)";
  else if (s === "queued") dot.style.background = "rgba(124, 92, 255, 0.95)";
  else dot.style.background = "rgba(255,255,255,0.22)";
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  els.stopBtn.disabled = true;
  els.pollBtn.disabled = false;
}

async function submitFile(file) {
  const formData = new FormData();
  formData.append("file", file, file.name);

  const res = await fetch("/submit", { method: "POST", body: formData });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || `Submit failed (${res.status})`);
  }
  return JSON.parse(text);
}

async function fetchStatus(jobId) {
  const res = await fetch(`/status/${encodeURIComponent(jobId)}`);
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || `Status failed (${res.status})`);
  }
  return JSON.parse(text);
}

async function fetchResult(jobId) {
  const res = await fetch(`/result/${encodeURIComponent(jobId)}`);
  const text = await res.text();
  if (res.status === 202) {
    return { pending: true, message: text };
  }
  if (!res.ok) {
    throw new Error(text || `Result failed (${res.status})`);
  }
  return JSON.parse(text);
}

async function pollOnce(jobId) {
  const status = await fetchStatus(jobId);
  setStatus(status.status, status.error ? `error: ${status.error}` : `job_id: ${status.job_id}`);
  log(`status: ${status.status}`);

  if (status.status === "failed") {
    stopPolling();
    els.result.textContent = "(job failed — see status error above)";
    return;
  }

  if (status.status === "done") {
    const result = await fetchResult(jobId);
    els.result.textContent = result.description || "(no description returned)";
    log("result: received description");
    stopPolling();
  }
}

function startPolling(jobId) {
  stopPolling();
  els.stopBtn.disabled = false;
  els.pollBtn.disabled = true;

  pollOnce(jobId).catch((e) => {
    log(`poll error: ${e.message}`);
    setStatus("error", e.message);
    stopPolling();
  });

  pollTimer = setInterval(() => {
    pollOnce(jobId).catch((e) => {
      log(`poll error: ${e.message}`);
      setStatus("error", e.message);
      stopPolling();
    });
  }, 1200);
}

els.uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = els.fileInput.files && els.fileInput.files[0];
  if (!file) return;

  els.uploadBtn.disabled = true;
  els.result.textContent = "(waiting for result...)";
  setStatus("submitting", `file: ${file.name}`);
  log(`submitting: ${file.name} (${Math.round(file.size / 1024)} KB)`);

  try {
    const data = await submitFile(file);
    const jobId = data.job_id;
    els.jobIdInput.value = jobId;
    log(`submitted: job_id=${jobId}`);
    setStatus(data.status || "queued", `job_id: ${jobId}`);
    startPolling(jobId);
  } catch (err) {
    log(`submit error: ${err.message}`);
    setStatus("error", err.message);
    els.result.textContent = "(submit failed)";
  } finally {
    els.uploadBtn.disabled = false;
  }
});

els.pollBtn.addEventListener("click", () => {
  const jobId = (els.jobIdInput.value || "").trim();
  if (!jobId) return;
  els.result.textContent = "(waiting for result...)";
  setStatus("polling", `job_id: ${jobId}`);
  log(`poll start: job_id=${jobId}`);
  startPolling(jobId);
});

els.stopBtn.addEventListener("click", () => {
  log("poll stopped");
  setStatus("idle", "");
  stopPolling();
});


