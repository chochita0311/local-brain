function formatLocalTime(value) {
  if (!value || value === "대기 중" || value === "-") return value;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

document.querySelectorAll("[data-local-time]").forEach((element) => {
  element.textContent = formatLocalTime(element.getAttribute("datetime") || element.textContent);
});

document.querySelectorAll("[data-local-epoch]").forEach((element) => {
  const milliseconds = Number(element.getAttribute("datetime"));
  if (Number.isFinite(milliseconds)) {
    element.textContent = formatLocalTime(new Date(milliseconds).toISOString());
  }
});

const scanButton = document.querySelector("#scan-button");
const scanResult = document.querySelector("#scan-result");

if (scanButton) {
  scanButton.addEventListener("click", async () => {
    const idle = scanButton.querySelector(".button-idle");
    const working = scanButton.querySelector(".button-working");
    scanButton.disabled = true;
    idle.hidden = true;
    working.hidden = false;
    scanResult.hidden = true;

    try {
      const response = await fetch("/api/scan", { method: "POST" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const imported = Object.values(data.report).reduce(
        (sum, source) => sum + source.imported,
        0,
      );
      scanResult.textContent = `${imported}개 변경 항목을 반영했습니다. 화면을 갱신합니다.`;
      scanResult.className = "scan-result success";
      scanResult.hidden = false;
      window.setTimeout(() => window.location.reload(), 700);
    } catch (error) {
      scanResult.textContent = `스캔에 실패했습니다: ${error.message}`;
      scanResult.className = "scan-result error";
      scanResult.hidden = false;
      scanButton.disabled = false;
      idle.hidden = false;
      working.hidden = true;
    }
  });
}

async function requestJson(endpoint, options = {}) {
  const response = await fetch(endpoint, options);
  let data = {};
  try {
    data = await response.json();
  } catch (_error) {
    data = {};
  }
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join(", ")
      : data.detail;
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return data;
}

function splitReference(value) {
  const separator = value.indexOf(":");
  if (separator < 1) return ["", ""];
  return [value.slice(0, separator), value.slice(separator + 1)];
}

document.querySelectorAll("[data-api-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector("button[type='submit']");
    const result = form.querySelector("[data-form-result]");
    const payload = Object.fromEntries(new FormData(form).entries());

    if (form.hasAttribute("data-split-entity")) {
      [payload.scope_type, payload.scope_id] = splitReference(payload.scope_ref || "");
      [payload.entity_type, payload.entity_id] = splitReference(payload.entity_ref || "");
      delete payload.scope_ref;
      delete payload.entity_ref;
    } else if (form.hasAttribute("data-split-scope")) {
      [payload.scope_type, payload.scope_id] = splitReference(payload.scope_ref || "");
      delete payload.scope_ref;
    }

    submitButton.disabled = true;
    if (result) result.hidden = true;
    try {
      const data = await requestJson(form.dataset.endpoint, {
        method: form.dataset.method || "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (data.redirect) {
        window.location.assign(data.redirect);
        return;
      }
      if (result) {
        result.textContent = "저장했습니다.";
        result.className = "form-result success";
        result.hidden = false;
      }
      window.setTimeout(() => window.location.reload(), 350);
    } catch (error) {
      if (result) {
        result.textContent = error.message;
        result.className = "form-result error";
        result.hidden = false;
      }
      submitButton.disabled = false;
    }
  });
});

document.querySelectorAll("[data-delete-link]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!window.confirm("이 연결을 제거할까요?")) return;
    button.disabled = true;
    try {
      await requestJson(button.dataset.deleteLink, { method: "DELETE" });
      window.location.reload();
    } catch (error) {
      window.alert(error.message);
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-delete-context-root], [data-delete-context-source]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (!window.confirm("이 Source를 Local Contexts 인덱스에서 제거할까요? 실제 파일과 Apple Notes는 삭제되지 않습니다.")) return;
    button.disabled = true;
    try {
      const sourceId = button.dataset.deleteContextSource || button.dataset.deleteContextRoot;
      await requestJson(`/api/context-sources/${sourceId}`, {
        method: "DELETE",
      });
      window.location.assign("/context");
    } catch (error) {
      window.alert(error.message);
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-suggestion-run]").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    const original = button.textContent;
    button.textContent = "분석 중";
    try {
      const data = await requestJson(
        `/api/workstreams/${button.dataset.suggestionRun}/suggestions`,
        { method: "POST" },
      );
      button.textContent = `${data.created}개 제안`;
      window.setTimeout(() => window.location.reload(), 500);
    } catch (error) {
      window.alert(error.message);
      button.disabled = false;
      button.textContent = original;
    }
  });
});

document.querySelectorAll("[data-suggestion-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      await requestJson(button.dataset.suggestionAction, { method: "POST" });
      window.location.reload();
    } catch (error) {
      window.alert(error.message);
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-maintenance-run]").forEach((button) => {
  button.addEventListener("click", async () => {
    const container = button.parentElement;
    const marker = container.querySelector("[data-maintenance-marker]");
    const copyButton = container.querySelector("[data-copy-marker]");
    button.disabled = true;
    try {
      const workstreamId = button.dataset.maintenanceRun || null;
      const data = await requestJson("/api/maintenance-runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workstream_id: workstreamId }),
      });
      marker.textContent = data.marker;
      marker.hidden = false;
      copyButton.hidden = false;
      button.textContent = "새 마커 생성";
    } catch (error) {
      window.alert(error.message);
    } finally {
      button.disabled = false;
    }
  });
});

document.querySelectorAll("[data-copy-marker]").forEach((button) => {
  button.addEventListener("click", async () => {
    const marker = button.parentElement.querySelector("[data-maintenance-marker]");
    await navigator.clipboard.writeText(marker.textContent);
    button.textContent = "복사됨";
    window.setTimeout(() => { button.textContent = "마커 복사"; }, 1000);
  });
});

const runConsole = document.querySelector("[data-run-console]");

if (runConsole) {
  const runId = runConsole.dataset.runId;
  const output = runConsole.querySelector("[data-run-output]");
  const status = document.querySelector("[data-run-status]");
  const pid = document.querySelector("[data-run-pid]");
  const suggestions = document.querySelector("[data-run-suggestions]");
  const mcpCalls = document.querySelector("[data-run-mcp]");
  const updated = runConsole.querySelector("[data-run-updated]");
  const errorPanel = runConsole.querySelector("[data-run-error]");
  const cancelButton = document.querySelector("[data-cancel-run]");
  const activeStatuses = new Set(["queued", "running", "cancelling"]);

  const refreshRun = async () => {
    try {
      const data = await requestJson(`/api/runs/${runId}`);
      const current = data.run;
      status.textContent = current.status;
      status.className = `run-status large ${current.status}`;
      pid.textContent = current.pid || "-";
      if (suggestions) suggestions.textContent = current.suggestions_created || 0;
      if (mcpCalls) {
        mcpCalls.textContent = `${current.mcp_calls_used || 0} / ${current.mcp_call_budget}`;
        mcpCalls.classList.toggle("missing", Boolean(current.mcp_budget_exceeded));
      }
      updated.textContent = formatLocalTime(current.updated_at);
      if (current.output) output.textContent = current.output;
      if (current.error) {
        errorPanel.textContent = current.error;
        errorPanel.hidden = false;
      }
      cancelButton.hidden = !activeStatuses.has(current.status);
      if (activeStatuses.has(current.status)) {
        window.setTimeout(refreshRun, 1000);
      }
    } catch (error) {
      errorPanel.textContent = error.message;
      errorPanel.hidden = false;
    }
  };

  if (activeStatuses.has(status.textContent.trim())) {
    window.setTimeout(refreshRun, 500);
  }

  cancelButton.addEventListener("click", async () => {
    cancelButton.disabled = true;
    try {
      await requestJson(`/api/runs/${runId}/cancel`, { method: "POST" });
      status.textContent = "cancelling";
      status.className = "run-status large cancelling";
      window.setTimeout(refreshRun, 300);
    } catch (error) {
      errorPanel.textContent = error.message;
      errorPanel.hidden = false;
      cancelButton.disabled = false;
    }
  });
}
