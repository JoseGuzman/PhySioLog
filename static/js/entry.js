// static/js/entry.js

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
    setFieldValue("sleep", decimalHoursToHHMM(entry.sleep_total));
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

function collectEntryPayload() {
    const sleepValue = entry$("sleep")?.value?.trim() || "";
    return {
        date: entry$("date")?.value,
        weight: parseFloat(entry$("weight")?.value) || null,
        body_fat: parseFloat(entry$("bodyFat")?.value) || null,
        calories: parseInt(entry$("calories")?.value, 10) || null,
        training_volume: parseFloat(entry$("trainingVolume")?.value) || null,
        steps: parseInt(entry$("steps")?.value, 10) || null,
        sleep_total: sleepValue || null,
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

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const result = await createOrUpdateEntry(collectEntryPayload());
            alert(result.mode === "updated" ? "Entry updated!" : "Entry added!");
        } catch (err) {
            console.error(err);
            alert("Error adding entry");
        }
    });
}

document.addEventListener("DOMContentLoaded", wireEntryPage);
