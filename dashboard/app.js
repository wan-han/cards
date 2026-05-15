const state = {
  cards: [],
  readers: [],
};

const api = {
  async get(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`GET ${path} failed`);
    return response.json();
  },
  async post(path, body) {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`POST ${path} failed`);
    return response.json();
  },
  async patch(path, body) {
    const response = await fetch(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error(`PATCH ${path} failed`);
    return response.json();
  },
};

function badge(text, type) {
  return `<span class="badge ${type}">${text}</span>`;
}

function formatTime(value) {
  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function renderSelects() {
  const cardSelect = document.querySelector("#scan-card");
  const readerSelect = document.querySelector("#scan-reader");
  const newCardReaders = document.querySelector("#new-card-readers");

  cardSelect.innerHTML = state.cards
    .map((card) => `<option value="${card.card_id}">${card.card_id} - ${card.holder}</option>`)
    .join("");

  readerSelect.innerHTML = state.readers
    .map((reader) => `<option value="${reader.reader_id}">${reader.name}</option>`)
    .join("");

  newCardReaders.innerHTML = state.readers
    .map((reader) => `<option value="${reader.reader_id}">${reader.name}</option>`)
    .join("");
}

function renderCards() {
  const body = document.querySelector("#cards-body");
  body.innerHTML = state.cards
    .map((card) => {
      const nextStatus = card.status === "active" ? "inactive" : "active";
      return `
        <tr>
          <td><strong>${card.card_id}</strong></td>
          <td>${card.holder}</td>
          <td>${card.role}</td>
          <td>${badge(card.status, card.status)}</td>
          <td class="muted">${card.allowed_readers.join(", ") || "None"}</td>
          <td>
            <button class="secondary" data-toggle="${card.card_id}" data-status="${nextStatus}">
              ${nextStatus === "active" ? "Activate" : "Revoke"}
            </button>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderReaders() {
  const grid = document.querySelector("#reader-grid");
  grid.innerHTML = state.readers
    .map(
      (reader) => `
        <article class="reader-card">
          <strong>${reader.name}</strong>
          <span>${reader.reader_id}</span>
          <span>${reader.location || "No location"}</span>
          ${badge(reader.action_type, "active")}
        </article>
      `,
    )
    .join("");
}

async function renderEvents() {
  const events = await api.get("/events");
  const body = document.querySelector("#events-body");
  body.innerHTML =
    events
      .map(
        (event) => `
          <tr>
            <td>${formatTime(event.ts)}</td>
            <td>${event.card_id}</td>
            <td>${event.reader_id}</td>
            <td>${badge(event.result, event.result)}</td>
            <td class="muted">${event.reason}</td>
          </tr>
        `,
      )
      .join("") || `<tr><td colspan="5" class="muted">No events yet.</td></tr>`;
}

async function loadDashboard() {
  const [health, cards, readers] = await Promise.all([
    api.get("/health"),
    api.get("/cards"),
    api.get("/readers"),
  ]);

  state.cards = cards;
  state.readers = readers;

  document.querySelector("#api-status").textContent = `API ${health.status}`;
  document.querySelector("#api-status").classList.add("online");

  renderSelects();
  renderCards();
  renderReaders();
  await renderEvents();
}

document.querySelector("#scan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const resultBox = document.querySelector("#scan-result");
  const payload = {
    card_id: document.querySelector("#scan-card").value,
    reader_id: document.querySelector("#scan-reader").value,
  };

  const result = await api.post("/scan", payload);
  resultBox.className = `scan-result ${result.result}`;
  resultBox.textContent = `${result.result.toUpperCase()}: ${result.action} - ${result.reason}`;
  await renderEvents();
});

document.querySelector("#cards-body").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-toggle]");
  if (!button) return;

  await api.patch(`/cards/${button.dataset.toggle}`, {
    status: button.dataset.status,
  });
  await loadDashboard();
});

document.querySelector("#card-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const readerSelect = document.querySelector("#new-card-readers");
  const allowed_readers = Array.from(readerSelect.selectedOptions).map(
    (option) => option.value,
  );

  await api.post("/cards", {
    card_id: document.querySelector("#new-card-id").value.trim(),
    holder: document.querySelector("#new-card-holder").value.trim(),
    role: document.querySelector("#new-card-role").value,
    status: "active",
    allowed_readers,
  });

  event.target.reset();
  await loadDashboard();
});

document.querySelector("#reader-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  await api.post("/readers", {
    reader_id: document.querySelector("#new-reader-id").value.trim(),
    name: document.querySelector("#new-reader-name").value.trim(),
    location: document.querySelector("#new-reader-location").value.trim(),
    action_type: document.querySelector("#new-reader-action").value,
    status: "active",
  });

  event.target.reset();
  await loadDashboard();
});

document.querySelector("#refresh").addEventListener("click", loadDashboard);

loadDashboard().catch((error) => {
  document.querySelector("#api-status").textContent = "API offline";
  document.querySelector("#scan-result").textContent = error.message;
});
