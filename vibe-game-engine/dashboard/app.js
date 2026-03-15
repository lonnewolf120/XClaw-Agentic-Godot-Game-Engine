const kpiGrid = document.getElementById("kpi-grid");
const agentGrid = document.getElementById("agent-grid");
const commandGrid = document.getElementById("command-grid");
const jobsList = document.getElementById("jobs-list");
const runList = document.getElementById("run-list");
const lastUpdated = document.getElementById("last-updated");

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function renderKpis(kpis) {
  const entries = [
    ["Benchmark Success", `${Math.round((kpis.benchmark_success_rate || 0) * 100)}%`],
    ["Prompts", String(kpis.benchmark_total_prompts || 0)],
    ["Needs-Human Queue", String(kpis.needs_human_queue_items || 0)],
    ["Triage Batches", String(kpis.triage_batches || 0)],
  ];
  kpiGrid.innerHTML = entries
    .map(
      ([label, value]) =>
        `<article class="kpi-card"><span class="meta">${label}</span><span class="value">${value}</span></article>`
    )
    .join("");
}

function renderAgents(agents) {
  agentGrid.innerHTML = agents
    .map(
      (agent) =>
        `<article class="agent-card"><strong>${agent.name}</strong><div class="agent-state state-${agent.state}">${agent.state}</div></article>`
    )
    .join("");
}

async function runCommand(commandId) {
  const response = await fetch("/api/commands/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command_id: commandId }),
  });
  if (!response.ok) {
    throw new Error(`Command failed: ${response.status}`);
  }
}

function renderCommands(commands) {
  commandGrid.innerHTML = commands
    .map(
      (cmd) =>
        `<article class="command-card"><strong>${cmd.label}</strong><button class="cmd-btn" data-cmd="${cmd.id}">Run</button></article>`
    )
    .join("");

  commandGrid.querySelectorAll(".cmd-btn").forEach((button) => {
    button.addEventListener("click", async () => {
      const commandId = button.getAttribute("data-cmd");
      button.disabled = true;
      try {
        await runCommand(commandId);
      } catch (error) {
        alert(String(error));
      } finally {
        button.disabled = false;
      }
    });
  });
}

function renderJobs(jobs) {
  if (!jobs.length) {
    jobsList.innerHTML = '<article class="job-card meta">No command jobs yet.</article>';
    return;
  }

  jobsList.innerHTML = jobs
    .slice(0, 12)
    .map(
      (job) =>
        `<article class="job-card">
          <div><strong>${job.command_id}</strong></div>
          <div class="status status-${job.status}">${job.status}</div>
          <div class="meta">started: ${job.started_at_utc}</div>
          <div class="meta">code: ${job.return_code === null ? "-" : job.return_code}</div>
        </article>`
    )
    .join("");
}

function renderRuns(runs) {
  if (!runs.length) {
    runList.innerHTML = '<article class="run-card meta">No runs discovered.</article>';
    return;
  }

  runList.innerHTML = runs
    .map(
      (run) =>
        `<article class="run-card"><strong>${run.run_id}</strong><div class="meta">${run.state}</div><div class="meta">${run.path}</div></article>`
    )
    .join("");
}

async function refresh() {
  try {
    const [overview, jobsPayload] = await Promise.all([getJson("/api/overview"), getJson("/api/jobs")]);
    renderKpis(overview.kpis || {});
    renderAgents(overview.agents || []);
    renderCommands(overview.commands || []);
    renderRuns(overview.recent_runs || []);
    renderJobs(jobsPayload.jobs || []);
    lastUpdated.textContent = `Telemetry synced ${overview.timestamp_utc}`;
  } catch (error) {
    lastUpdated.textContent = `Sync error: ${String(error)}`;
  }
}

refresh();
setInterval(refresh, 3000);