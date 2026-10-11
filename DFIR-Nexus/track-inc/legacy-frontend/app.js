// Frontend de Nexus — Módulo 3 (Tracking). Vanilla JS, sin build, habla
// directamente con la API FastAPI del mismo origen.

const API_BASE = ""; // mismo origen: FastAPI sirve este frontend como estático

let lastPreview = null; // guarda el último resultado de /analyze para poder guardarlo después

// ---------- utilidades ----------

function flash(message, type = "info") {
    const container = document.getElementById("flash-container");
    const el = document.createElement("div");
    el.className = `flash flash-${type}`;
    el.textContent = message;
    container.innerHTML = "";
    container.appendChild(el);
    setTimeout(() => el.remove(), 6000);
}

function severityBadge(sev) {
    return `<span class="badge badge-${sevToCss(sev)}">${sev.toUpperCase()}</span>`;
}

function sevToCss(sev) {
    return { baja: "low", media: "medium", alta: "high", critica: "critical" }[sev] || "low";
}

async function apiFetch(path, options = {}) {
    const response = await fetch(API_BASE + path, options);
    if (!response.ok) {
        let detail = response.statusText;
        try {
            const body = await response.json();
            detail = body.detail || JSON.stringify(body);
        } catch (_) { /* no era JSON */ }
        throw new Error(`${response.status}: ${detail}`);
    }
    if (response.status === 204) return null;
    return response.json();
}

// ---------- pestañas ----------

function setupTabs() {
    document.querySelectorAll(".tab-link").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const tab = link.dataset.tab;
            document.querySelectorAll(".tab-link").forEach(l => l.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
            link.classList.add("active");
            document.getElementById(`tab-${tab}`).classList.add("active");
        });
    });
}

// ---------- estado de la API ----------

async function checkApiStatus() {
    const el = document.getElementById("api-status");
    try {
        await apiFetch("/cases/");
        el.textContent = "● API conectada";
        el.className = "api-status ok";
    } catch (e) {
        el.textContent = "● API no disponible";
        el.className = "api-status error";
    }
}

// ---------- casos ----------

async function loadCasesInto(selectEl) {
    try {
        const cases = await apiFetch("/cases/");
        selectEl.innerHTML = cases.map(c => `<option value="${c.id}">#${c.id} — ${c.nombre} (${c.estado})</option>`).join("")
            || `<option value="">Sin casos — créalo en la pestaña "Casos"</option>`;
    } catch (e) {
        flash(`No se pudieron cargar los casos: ${e.message}`, "error");
    }
}

async function refreshCasesTable() {
    try {
        const cases = await apiFetch("/cases/");
        document.getElementById("cases-tbody").innerHTML = cases.map(c => `
            <tr><td>${c.id}</td><td>${c.nombre}</td><td>${c.estado}</td></tr>
        `).join("") || `<tr><td colspan="3" class="text-muted">No hay casos todavía.</td></tr>`;
    } catch (e) {
        flash(`Error al listar casos: ${e.message}`, "error");
    }
}

async function createCase() {
    const input = document.getElementById("input-case-name");
    const nombre = input.value.trim();
    if (!nombre) { flash("Escribe un nombre para el caso.", "error"); return; }

    try {
        await apiFetch(`/cases/?nombre=${encodeURIComponent(nombre)}`, { method: "POST" });
        input.value = "";
        flash("Caso creado correctamente.", "success");
        refreshCasesTable();
        loadCasesInto(document.getElementById("select-case"));
        loadCasesInto(document.getElementById("select-case-events"));
    } catch (e) {
        flash(`No se pudo crear el caso: ${e.message}`, "error");
    }
}

// ---------- analizar log ----------

async function analyzeLog() {
    const caseId = document.getElementById("select-case").value;
    const fileInput = document.getElementById("input-log-file");

    if (!caseId) { flash("Selecciona un caso primero.", "error"); return; }
    if (!fileInput.files.length) { flash("Selecciona un fichero de log.", "error"); return; }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const result = await apiFetch(`/cases/${caseId}/tracking/analyze`, { method: "POST", body: formData });
        lastPreview = { caseId, fuenteLog: fileInput.files[0].name, result };
        renderPreview(result);
        flash(`Análisis completo: ${result.total_eventos} eventos detectados.`, "success");
    } catch (e) {
        flash(`Error al analizar el log: ${e.message}`, "error");
    }
}

function renderPreview(result) {
    document.getElementById("preview-panel").style.display = "block";

    const statsHtml = Object.entries(result.por_severidad).map(([sev, count]) => `
        <div class="stat-card">
            <div class="stat-value">${count}</div>
            <div class="stat-label">${sev.toUpperCase()}</div>
        </div>
    `).join("");
    document.getElementById("preview-stats").innerHTML = statsHtml;

    const rowsHtml = result.eventos.map((ev, idx) => `
        <tr>
            <td>${new Date(ev.hora).toLocaleString()}</td>
            <td class="truncate" title="${escapeHtml(ev.evento)}">${escapeHtml(ev.evento)}</td>
            <td>${severityBadge(ev.severidad)}</td>
            <td class="text-muted">${ev.usuario_detectado || "—"}</td>
            <td class="text-muted">${ev.regla || "—"}</td>
        </tr>
    `).join("");
    document.getElementById("preview-tbody").innerHTML = rowsHtml;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function saveEvents() {
    if (!lastPreview) { flash("Analiza un log primero.", "error"); return; }

    const payload = {
        case_id: parseInt(lastPreview.caseId, 10),
        fuente_log: lastPreview.fuenteLog,
        eventos: lastPreview.result.eventos,
    };

    try {
        const result = await apiFetch(`/cases/${lastPreview.caseId}/tracking/events`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        flash(`✔ ${result.guardados} eventos guardados en tracking_events.`, "success");
        document.getElementById("preview-panel").style.display = "none";
        lastPreview = null;
        document.getElementById("input-log-file").value = "";
    } catch (e) {
        flash(`Error al guardar: ${e.message}`, "error");
    }
}

// ---------- eventos guardados ----------

async function loadSavedEvents() {
    const caseId = document.getElementById("select-case-events").value;
    if (!caseId) { flash("Selecciona un caso primero.", "error"); return; }

    try {
        const events = await apiFetch(`/cases/${caseId}/tracking/events`);
        document.getElementById("events-tbody").innerHTML = events.map(ev => `
            <tr>
                <td>${ev.id}</td>
                <td>${new Date(ev.hora).toLocaleString()}</td>
                <td class="truncate" title="${escapeHtml(ev.evento)}">${escapeHtml(ev.evento)}</td>
                <td>${severityBadge(ev.severidad)}</td>
                <td class="text-muted">${ev.fuente_log || "—"}</td>
                <td class="text-muted">${ev.usuario_detectado || "—"}</td>
            </tr>
        `).join("") || `<tr><td colspan="6" class="text-muted">Sin eventos guardados para este caso.</td></tr>`;
    } catch (e) {
        flash(`Error al listar eventos: ${e.message}`, "error");
    }
}

async function verifyIntegrity() {
    const caseId = document.getElementById("select-case-events").value;
    if (!caseId) { flash("Selecciona un caso primero.", "error"); return; }

    try {
        const result = await apiFetch(`/cases/${caseId}/tracking/verify`);
        flash(result.mensaje, result.ok ? "success" : "error");
    } catch (e) {
        flash(`Error al verificar: ${e.message}`, "error");
    }
}

// ---------- inicialización ----------

document.addEventListener("DOMContentLoaded", () => {
    setupTabs();
    checkApiStatus();

    loadCasesInto(document.getElementById("select-case"));
    loadCasesInto(document.getElementById("select-case-events"));
    refreshCasesTable();

    document.getElementById("btn-refresh-cases").addEventListener("click", () => loadCasesInto(document.getElementById("select-case")));
    document.getElementById("btn-analyze").addEventListener("click", analyzeLog);
    document.getElementById("btn-save-events").addEventListener("click", saveEvents);
    document.getElementById("btn-load-events").addEventListener("click", loadSavedEvents);
    document.getElementById("btn-verify").addEventListener("click", verifyIntegrity);
    document.getElementById("btn-create-case").addEventListener("click", createCase);
});
