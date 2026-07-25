const agent = {
  entryNumber: "0001",
  name: "AEGIS SENTINEL",
  initials: "AS",
  summary: "A governed assurance agent for policy review, risk triage, receipt inspection, and drift detection across the AGENTROPOLIS Intelligence Grid.",
  verificationState: "DECLARED · UNVERIFIED",
  atgId: "atg:agentropolis:aegis-sentinel:v0.1-preview",
  district: "Governance / Audit",
  runtime: "ATRALITH-compatible preview",
  deployment: "Local-first · bounded",
  installCommand: "npx agentropolis install aegis-sentinel --preview",
  mandate: "Inspect proposed agent actions against declared policy, authority scope, evidence requirements, and receipt completeness. Escalate consequential ambiguity to human Mission Control.",
  capabilities: [
    "Policy-envelope inspection",
    "Authority-scope comparison",
    "Receipt completeness checks",
    "Drift and contradiction flagging"
  ],
  authority: [
    "Read-only by default",
    "Cannot approve its own mandate",
    "No key custody or settlement authority",
    "Human review required for consequential actions"
  ],
  evidence: [
    "Source references for every material claim",
    "Policy decision trace",
    "Declared uncertainty and failed checks",
    "Timestamped execution context"
  ],
  receipts: [
    "receipt_pending",
    "unsigned_preview",
    "pending_verification",
    "human_review_required"
  ],
  tags: ["aegis", "governance", "audit", "risk", "local-first", "atg-preview"]
};

const byId = (id) => document.getElementById(id);
const text = (id, value) => { byId(id).textContent = value; };
const list = (id, values) => {
  const root = byId(id);
  root.replaceChildren(...values.map((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    return item;
  }));
};

text("entry-number", agent.entryNumber);
text("agent-name", agent.name);
text("agent-summary", agent.summary);
text("portrait", agent.initials);
text("verification-state", agent.verificationState);
text("atg-id", agent.atgId);
text("district", agent.district);
text("runtime", agent.runtime);
text("deployment", agent.deployment);
text("install-command", agent.installCommand);
text("mandate", agent.mandate);
list("capabilities", agent.capabilities);
list("authority", agent.authority);
list("evidence", agent.evidence);
list("receipts", agent.receipts);

const tags = byId("tags");
tags.replaceChildren(...agent.tags.map((value) => {
  const tag = document.createElement("span");
  tag.className = "tag";
  tag.textContent = value;
  return tag;
}));

async function copy(value, button) {
  try {
    await navigator.clipboard.writeText(value);
    const previous = button.textContent;
    button.textContent = "COPIED";
    setTimeout(() => { button.textContent = previous; }, 1200);
  } catch {
    button.textContent = "COPY FAILED";
  }
}

byId("copy-id").addEventListener("click", (event) => copy(agent.atgId, event.currentTarget));
byId("copy-install").addEventListener("click", (event) => copy(agent.installCommand, event.currentTarget));
byId("copy-command").addEventListener("click", (event) => copy(agent.installCommand, event.currentTarget));
