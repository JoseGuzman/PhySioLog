// static/js/dashboard.js

console.log("✏️ dashboard.js loaded");

// ------------------------------ 
// Small DOM helpers (page-safe)
// -----------------------------
function $(id) {
    return document.getElementById(id);
}

function hasAnyElement(ids) {
    return ids.some((id) => $(id));
}

// -----------------------------
// Fetch helper
// -----------------------------
async function fetchJson(url, options) {
    const res = await fetch(url, options);
    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`${url} failed: ${res.status} ${res.statusText} ${text}`);
    }
    return res.json();
}

// -----------------------------
// Trends stats panel (trends.html)
// -----------------------------
const TRENDS_STAT_FIELDS = ["avg_weight", "avg_body_fat", "avg_calories", "avg_steps", "avg_sleep"];

function getSelectedWindowValue() {
    const sel = $("windowSelect");
    if (!sel) return null;
    // trends.html uses "" for all-time (per your description)
    return sel.value ?? "";
}

function formatStatValue(v) {
    if (v === null || v === undefined) return "--";
    if (typeof v === "number" && Number.isFinite(v)) return v.toFixed(2);
    return String(v);
}

function renderTrendsStats(payload) {
    // Expected payload: { window_days, start_date, end_date, stats: {...} }
    const stats = payload?.stats;
    if (!stats) return;

    for (const key of TRENDS_STAT_FIELDS) {
        const el = $(`stat-${key}`);
        if (!el) continue;
        el.textContent = formatStatValue(stats[key]);
    }

    const meta = $("windowMeta");
    if (meta) {
        const { start_date, end_date, window_days } = payload || {};
        if (start_date && end_date && window_days) {
            meta.textContent = `${start_date} → ${end_date} (${window_days} days)`;
        } else {
            meta.textContent = "All time";
        }
    }
}

async function fetchStatsPayload(windowValue) {
    // If windowValue is "" => all-time
    const hasWindow = windowValue !== null && windowValue !== undefined && windowValue !== "";
    const url = hasWindow
        ? `/api/stats?window=${encodeURIComponent(windowValue)}`
        : "/api/stats";

    return fetchJson(url);
}

async function loadTrendsStats() {
    // Only run on trends-like pages
    const statsGrid = $("statsGrid");
    const hasTrendsPanel = !!statsGrid || TRENDS_STAT_FIELDS.some((k) => $(`stat-${k}`));
    if (!hasTrendsPanel) return;

    const windowValue = getSelectedWindowValue();

    try {
        const payload = await fetchStatsPayload(windowValue);
        renderTrendsStats(payload);
    } catch (err) {
        // If backend returns 404 "No data available", don't explode the UI
        console.error(err);

        // Best effort: set trends panel to "--"
        for (const key of TRENDS_STAT_FIELDS) {
            const el = $(`stat-${key}`);
            if (el) el.textContent = "--";
        }
        const meta = $("windowMeta");
        if (meta) meta.textContent = "—";
    }
}

function wireWindowSelect(onChange) {
    const sel = $("windowSelect");
    if (!sel) return;

    sel.addEventListener("change", () => {
        // keep handler tiny + safe
        Promise.resolve(onChange?.()).catch((err) => console.error(err));
    });
}

// -----------------------------
// Plotly styling helpers
// -----------------------------
function cssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
}

const CARD_BG = cssVar("--panel", "#252525");

const BASE_LAYOUT = {
    paper_bgcolor: CARD_BG,
    plot_bgcolor: CARD_BG,
    font: { color: "#e0e0e0" },
    hovermode: "x unified",
    showlegend: false,
    margin: { t: 20, r: 20, b: 60, l: 60 },
    xaxis: { gridcolor: "#333", tickcolor: "#888", linecolor: "#888", zerolinecolor: "#2e2e2e", layer: "below traces" },
    yaxis: { gridcolor: "#333", tickcolor: "#888", linecolor: "#888", zerolinecolor: "#2e2e2e", layer: "below traces" },
};

const MYCOLORS = {
    weight: { dots: "#2dd4bf", line: "#fb7185" },
    fat: { dots: "#38bdf8", line: "#fb923c" },
    // Opaque equivalents of 35% alpha over #252525 plot background
    steps: { main: "#22c55e", bar: "#245d39", line: "#fb7185" },
    sleep: { main: "#a78bfa", bar: "#534970", line: "#fb923c" },
};

const CHART_IDS = ["weightChart", "bodyFatChart", "stepsChart", "sleepChart"];

const PLOTLY_CONFIG = {
    responsive: true,
    displaylogo: false,
    scrollZoom: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
};

let LATEST_DATE_ISO = null;

// -----------------------------
// Chart utilities
// -----------------------------
function hexToRgba(hex, alpha = 1) {
    const h = hex.replace("#", "");
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function calculateMovingAverage(data, windowSize = 7) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
        // Use expanding window at the beginning (from start to min(i+1, windowSize))
        const start = Math.max(0, i - windowSize + 1);
        const window = data.slice(start, i + 1).filter((v) => v != null);
        if (window.length === 0) {
            result.push(null);
            continue;
        }
        const avg = window.reduce((a, b) => a + b, 0) / window.length;
        result.push(avg);
    }
    return result;
}

function makeXAxis(angle = -45) {
    return { type: "date", tickangle: angle, dtick: "M1" };
}

// -----------------------------
// Global range controls (optional)
// -----------------------------
function setButtonActive(activeId) {
    const ids = ["btn30", "btn90", "btnAll"];
    ids.forEach((id) => {
        const el = $(id);
        if (!el) return;
        el.style.opacity = id === activeId ? "1" : "0.7";
        el.style.transform = id === activeId ? "translateY(-1px)" : "none";
    });
}

function setGlobalRange(days) {
    if (!hasAnyElement(CHART_IDS)) return;
    if (!LATEST_DATE_ISO) return;

    if (days == null) {
        CHART_IDS.forEach((id) => {
            if ($(id)) Plotly.relayout(id, { "xaxis.autorange": true });
        });
        setButtonActive("btnAll");
        return;
    }

    const end = new Date(LATEST_DATE_ISO + "T00:00:00");
    const start = new Date(end);
    start.setDate(start.getDate() - days);

    const update = {
        "xaxis.range": [start.toISOString().slice(0, 10), end.toISOString().slice(0, 10)],
    };

    CHART_IDS.forEach((id) => {
        if ($(id)) Plotly.relayout(id, update);
    });

    setButtonActive(days === 30 ? "btn30" : "btn90");
}

function wireRangeButtons() {
    const btn30 = $("btn30");
    const btn90 = $("btn90");
    const btnAll = $("btnAll");

    if (btn30) btn30.addEventListener("click", () => setGlobalRange(30));
    if (btn90) btn90.addEventListener("click", () => setGlobalRange(90));
    if (btnAll) btnAll.addEventListener("click", () => setGlobalRange(null));
}

// -----------------------------
// Legacy stats (overview.html - #stats)
// -----------------------------
function renderLegacyStats(stats) {
    const statsEl = $("stats");
    if (!statsEl) return;

    const s = stats || {};
    statsEl.innerHTML = `
    <div class="stat-card">
      <div class="stat-label">Avg Weight</div>
      <div class="stat-value">${s.avg_weight ?? "--"} kg</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Body Fat</div>
      <div class="stat-value">${s.avg_body_fat ?? "--"}%</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Calories</div>
      <div class="stat-value">${s.avg_calories ?? "--"}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Steps</div>
      <div class="stat-value">${s.avg_steps ?? "--"}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Entries</div>
      <div class="stat-value">${s.total_entries ?? "--"}</div>
    </div>
  `;
}

async function loadLegacyStats() {
    const statsEl = $("stats");
    if (!statsEl) return;

    try {
        const payload = await fetchJson("/api/stats");
        const stats = payload.stats ?? payload; // support both shapes
        renderLegacyStats(stats);
    } catch (err) {
        console.error(err);
        renderLegacyStats(null);
    }
}

// -----------------------------
// Synchronized zoom/pan - INTERCEPT Plotly.relayout
// -----------------------------
let isSyncing = false;

function setupSyncZoom() {
    console.log("🔗 Setting up sync zoom...");

    if (!window.Plotly) {
        console.error("Plotly not loaded yet");
        return;
    }

    const originalRelayout = window.Plotly.relayout;
    let relayoutCallCount = 0;

    window.Plotly.relayout = function (div, update, ...args) {
        relayoutCallCount++;
        const chartId = typeof div === "string" ? div : div?.id;

        console.log(`[${relayoutCallCount}] 📊 Plotly.relayout on ${chartId}`, update);

        // Call original
        const result = originalRelayout.call(this, div, update, ...args);

        // Sync if this is one of our charts and we're not already syncing
        const hasAxisUpdate = !!(
            update &&
            (
                update["xaxis.range"] ||
                update["yaxis.range"] ||
                update["xaxis.range[0]"] !== undefined ||
                update["xaxis.range[1]"] !== undefined ||
                update["yaxis.range[0]"] !== undefined ||
                update["yaxis.range[1]"] !== undefined ||
                update["xaxis.autorange"] !== undefined ||
                update["yaxis.autorange"] !== undefined
            )
        );

        if (!isSyncing && chartId && CHART_IDS.includes(chartId) && hasAxisUpdate) {
            console.log(`✨ Syncing triggered by ${chartId}`);
            syncAllCharts(chartId);
        }

        return result;
    };

    console.log("✅ Sync setup complete");

    // Also poll layout changes every 500ms as fallback
    setInterval(() => {
        if (isSyncing) return;

        CHART_IDS.forEach((chartId) => {
            const el = $(chartId);
            if (!el) return;

            // Access layout from Plotly's internal structure
            const layout = el.layout;
            if (!layout) return;

            if (!el._lastLayout) {
                el._lastLayout = JSON.stringify(layout);
                return;
            }

            const current = JSON.stringify(layout);
            if (current !== el._lastLayout) {
                console.log(`🔍 Layout change detected in ${chartId}`);
                el._lastLayout = current;
                syncAllCharts(chartId);
            }
        });
    }, 500);
}

function syncAllCharts(sourceChartId) {
    if (isSyncing) {
        console.log("⏸️  Already syncing, skipping");
        return;
    }

    isSyncing = true;

    setTimeout(() => {
        try {
            const el = $(sourceChartId);
            if (!el || !el.layout) {
                console.log("   No element or layout found");
                isSyncing = false;
                return;
            }

            const layout = el.layout;
            const xRange = layout.xaxis?.range;
            const xAutorange = layout.xaxis?.autorange;

            console.log(`🔄 Syncing from ${sourceChartId}:`, { xRange, xAutorange });

            CHART_IDS.forEach((targetId) => {
                if (targetId === sourceChartId) return;

                console.log(`   → Updating ${targetId}`);
                const update = { "yaxis.autorange": true };
                if (Array.isArray(xRange) && xRange.length === 2) {
                    update["xaxis.range"] = xRange;
                } else if (xAutorange !== undefined) {
                    update["xaxis.autorange"] = xAutorange;
                }
                Plotly.relayout(targetId, update);
            });
        } catch (e) {
            console.error("Sync error:", e);
        } finally {
            isSyncing = false;
        }
    }, 50);
}

// -----------------------------
// Charts
// -----------------------------
async function loadCharts() {
    if (!hasAnyElement(CHART_IDS)) return;

    let entries;
    try {
        entries = await fetchJson("/api/entries");
    } catch (err) {
        console.error(err);
        return;
    }

    // Sort ascending by date (oldest -> newest)
    entries.sort((a, b) => new Date(a.date) - new Date(b.date));

    const dates = entries.map((e) => e.date);
    if (dates.length) LATEST_DATE_ISO = dates[dates.length - 1];

    // Weight
    if ($("weightChart")) {
        const weightData = entries.map((e) => e.weight);
        const weightMA = calculateMovingAverage(weightData, 7);

        Plotly.react(
            "weightChart",
            [
                {
                    x: dates, y: weightData, name: "Daily Weight", type: "scatter", mode: "markers",
                    marker: { opacity: 0.6, line: { width: 0 }, color: MYCOLORS.weight.dots }
                },
                {
                    x: dates, y: weightMA, name: "7-Day Average", type: "scatter", mode: "lines",
                    line: { width: 2, color: MYCOLORS.weight.line }
                },
            ],
            {
                ...BASE_LAYOUT,
                yaxis: { ...BASE_LAYOUT.yaxis, title: "Weight (kg)" },
                xaxis: { ...BASE_LAYOUT.xaxis, ...makeXAxis(-30) },
                hovermode: "x closest",
            },
            PLOTLY_CONFIG
        );
    }

    // Body fat
    if ($("bodyFatChart")) {
        const bfData = entries.map((e) => e.body_fat);
        const bfMA = calculateMovingAverage(bfData, 7);

        Plotly.react(
            "bodyFatChart",
            [
                {
                    x: dates, y: bfData, name: "Daily Body Fat", type: "scatter", mode: "markers",
                    marker: { opacity: 0.6, line: { width: 0 }, color: MYCOLORS.fat.dots }
                },
                {
                    x: dates, y: bfMA, name: "7-Day Average", type: "scatter", mode: "lines",
                    line: { width: 2, color: MYCOLORS.fat.line }
                },
            ],
            {
                ...BASE_LAYOUT,
                yaxis: { ...BASE_LAYOUT.yaxis, title: "Body Fat (%)" },
                xaxis: { ...BASE_LAYOUT.xaxis, ...makeXAxis(-30) },
                hovermode: "x closets",
            },
            PLOTLY_CONFIG
        );
    }

    // Steps
    if ($("stepsChart")) {
        const stepsData = entries.map((e) => e.steps);
        const stepsMA = calculateMovingAverage(stepsData, 7);

        Plotly.react(
            "stepsChart",
            [
                {
                    x: dates, y: stepsData, name: "Daily Steps", type: "bar",
                    marker: { color: MYCOLORS.steps.bar, line: { width: 0 } },
                },
                {
                    x: dates, y: stepsMA, name: "7-Day Average", type: "scatter", mode: "lines",
                    line: { width: 2, color: MYCOLORS.steps.line }
                },
            ],
            {
                ...BASE_LAYOUT,
                hovermode: "closest",
                bargap: 0.15,
                yaxis: { ...BASE_LAYOUT.yaxis, title: "Steps" },
                xaxis: {
                    ...BASE_LAYOUT.xaxis,
                    ...makeXAxis(-30),
                    showspikes: true,
                    spikemode: "across",
                    spikesnap: "cursor"
                },
            },
            PLOTLY_CONFIG
        );
    }


    // Sleep
    if ($("sleepChart")) {
        const sleepData = entries.map((e) => e.sleep_total);
        const sleepMA = calculateMovingAverage(sleepData, 7);

        Plotly.react(
            "sleepChart",
            [
                {
                    x: dates, y: sleepData, name: "Daily Sleep", type: "bar",
                    marker: { color: MYCOLORS.sleep.bar, line: { width: 0 } }
                },
                {
                    x: dates, y: sleepMA, name: "7-Day Average", type: "scatter", mode: "lines",
                    line: { width: 2, color: MYCOLORS.sleep.line }
                },
            ],
            {
                ...BASE_LAYOUT,
                hovermode: "closest",
                bargap: 0.15,
                yaxis: { ...BASE_LAYOUT.yaxis, title: "Sleep (hours)" },
                xaxis: {
                    ...BASE_LAYOUT.xaxis, ...makeXAxis(-30), showspikes: true,
                    spikemode: "across",
                    spikesnap: "cursor"
                },
            },
            PLOTLY_CONFIG
        );
    }
}

// -----------------------------
// Form handling (only if form exists)
// -----------------------------
function wireEntryForm() {
    const form = $("entryForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const data = {
            date: $("date")?.value,
            weight: parseFloat($("weight")?.value) || null,
            body_fat: parseFloat($("bodyFat")?.value) || null,
            calories: parseInt($("calories")?.value) || null,
            steps: parseInt($("steps")?.value) || null,
            sleep_total: parseFloat($("sleep")?.value) || null,
        };

        try {
            await fetchJson("/api/entries", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });

            alert("Entry added!");
            form.reset();

            // Reload only what exists on the page
            await loadLegacyStats();
            await loadTrendsStats();
            await loadCharts();

            if ($("btn90")) setGlobalRange(90);
        } catch (err) {
            console.error(err);
            alert("Error adding entry");
        }
    });
}

// -----------------------------
// Init: clear flow + no unnecessary work
// -----------------------------
async function init() {
    console.log("🚀 Init starting...");

    wireEntryForm();
    wireRangeButtons();
    setupSyncZoom(); // Setup the sync early

    // trends-specific controls
    wireWindowSelect(async () => {
        await loadTrendsStats();
        // (Optional later) also filter charts by window
    });

    // Load only what the page can show
    await loadLegacyStats();  // only if #stats exists
    await loadTrendsStats();  // only if trends stats exist
    await loadCharts();       // only if any chart exists

    // Default view if buttons exist
    if ($("btn90")) setGlobalRange(90);
}

document.addEventListener("DOMContentLoaded", () => {
    Promise.resolve(init()).catch((err) => console.error(err));
});
