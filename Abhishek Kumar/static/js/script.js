/* ==========================================================================
   Smart Hospital Navigation — Frontend Logic (v2, interactive)
   - Interactive symptom picker (autocomplete + tags) backed by /symptoms
   - Free-text fallback, matched-symptom feedback from the backend
   - Calls /predict, renders department + confidence + route
   - Interactive SVG hospital map: zoom (buttons + scroll), pan (drag),
     hover tooltips, and the shortest path highlighted in coral
   ========================================================================== */

// Fixed (x, y) coordinates for each node, used only for VISUALIZATION.
// These do not affect the actual Dijkstra calculation on the backend.
const NODE_POSITIONS = {
  "Entrance": [40, 210],
  "Parking": [40, 80],
  "Reception": [165, 210],
  "Pharmacy": [165, 340],
  "Corridor A": [300, 115],
  "Corridor B": [300, 300],
  "Cardiology": [440, 40],
  "Neurology": [440, 115],
  "Orthopedic": [440, 190],
  "Psychiatry": [570, 115],
  "Corridor C": [570, 190],
  "Gastroenterology": [570, 260],
  "Urology": [570, 330],
  "Pediatrics": [440, 330],
  "Dermatology": [440, 260],
  "ENT": [570, 40],
  "Ophthalmology": [440, 390],
  "General Medicine": [300, 390],
};

let hospitalGraph = {};
let allSymptoms = [];           // [{id, label}, ...] loaded from /symptoms
let selectedSymptoms = new Map(); // id -> label

// -------------------------------------------------------------------
// Element refs
// -------------------------------------------------------------------
const symptomSearch = document.getElementById("symptomSearch");
const suggestionList = document.getElementById("suggestionList");
const selectedSymptomsEl = document.getElementById("selectedSymptoms");
const symptomsInput = document.getElementById("symptomsInput");
const predictBtn = document.getElementById("predictBtn");
const errorBox = document.getElementById("errorBox");
const emptyState = document.getElementById("emptyState");
const resultState = document.getElementById("resultState");
const departmentName = document.getElementById("departmentName");
const confidenceFill = document.getElementById("confidenceFill");
const confidenceText = document.getElementById("confidenceText");
const distanceStat = document.getElementById("distanceStat");
const stopsStat = document.getElementById("stopsStat");
const pathList = document.getElementById("pathList");
const matchedSymptomsText = document.getElementById("matchedSymptomsText");
const mapSvg = document.getElementById("mapSvg");
const mapTooltip = document.getElementById("mapTooltip");
const langSelect = document.getElementById("langSelect");

// --------------------------------------------------------------------
// Load hospital graph + symptom vocabulary on page load
// --------------------------------------------------------------------
async function loadHospitalMap() {
  try {
    const res = await fetch("/map");
    const data = await res.json();
    if (data.success) {
      hospitalGraph = data.graph;
      drawMap([]); // draw the base (empty) map immediately
    }
  } catch (err) {
    console.error("Could not load hospital map:", err);
  }
}

async function loadSymptomVocabulary() {
  try {
    const res = await fetch("/symptoms");
    const data = await res.json();
    if (data.success) {
      allSymptoms = data.symptoms;
    }
  } catch (err) {
    console.error("Could not load symptom list:", err);
  }
}

loadHospitalMap();
loadSymptomVocabulary();

// --------------------------------------------------------------------
// Interactive symptom picker: search / suggest / tag
// --------------------------------------------------------------------
symptomSearch.addEventListener("input", () => {
  const query = symptomSearch.value.trim().toLowerCase();
  if (!query) {
    suggestionList.classList.add("hidden");
    suggestionList.innerHTML = "";
    return;
  }

  const matches = allSymptoms
    .filter((s) => !selectedSymptoms.has(s.id))
    .filter((s) => s.label.toLowerCase().includes(query))
    .slice(0, 8);

  if (matches.length === 0) {
    suggestionList.classList.add("hidden");
    suggestionList.innerHTML = "";
    return;
  }

  suggestionList.innerHTML = "";
  matches.forEach((s) => {
    const item = document.createElement("div");
    item.className = "suggestion-item";
    item.textContent = s.label;
    item.addEventListener("click", () => addSymptom(s.id, s.label));
    suggestionList.appendChild(item);
  });
  suggestionList.classList.remove("hidden");
});

document.addEventListener("click", (e) => {
  if (!e.target.closest(".picker-wrap")) {
    suggestionList.classList.add("hidden");
  }
});

function addSymptom(id, label) {
  selectedSymptoms.set(id, label);
  symptomSearch.value = "";
  suggestionList.classList.add("hidden");
  renderSelectedSymptoms();
}

function removeSymptom(id) {
  selectedSymptoms.delete(id);
  renderSelectedSymptoms();
}

function renderSelectedSymptoms() {
  selectedSymptomsEl.innerHTML = "";
  selectedSymptoms.forEach((label, id) => {
    const tag = document.createElement("span");
    tag.className = "symptom-tag";
    tag.innerHTML = `${label} <button type="button" aria-label="Remove">&times;</button>`;
    tag.querySelector("button").addEventListener("click", () => removeSymptom(id));
    selectedSymptomsEl.appendChild(tag);
  });
}

// --------------------------------------------------------------------
// Quick example chips (fills the free-text box)
// --------------------------------------------------------------------
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    symptomsInput.value = chip.dataset.value;
    symptomsInput.focus();
  });
});

// --------------------------------------------------------------------
// Language toggle (English / Hindi) — swaps data-en / data-hi labels
// --------------------------------------------------------------------
langSelect.addEventListener("change", () => {
  const lang = langSelect.value; // 'en' or 'hi'
  document.querySelectorAll("[data-en]").forEach((el) => {
    el.textContent = el.dataset[lang] || el.dataset.en;
  });
});

// --------------------------------------------------------------------
// Error handling helpers
// --------------------------------------------------------------------
function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("hidden");
}
function clearError() {
  errorBox.textContent = "";
  errorBox.classList.add("hidden");
}
function setLoading(isLoading) {
  predictBtn.disabled = isLoading;
  predictBtn.querySelector(".btn-spinner").classList.toggle("hidden", !isLoading);
}

// --------------------------------------------------------------------
// Main predict action
// --------------------------------------------------------------------
async function handlePredict() {
  clearError();

  const symptomsListIds = Array.from(selectedSymptoms.keys());
  const symptomsText = symptomsInput.value.trim();

  if (symptomsListIds.length === 0 && !symptomsText) {
    showError("Please pick at least one symptom or describe your symptoms.");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symptoms_list: symptomsListIds,
        symptoms_text: symptomsText,
      }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      showError(data.error || "Something went wrong. Please try again.");
      return;
    }

    renderResult(data);
  } catch (err) {
    console.error(err);
    showError("Could not reach the server. Is the Flask app running?");
  } finally {
    setLoading(false);
  }
}

predictBtn.addEventListener("click", handlePredict);
symptomsInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handlePredict();
});

// --------------------------------------------------------------------
// Render the prediction + path results
// --------------------------------------------------------------------
function renderResult(data) {
  emptyState.classList.add("hidden");
  resultState.classList.remove("hidden");

  departmentName.textContent = data.department;

  if (data.confidence !== null && data.confidence !== undefined) {
    confidenceFill.style.width = `${data.confidence}%`;
    confidenceText.textContent = `${data.confidence}%`;
  } else {
    confidenceFill.style.width = "100%";
    confidenceText.textContent = "--";
  }

  distanceStat.textContent = data.distance_meters;
  stopsStat.textContent = data.path.length;
  matchedSymptomsText.textContent = data.matched_symptoms.join(", ");

  pathList.innerHTML = "";
  data.path.forEach((stop) => {
    const li = document.createElement("li");
    li.textContent = stop;
    pathList.appendChild(li);
  });

  drawMap(data.path);
}

// --------------------------------------------------------------------
// Interactive map: build/redraw SVG content into a <g> we can pan/zoom
// --------------------------------------------------------------------
const VIEW_W = 620, VIEW_H = 420;
let mapState = { scale: 1, tx: 0, ty: 0 };
let lastHighlightPath = [];

function drawMap(highlightPath = []) {
  lastHighlightPath = highlightPath;
  mapSvg.innerHTML = "";
  const ns = "http://www.w3.org/2000/svg";

  const group = document.createElementNS(ns, "g");
  group.setAttribute("id", "mapContent");
  applyTransform(group);

  const highlightSet = new Set(highlightPath);
  const highlightEdges = new Set();
  for (let i = 0; i < highlightPath.length - 1; i++) {
    highlightEdges.add(`${highlightPath[i]}|${highlightPath[i + 1]}`);
    highlightEdges.add(`${highlightPath[i + 1]}|${highlightPath[i]}`);
  }

  // 1) Draw all edges (base map, faint; highlighted ones in coral)
  for (const [node, neighbors] of Object.entries(hospitalGraph)) {
    const [x1, y1] = NODE_POSITIONS[node] || [0, 0];
    for (const neighbor of Object.keys(neighbors)) {
      const [x2, y2] = NODE_POSITIONS[neighbor] || [0, 0];
      const isHighlighted = highlightEdges.has(`${node}|${neighbor}`);
      const line = document.createElementNS(ns, "line");
      line.setAttribute("x1", x1);
      line.setAttribute("y1", y1);
      line.setAttribute("x2", x2);
      line.setAttribute("y2", y2);
      line.setAttribute("stroke", isHighlighted ? "#FF6B5B" : "#DCE8E7");
      line.setAttribute("stroke-width", isHighlighted ? "4" : "2");
      group.appendChild(line);
    }
  }

  // 2) Draw all nodes on top of the edges, with hover tooltips
  for (const [node, [x, y]] of Object.entries(NODE_POSITIONS)) {
    const isOnPath = highlightSet.has(node);

    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", x);
    circle.setAttribute("cy", y);
    circle.setAttribute("r", node === "Entrance" ? 10 : 7);
    circle.setAttribute("fill", isOnPath ? "#FF6B5B" : "#1D7874");
    circle.setAttribute("stroke", "#fff");
    circle.setAttribute("stroke-width", "2");
    circle.style.cursor = "pointer";

    circle.addEventListener("mouseenter", (e) => showTooltip(node, e));
    circle.addEventListener("mousemove", (e) => showTooltip(node, e));
    circle.addEventListener("mouseleave", hideTooltip);

    group.appendChild(circle);

    const label = document.createElementNS(ns, "text");
    label.setAttribute("x", x);
    label.setAttribute("y", y - 12);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-size", "10.5");
    label.setAttribute("font-family", "Inter, sans-serif");
    label.setAttribute("fill", isOnPath ? "#E85444" : "#5C7278");
    label.setAttribute("font-weight", isOnPath ? "700" : "500");
    label.textContent = node;
    group.appendChild(label);
  }

  mapSvg.appendChild(group);
}

function showTooltip(node, evt) {
  const rect = mapSvg.getBoundingClientRect();
  mapTooltip.textContent = node;
  mapTooltip.style.left = `${evt.clientX - rect.left}px`;
  mapTooltip.style.top = `${evt.clientY - rect.top}px`;
  mapTooltip.classList.add("visible");
}
function hideTooltip() {
  mapTooltip.classList.remove("visible");
}

function applyTransform(el) {
  el.setAttribute(
    "transform",
    `translate(${mapState.tx}, ${mapState.ty}) scale(${mapState.scale})`
  );
}

function redrawTransformOnly() {
  const group = document.getElementById("mapContent");
  if (group) applyTransform(group);
}

// ---- Zoom (buttons + mouse wheel) ----
function zoomBy(factor, pivotX = VIEW_W / 2, pivotY = VIEW_H / 2) {
  const newScale = Math.min(3, Math.max(0.6, mapState.scale * factor));
  // Keep the point under the pivot stable while zooming
  mapState.tx = pivotX - ((pivotX - mapState.tx) * newScale) / mapState.scale;
  mapState.ty = pivotY - ((pivotY - mapState.ty) * newScale) / mapState.scale;
  mapState.scale = newScale;
  redrawTransformOnly();
}

document.getElementById("zoomInBtn").addEventListener("click", () => zoomBy(1.25));
document.getElementById("zoomOutBtn").addEventListener("click", () => zoomBy(0.8));
document.getElementById("resetMapBtn").addEventListener("click", () => {
  mapState = { scale: 1, tx: 0, ty: 0 };
  redrawTransformOnly();
});

mapSvg.addEventListener("wheel", (e) => {
  e.preventDefault();
  const rect = mapSvg.getBoundingClientRect();
  const pivotX = ((e.clientX - rect.left) / rect.width) * VIEW_W;
  const pivotY = ((e.clientY - rect.top) / rect.height) * VIEW_H;
  zoomBy(e.deltaY < 0 ? 1.12 : 0.9, pivotX, pivotY);
}, { passive: false });

// ---- Pan (drag) ----
let isDragging = false;
let dragStart = { x: 0, y: 0 };

mapSvg.addEventListener("mousedown", (e) => {
  isDragging = true;
  dragStart = { x: e.clientX, y: e.clientY };
});
window.addEventListener("mousemove", (e) => {
  if (!isDragging) return;
  const rect = mapSvg.getBoundingClientRect();
  const scaleFactor = VIEW_W / rect.width;
  mapState.tx += (e.clientX - dragStart.x) * scaleFactor;
  mapState.ty += (e.clientY - dragStart.y) * scaleFactor;
  dragStart = { x: e.clientX, y: e.clientY };
  redrawTransformOnly();
});
window.addEventListener("mouseup", () => { isDragging = false; });
