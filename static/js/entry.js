//-------------------------------------------------------------------------
// static/js/entry.js
//-------------------------------------------------------------------------

function entry$(id) {
    return document.getElementById(id);
}

function setFieldValue(id, value) {
    const el = entry$(id);
    if (!el) return;
    el.value = (value === null || value === undefined || value === "") ? "" : value;
}

function clearEntryFields() {
    setFieldValue("weight", "");
    setFieldValue("bodyFat", "");
    setFieldValue("calories", "");
    setFieldValue("trainingVolume", "");
    setFieldValue("steps", "");
    setFieldValue("sleep", "");
    setFieldValue("observations", "");
}

function fillEntryFields(entry) {
    setFieldValue("weight", entry.weight);
    setFieldValue("bodyFat", entry.body_fat);
    setFieldValue("calories", entry.calories);
    setFieldValue("trainingVolume", entry.training_volume);
    setFieldValue("steps", entry.steps);
    setFieldValue(
        "sleep",
        entry.sleep_total || decimalHoursToHHMM(entry.sleep_total_decimal)
    );
    setFieldValue("observations", entry.observations);
}

function decimalHoursToHHMM(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) return "";
    let hours = Math.floor(value);
    let minutes = Math.round((value - hours) * 60);
    if (minutes === 60) {
        hours += 1;
        minutes = 0;
    }
    return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

async function loadEntryForDate(dateValue) {
    if (!dateValue) {
        clearEntryFields();
        return;
    }

    const url = `/api/entries?date=${encodeURIComponent(dateValue)}`;
    const res = await fetch(url);

    if (res.status === 404) {
        clearEntryFields();
        return;
    }

    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`${url} failed: ${res.status} ${res.statusText} ${text}`);
    }

    const payload = await res.json();
    if (payload?.success && payload?.entry) {
        fillEntryFields(payload.entry);
        return;
    }

    clearEntryFields();
}

function normalizeSleepTotal(value) {
    const raw = String(value ?? "").trim();
    if (!raw || raw === "--") return null;

    const match = raw.match(/^(\d{1,2}):([0-5]\d)$/);
    if (!match) return raw;

    const hours = Number.parseInt(match[1], 10);
    if (hours < 0 || hours > 23) return raw;

    return `${String(hours).padStart(2, "0")}:${match[2]}`;
}

function collectEntryPayload() {
    const sleepValue = normalizeSleepTotal(entry$("sleep")?.value);
    return {
        date: entry$("date")?.value,
        weight: parseFloat(entry$("weight")?.value) || null,
        body_fat: parseFloat(entry$("bodyFat")?.value) || null,
        calories: parseInt(entry$("calories")?.value, 10) || null,
        training_volume: parseFloat(entry$("trainingVolume")?.value) || null,
        steps: parseInt(entry$("steps")?.value, 10) || null,
        sleep_total: sleepValue,
        observations: entry$("observations")?.value?.trim() || null,
    };
}

async function createOrUpdateEntry(payload) {
    const createRes = await fetch("/api/entries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (createRes.ok) {
        return { mode: "created", payload: await createRes.json() };
    }

    if (createRes.status !== 409) {
        const text = await createRes.text().catch(() => "");
        throw new Error(
            `/api/entries POST failed: ${createRes.status} ${createRes.statusText} ${text}`
        );
    }

    const updateRes = await fetch("/api/entries", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!updateRes.ok) {
        const text = await updateRes.text().catch(() => "");
        throw new Error(
            `/api/entries PUT failed: ${updateRes.status} ${updateRes.statusText} ${text}`
        );
    }

    return { mode: "updated", payload: await updateRes.json() };
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

/**
 * Loads recent entries and renders their observations into `#entriesList`.
 * - Fetches `/api/entries`.
 * - Shows an empty state when there are no entries.
 * - Renders up to 7 most recent observation cards.
 * - Shows an error state card if the request fails.
 *
 * Safe-guard:
 * - Returns early when `#entriesList` is missing (idempotent page script behavior).
 */
async function loadLatestObservations() {
    const list = entry$("entriesList");
    if (!list) return;

    try {
        const res = await fetch("/api/entries");
        if (!res.ok) {
            const text = await res.text().catch(() => "");
            throw new Error(`/api/entries failed: ${res.status} ${res.statusText} ${text}`);
        }

        const payload = await res.json();
        const entries = Array.isArray(payload) ? payload : payload?.entries;
        if (!Array.isArray(entries) || entries.length === 0) {
            list.innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">No entries yet</div>
                    <div class="stat-value">--</div>
                </div>
            `;
            return;
        }

        const html = entries.slice(0, 7).map((entry) => {
            const notes = entry?.observations
                ? escapeHtml(entry.observations)
                : '<span style="color:#7a7a7a;">No observations</span>';
            return `
                <div class="stat-card">
                    <div class="stat-label">${escapeHtml(entry.date || "--")}</div>
                    <div style="color: #cfcfcf; line-height: 1.4;">${notes}</div>
                </div>
            `;
        }).join("");

        list.innerHTML = html;
    } catch (err) {
        console.error("Error loading entries list", err);
        list.innerHTML = `
            <div class="stat-card">
                <div class="stat-label">Error loading entries</div>
                <div class="stat-value">--</div>
            </div>
        `;
    }
}

/**
 * Wires all Entry page interactions:
 * - Initializes the date input with today's date when empty.
 * - Loads an existing entry whenever the selected date changes.
 * - Loads the initial date entry and latest observations on page load.
 * - Handles form submission by creating/updating the entry and refreshing observations.
 *
 * Safe-guard:
 * - Exits early when required DOM elements are not present (idempotent page script behavior).
 */
function wireEntryPage() {
    const form = entry$("entryForm");
    const dateEl = entry$("date");
    if (!form || !dateEl) return;

    if (!dateEl.value) {
        dateEl.value = new Date().toISOString().slice(0, 10);
    }

    dateEl.addEventListener("change", () => {
        Promise.resolve(loadEntryForDate(dateEl.value)).catch((err) => {
            console.error("Error loading entry for date", err);
        });
    });

    Promise.resolve(loadEntryForDate(dateEl.value)).catch((err) => {
        console.error("Error loading initial entry", err);
    });
    Promise.resolve(loadLatestObservations()).catch((err) => {
        console.error("Error loading latest observations", err);
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            //const result = await createOrUpdateEntry(collectEntryPayload());
            //alert(result.mode === "updated" ? "Entry updated!" : "Entry added!");
            const payload = collectEntryPayload();
            const result = await createOrUpdateEntry(payload);
            alert(
                result.mode == "updated"
                    ? `Entry for ${payload.date} updated!`
                    : `Entry for ${payload.date} added`
            );
            await loadLatestObservations();
        } catch (err) {
            console.error(err);
            alert("Error adding entry");
        }
    });
}

document.addEventListener("DOMContentLoaded", wireEntryPage);
