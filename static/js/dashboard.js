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

function decimalHoursToHHMM(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "--";
    let hours = Math.floor(value);
    let minutes = Math.round((value - hours) * 60);
    if (minutes === 60) {
        hours += 1;
        minutes = 0;
    }
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function renderTrendsStats(payload) {
    // Expected payload: { window_days, start_date, end_date, stats: {...} }
    const stats = payload?.stats;
    if (!stats) return;

    for (const key of TRENDS_STAT_FIELDS) {
        const el = $(`stat-${key}`);
        if (!el) continue;
        el.textContent = key === "avg_sleep"
            ? decimalHoursToHHMM(stats[key])
            : formatStatValue(stats[key]);
    }

    const meta = $("windowMeta");
    if (meta) {
        const { start_date, end_date, window_days } = payload || {};
        if (start_date && end_date) {
            let days = window_days;
            if (!days) {
                const start = new Date(`${start_date}T00:00:00`);
                const end = new Date(`${end_date}T00:00:00`);
                if (!Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime())) {
                    days = Math.max(1, Math.round((end - start) / 86400000) + 1);
                }
            }
            meta.textContent = days
                ? `${start_date} → ${end_date} (${days} days)`
                : `${start_date} → ${end_date}`;
        } else {
            const isAllTime = !getSelectedWindowValue();
            if (isAllTime && Array.isArray(CURRENT_WINDOW_ENTRIES) && CURRENT_WINDOW_ENTRIES.length) {
                const sorted = [...CURRENT_WINDOW_ENTRIES].sort((a, b) => new Date(a.date) - new Date(b.date));
                const startDate = sorted[0]?.date;
                const endDate = sorted[sorted.length - 1]?.date;
                if (startDate && endDate) {
                    const start = new Date(`${startDate}T00:00:00`);
                    const end = new Date(`${endDate}T00:00:00`);
                    const days = (!Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime()))
                        ? Math.max(1, Math.round((end - start) / 86400000) + 1)
                        : null;
                    meta.textContent = days
                        ? `${startDate} → ${endDate} (${days} days)`
                        : `${startDate} → ${endDate}`;
                    return;
                }
            }
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

async function loadTrendsStats(
    windowValue = getSelectedWindowValue(),
    requestId = ACTIVE_TRENDS_REQUEST_ID
) {
    // Only run on trends-like pages
    const statsGrid = $("statsGrid");
    const hasTrendsPanel = !!statsGrid || TRENDS_STAT_FIELDS.some((k) => $(`stat-${k}`));
    if (!hasTrendsPanel) return;

    try {
        const payload = await fetchStatsPayload(windowValue);
        if (requestId !== ACTIVE_TRENDS_REQUEST_ID) return;
        renderTrendsStats(payload);
    } catch (err) {
        if (requestId !== ACTIVE_TRENDS_REQUEST_ID) return;
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

/* detects change in windowsSelect in trends.html */
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
    steps: { bar: "#245d39", line: "#fb7185" },
    sleep: { bar: "#534970", line: "#fb923c" },
    calories: { bar: "#475569", line: "#f59e0b" },
    training: { line: "#38bdf8", dots: "#f97316" },
};

const CHART_IDS = ["weightChart", "bodyFatChart", "stepsChart", "sleepChart", "caloriesChart", "trainingVolumeChart"];

const PLOTLY_CONFIG = {
    responsive: true,
    displaylogo: false,
    scrollZoom: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
};

let LATEST_DATE_ISO = null;
let CURRENT_WINDOW_ENTRIES = [];
let ACTIVE_X_RANGE = null;
let IS_SYNCING_ZOOM = false;
let ACTIVE_TRENDS_REQUEST_ID = 0;

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

function calculateAverages(entries) {
    const fields = [
        ["weight", "avg_weight"],
        ["body_fat", "avg_body_fat"],
        ["calories", "avg_calories"],
        ["steps", "avg_steps"],
        ["sleep_total", "avg_sleep"],
    ];

    const stats = {};
    for (const [sourceKey, targetKey] of fields) {
        const values = entries
            .map((e) => e?.[sourceKey])
            .filter((v) => typeof v === "number" && Number.isFinite(v));
        stats[targetKey] = values.length
            ? values.reduce((a, b) => a + b, 0) / values.length
            : null;
    }
    return stats;
}

function filterEntriesByDateRange(entries, xRange) {
    if (!Array.isArray(xRange) || xRange.length !== 2) return entries;
    const start = new Date(xRange[0]);
    const end = new Date(xRange[1]);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return entries;

    return entries.filter((e) => {
        const d = new Date(`${e.date}T00:00:00`);
        return !Number.isNaN(d.getTime()) && d >= start && d <= end;
    });
}

function getRangeFromRelayoutUpdate(update) {
    if (!update || typeof update !== "object") return null;

    if (Array.isArray(update["xaxis.range"]) && update["xaxis.range"].length === 2) {
        return update["xaxis.range"];
    }

    const r0 = update["xaxis.range[0]"];
    const r1 = update["xaxis.range[1]"];
    if (r0 !== undefined && r1 !== undefined) {
        return [r0, r1];
    }

    return null;
}

async function refreshStatsForCurrentView() {
    if (!ACTIVE_X_RANGE) {
        await loadTrendsStats(getSelectedWindowValue());
        return;
    }

    const inRange = filterEntriesByDateRange(CURRENT_WINDOW_ENTRIES, ACTIVE_X_RANGE);
    if (!inRange.length) {
        for (const key of TRENDS_STAT_FIELDS) {
            const el = $(`stat-${key}`);
            if (el) el.textContent = "--";
        }
        const meta = $("windowMeta");
        if (meta) meta.textContent = "No data in selected zoom range";
        return;
    }

    const sorted = [...inRange].sort((a, b) => new Date(a.date) - new Date(b.date));
    const startDate = sorted[0]?.date ?? null;
    const endDate = sorted[sorted.length - 1]?.date ?? null;

    const start = new Date(`${startDate}T00:00:00`);
    const end = new Date(`${endDate}T00:00:00`);
    const spanDays = Math.max(1, Math.round((end - start) / 86400000) + 1);

    renderTrendsStats({
        stats: calculateAverages(inRange),
        start_date: startDate,
        end_date: endDate,
        window_days: spanDays,
    });
}

function wireChartZoomSync() {
    for (const chartId of CHART_IDS) {
        const el = $(chartId);
        if (!el || typeof el.on !== "function" || el.__zoomSyncBound) continue;

        el.on("plotly_relayout", async (update) => {
            if (IS_SYNCING_ZOOM) return;

            const resetRequested = update?.["xaxis.autorange"] === true;
            const nextRange = getRangeFromRelayoutUpdate(update);
            if (!resetRequested && !nextRange) return;

            ACTIVE_X_RANGE = resetRequested ? null : nextRange;

            IS_SYNCING_ZOOM = true;
            try {
                for (const targetId of CHART_IDS) {
                    if (targetId === chartId || !$(targetId)) continue;
                    if (ACTIVE_X_RANGE) {
                        await Plotly.relayout(targetId, { "xaxis.range": ACTIVE_X_RANGE });
                    } else {
                        await Plotly.relayout(targetId, { "xaxis.autorange": true });
                    }
                }
            } catch (err) {
                console.error(err);
            } finally {
                IS_SYNCING_ZOOM = false;
            }

            await refreshStatsForCurrentView();
        });

        el.__zoomSyncBound = true;
    }
}

function windowValueToDays(windowValue) {
    if (!windowValue) return null;
    const m = String(windowValue).trim().toLowerCase().match(/^(\d+)([dmy])$/);
    if (!m) return null;

    const amount = parseInt(m[1], 10);
    const unit = m[2];
    if (!Number.isFinite(amount) || amount <= 0) return null;
    if (unit === "d") return amount;
    if (unit === "m") return amount * 30;
    if (unit === "y") return amount * 365;
    return null;
}

function filterEntriesByWindow(entries, windowValue) {
    const days = windowValueToDays(windowValue);
    if (!days) return entries;

    const end = new Date();
    end.setHours(0, 0, 0, 0);
    const start = new Date(end);
    start.setDate(start.getDate() - days + 1);

    return entries.filter((e) => {
        const d = new Date(`${e.date}T00:00:00`);
        return !Number.isNaN(d.getTime()) && d >= start && d <= end;
    });
}

function getWindowXAxisRange(windowValue) {
    const days = windowValueToDays(windowValue);
    if (!days) return null;

    const end = new Date();
    end.setHours(0, 0, 0, 0);
    const start = new Date(end);
    start.setDate(start.getDate() - days + 1);

    return [
        start.toISOString().slice(0, 10),
        end.toISOString().slice(0, 10),
    ];
}

async function refreshTrendsWindow() {
    const windowValue = getSelectedWindowValue();
    const requestId = ++ACTIVE_TRENDS_REQUEST_ID;
    ACTIVE_X_RANGE = null;
    try {
        await loadCharts(windowValue, requestId);
    } catch (err) {
        if (requestId !== ACTIVE_TRENDS_REQUEST_ID) return;
        console.error(err);
    }

    await loadTrendsStats(windowValue, requestId);
}


// -----------------------------
// Loading Charts with custom windows
// -----------------------------
async function loadCharts(
    windowValue = getSelectedWindowValue(),
    requestId = ACTIVE_TRENDS_REQUEST_ID
) {
    if (!hasAnyElement(CHART_IDS)) return;

    let entries;
    try {
        const hasWindow = windowValue !== null && windowValue !== undefined && windowValue !== "";
        const entriesUrl = hasWindow
            ? `/api/entries?window=${encodeURIComponent(windowValue)}`
            : "/api/entries";
        const payload = await fetchJson(entriesUrl);
        if (requestId !== ACTIVE_TRENDS_REQUEST_ID) return;
        entries = Array.isArray(payload) ? payload : payload?.entries;
        if (!Array.isArray(entries)) return;
    } catch (err) {
        if (requestId !== ACTIVE_TRENDS_REQUEST_ID) return;
        console.error(err);
        return;
    }

    if (requestId !== ACTIVE_TRENDS_REQUEST_ID) return;
    CURRENT_WINDOW_ENTRIES = entries;
    const xAxisRange = getWindowXAxisRange(windowValue);

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
                xaxis: {
                    ...BASE_LAYOUT.xaxis,
                    ...makeXAxis(-30),
                    ...(xAxisRange ? { range: xAxisRange } : {}),
                },
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
                xaxis: {
                    ...BASE_LAYOUT.xaxis,
                    ...makeXAxis(-30),
                    ...(xAxisRange ? { range: xAxisRange } : {}),
                },
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
                    ...(xAxisRange ? { range: xAxisRange } : {}),
                    showspikes: false
                },
            },
            PLOTLY_CONFIG
        );
    }


    // Sleep
    if ($("sleepChart")) {
        const sleepData = entries.map((e) =>
            typeof e.sleep_total_decimal === "number"
                ? e.sleep_total_decimal
                : e.sleep_total
        );
        const sleepMA = calculateMovingAverage(sleepData, 7);

        Plotly.react(
            "sleepChart",
            [
                {
                    x: dates, y: sleepData, name: "Daily Sleep", type: "bar",
                    marker: { color: MYCOLORS.sleep.bar, line: { width: 0 } },
                    customdata: sleepData.map(decimalHoursToHHMM),
                    hovertemplate: "Date: %{x}<br>Sleep: %{customdata}<extra></extra>"
                },
                {
                    x: dates, y: sleepMA, name: "7-Day Average", type: "scatter", mode: "lines",
                    line: { width: 2, color: MYCOLORS.sleep.line },
                    customdata: sleepMA.map(decimalHoursToHHMM),
                    hovertemplate: "Date: %{x}<br>7-Day Avg: %{customdata}<extra></extra>"
                },
            ],
            {
                ...BASE_LAYOUT,
                hovermode: "closest",
                bargap: 0.15,
                yaxis: {
                    ...BASE_LAYOUT.yaxis,
                    title: "Sleep (HH:MM)",
                    tickformat: ",.2f",
                    tickmode: "array",
                    tickvals: [0, 2, 4, 6, 8, 10, 12],
                    ticktext: ["00:00", "02:00", "04:00", "06:00", "08:00", "10:00", "12:00"],
                },
                xaxis: {
                    ...BASE_LAYOUT.xaxis,
                    ...makeXAxis(-30),
                    ...(xAxisRange ? { range: xAxisRange } : {}),
                    showspikes: false
                },
            },
            PLOTLY_CONFIG
        );
    }

    // Calories
    if ($("caloriesChart")) {
        const caloriesData = entries.map((e) => e.calories);
        const caloriesMA = calculateMovingAverage(caloriesData, 7);

        Plotly.react(
            "caloriesChart",
            [
                {
                    x: dates, y: caloriesData, name: "Daily Calories", type: "bar",
                    marker: { color: MYCOLORS.calories.bar, line: { width: 0 } }
                },
                {
                    x: dates, y: caloriesMA, name: "7-Day Average", type: "scatter", mode: "lines",
                    line: { width: 2, color: MYCOLORS.calories.line }
                },
            ],
            {
                ...BASE_LAYOUT,
                hovermode: "closest",
                bargap: 0.15,
                yaxis: { ...BASE_LAYOUT.yaxis, title: "Calories (kcal)" },
                xaxis: {
                    ...BASE_LAYOUT.xaxis,
                    ...makeXAxis(-30),
                    ...(xAxisRange ? { range: xAxisRange } : {}),
                    showspikes: false
                },
            },
            PLOTLY_CONFIG
        );
    }

    // Training volume (dot plot)
    if ($("trainingVolumeChart")) {
        const tvData = entries.map((e) => e.training_volume);
        const tvMA = calculateMovingAverage(tvData, 7);

        Plotly.react(
            "trainingVolumeChart",
            [
                {
                    x: dates, y: tvData, name: "Training Volume", type: "scatter", mode: "markers",
                    marker: { opacity: 0.6, line: { width: 0 }, color: MYCOLORS.training.dots }
                },
                {
                    x: dates, y: tvMA, name: "7-Day Average", type: "scatter", mode: "lines",
                    line: { width: 2, color: MYCOLORS.training.line }
                },
            ],
            {
                ...BASE_LAYOUT,
                hovermode: "x closest",
                yaxis: { ...BASE_LAYOUT.yaxis, title: "Training Volume (kg)" },
                xaxis: {
                    ...BASE_LAYOUT.xaxis,
                    ...makeXAxis(-30),
                    ...(xAxisRange ? { range: xAxisRange } : {}),
                },
            },
            PLOTLY_CONFIG
        );
    }

    wireChartZoomSync();
}

// -----------------------------
// Init: clear flow + no unnecessary work
// -----------------------------
async function init() {
    console.log("🚀 Init starting...");

    // trends-specific controls
    wireWindowSelect(async () => {
        await refreshTrendsWindow();
        // (Optional later) also filter charts by window
    });

    // Load only what the page can show
    await refreshTrendsWindow();

}

document.addEventListener("DOMContentLoaded", () => {
    Promise.resolve(init()).catch((err) => console.error(err));
});
