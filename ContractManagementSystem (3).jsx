import { useState, useEffect } from "react";

// ─── Mock Data ───────────────────────────────────────────────────────────────
const CONTRACTS = [
  { id: "C-001", name: "Master Services Agreement – Accenture", vendor: "Accenture", expiry: "2025-06-15", redlines: 3, version: "v2.1", risk: "High", status: "Active", uploaded: "2024-01-10", clauses: 28 },
  { id: "C-002", name: "Software License Agreement – Oracle", vendor: "Oracle Corp", expiry: "2025-07-20", redlines: 1, version: "v1.0", risk: "Medium", status: "Active", uploaded: "2024-02-14", clauses: 15 },
  { id: "C-003", name: "Consulting Agreement – Deloitte", vendor: "Deloitte", expiry: "2024-12-31", redlines: 0, version: "v3.0", risk: "Low", status: "Expired", uploaded: "2022-12-01", clauses: 20 },
  { id: "C-004", name: "NDA – TechPartners Inc", vendor: "TechPartners", expiry: "2025-08-30", redlines: 2, version: "v1.2", risk: "Medium", status: "Active", uploaded: "2024-03-05", clauses: 8 },
  { id: "C-005", name: "Cloud Services Agreement – AWS", vendor: "Amazon Web Services", expiry: "2025-05-28", redlines: 5, version: "v1.0", risk: "High", status: "Active", uploaded: "2024-04-18", clauses: 40 },
  { id: "C-006", name: "Support Contract – Microsoft", vendor: "Microsoft", expiry: "2025-06-10", redlines: 0, version: "v2.0", risk: "Low", status: "Active", uploaded: "2023-06-01", clauses: 12 },
  { id: "C-007", name: "Vendor Agreement – Infosys", vendor: "Infosys Ltd", expiry: "2024-11-15", redlines: 4, version: "v1.5", risk: "High", status: "Expired", uploaded: "2023-11-01", clauses: 32 },
  { id: "C-008", name: "SaaS Agreement – Salesforce", vendor: "Salesforce", expiry: "2025-09-01", redlines: 1, version: "v1.0", risk: "Low", status: "Active", uploaded: "2024-05-12", clauses: 18 },
];

const CLAUSES = [
  { id: "CL-001", name: "Liability Clause", category: "Liability", risk: "High", version: "v2.0", status: "Approved" },
  { id: "CL-002", name: "Payment Terms", category: "Finance", risk: "Medium", version: "v1.3", status: "Approved" },
  { id: "CL-003", name: "Indemnification", category: "Legal", risk: "High", version: "v1.0", status: "Pending" },
  { id: "CL-004", name: "Termination Clause", category: "Operational", risk: "Medium", version: "v1.1", status: "Approved" },
  { id: "CL-005", name: "Confidentiality", category: "Legal", risk: "Low", version: "v3.0", status: "Approved" },
];

const ACTIVITIES = [
  { action: "Contract uploaded", contract: "SaaS Agreement – Salesforce", user: "Priya Sharma", time: "2 min ago", type: "upload" },
  { action: "Redline accepted", contract: "Master Services Agreement – Accenture", user: "Ravi Kumar", time: "25 min ago", type: "redline" },
  { action: "Expiry alert sent", contract: "Cloud Services Agreement – AWS", user: "System", time: "1 hr ago", type: "alert" },
  { action: "Comparison exported", contract: "Software License – Oracle vs NDA", user: "Anjali Rao", time: "3 hr ago", type: "compare" },
  { action: "SharePoint sync", contract: "All Contracts", user: "System", time: "6 hr ago", type: "sync" },
];

const AUDIT_LOGS = [
  { id: 1, user: "Priya Sharma", action: "Uploaded Contract", target: "SaaS Agreement – Salesforce", time: "2025-05-15 09:12", ip: "192.168.1.101" },
  { id: 2, user: "Ravi Kumar", action: "Accepted Redline", target: "MSA – Accenture Cl. 7.2", time: "2025-05-15 08:47", ip: "192.168.1.102" },
  { id: 3, user: "System", action: "Sent Expiry Alert", target: "AWS Cloud Services", time: "2025-05-15 08:00", ip: "Internal" },
  { id: 4, user: "Anjali Rao", action: "Exported Report", target: "Oracle vs NDA Comparison", time: "2025-05-14 17:35", ip: "192.168.1.103" },
  { id: 5, user: "Admin", action: "Added User", target: "kiran.mehta@org.com", time: "2025-05-14 10:20", ip: "192.168.1.100" },
];

const USERS = [
  { id: 1, name: "Priya Sharma", email: "priya.sharma@org.com", role: "Contract Manager", status: "Active" },
  { id: 2, name: "Ravi Kumar", email: "ravi.kumar@org.com", role: "Legal Reviewer", status: "Active" },
  { id: 3, name: "Anjali Rao", email: "anjali.rao@org.com", role: "Admin", status: "Active" },
  { id: 4, name: "Kiran Mehta", email: "kiran.mehta@org.com", role: "Viewer", status: "Inactive" },
];

const today = new Date("2025-05-15");
const daysUntil = (dateStr) => Math.ceil((new Date(dateStr) - today) / 86400000);

// ─── Helpers ─────────────────────────────────────────────────────────────────
const RiskBadge = ({ risk }) => {
  const colors = { High: "#ef4444", Medium: "#f59e0b", Low: "#22c55e" };
  return (
    <span style={{ background: colors[risk] + "22", color: colors[risk], padding: "2px 10px", borderRadius: 99, fontSize: 12, fontWeight: 700, border: `1px solid ${colors[risk]}44` }}>
      {risk}
    </span>
  );
};

const StatusBadge = ({ status }) => {
  const colors = { Active: "#22c55e", Expired: "#ef4444", Pending: "#f59e0b", Approved: "#22c55e", Inactive: "#6b7280" };
  return (
    <span style={{ background: colors[status] + "22", color: colors[status], padding: "2px 10px", borderRadius: 99, fontSize: 12, fontWeight: 700, border: `1px solid ${colors[status]}44` }}>
      {status}
    </span>
  );
};

// ─── Icons (inline SVG) ──────────────────────────────────────────────────────
const Icon = ({ name, size = 18 }) => {
  const icons = {
    dashboard: <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>,
    contracts: <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z"/>,
    clauses: <path d="M9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm2-7h-1V2h-2v2H8V2H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/>,
    redline: <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>,
    compare: <path d="M9.01 14H2v2h7.01v3L13 15l-3.99-4v3zm5.98-1v-3H22V8h-7.01V5L11 9l3.99 4z"/>,
    sharepoint: <path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/>,
    audit: <path d="M13 2.05V4.07c3.39.49 6 3.39 6 6.93 0 3.21-1.81 6-4.72 7.28L13 17v2.05c4.23-.49 7.5-4.06 7.5-8.98C20.5 5.43 17.18 2.58 13 2.05zM11 2.05C6.82 2.58 3.5 5.43 3.5 10.07c0 4.92 3.27 8.49 7.5 8.98V17l-1.28 1.28C6.81 17 5 14.21 5 11c0-3.54 2.61-6.44 6-6.93V2.05z"/>,
    users: <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>,
    upload: <path d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z"/>,
    search: <path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>,
    bell: <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>,
    alert: <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>,
    check: <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>,
    close: <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>,
    sync: <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>,
    export: <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>,
  };
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      {icons[name]}
    </svg>
  );
};

// ─── Modal ────────────────────────────────────────────────────────────────────
const Modal = ({ title, onClose, children }) => (
  <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.65)", zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
    <div style={{ background: "#0f1117", border: "1px solid #1e2333", borderRadius: 16, width: "100%", maxWidth: 600, maxHeight: "85vh", overflow: "auto", boxShadow: "0 24px 80px rgba(0,0,0,0.5)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 24px", borderBottom: "1px solid #1e2333" }}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#e2e8f0" }}>{title}</h2>
        <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "#64748b", padding: 4 }}><Icon name="close" /></button>
      </div>
      <div style={{ padding: 24 }}>{children}</div>
    </div>
  </div>
);

// ─── Stat Card ────────────────────────────────────────────────────────────────
const StatCard = ({ label, value, sub, icon, accent }) => (
  <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: "20px 22px", display: "flex", flexDirection: "column", gap: 6, position: "relative", overflow: "hidden" }}>
    <div style={{ position: "absolute", top: 0, right: 0, width: 80, height: 80, background: `radial-gradient(circle at 80% 20%, ${accent}22, transparent 70%)` }} />
    <div style={{ color: accent, marginBottom: 4 }}><Icon name={icon} size={22} /></div>
    <div style={{ fontSize: 28, fontWeight: 800, color: "#f1f5f9", letterSpacing: -1 }}>{value}</div>
    <div style={{ fontSize: 13, color: "#94a3b8", fontWeight: 500 }}>{label}</div>
    {sub && <div style={{ fontSize: 11, color: accent, fontWeight: 600 }}>{sub}</div>}
  </div>
);

// ─── Sidebar ──────────────────────────────────────────────────────────────────
const NAV = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "contracts", label: "Contracts", icon: "contracts" },
  { id: "clauses", label: "Clause Repository", icon: "clauses" },
  { id: "redline", label: "Redline Engine", icon: "redline" },
  { id: "compare", label: "Contract Comparison", icon: "compare" },
  { id: "sharepoint", label: "SharePoint", icon: "sharepoint" },
  { id: "audit", label: "Audit Logs", icon: "audit" },
  { id: "users", label: "User Management", icon: "users" },
];

const Sidebar = ({ active, setActive }) => (
  <aside style={{ width: 240, minHeight: "100vh", background: "#070a10", borderRight: "1px solid #1e2333", display: "flex", flexDirection: "column", position: "fixed", left: 0, top: 0, bottom: 0, zIndex: 50 }}>
    <div style={{ padding: "28px 20px 24px", borderBottom: "1px solid #1e2333" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 34, height: 34, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon name="contracts" size={18} />
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 800, color: "#e2e8f0", letterSpacing: 0.5 }}>ContractOS</div>
          <div style={{ fontSize: 10, color: "#6366f1", fontWeight: 600 }}>POC v1.0</div>
        </div>
      </div>
    </div>
    <nav style={{ padding: "16px 12px", flex: 1 }}>
      {NAV.map(n => (
        <button key={n.id} onClick={() => setActive(n.id)}
          style={{ width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 10, border: "none", cursor: "pointer", marginBottom: 2, background: active === n.id ? "linear-gradient(90deg, #6366f122, #8b5cf611)" : "transparent", color: active === n.id ? "#a5b4fc" : "#64748b", fontWeight: active === n.id ? 700 : 500, fontSize: 13, textAlign: "left", transition: "all .15s", borderLeft: active === n.id ? "2px solid #6366f1" : "2px solid transparent" }}>
          <Icon name={n.icon} size={16} />
          {n.label}
        </button>
      ))}
    </nav>
    <div style={{ padding: "16px 20px", borderTop: "1px solid #1e2333" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg, #6366f1, #ec4899)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 700, color: "#fff" }}>A</div>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#cbd5e1" }}>Anjali Rao</div>
          <div style={{ fontSize: 11, color: "#475569" }}>Admin</div>
        </div>
      </div>
    </div>
  </aside>
);

// ─── Dashboard View ───────────────────────────────────────────────────────────
const DashboardView = ({ contracts, setActive, setUploadOpen }) => {
  const active = contracts.filter(c => c.status === "Active").length;
  const expired = contracts.filter(c => c.status === "Expired").length;
  const expiring30 = contracts.filter(c => c.status === "Active" && daysUntil(c.expiry) <= 30).length;
  const highRisk = contracts.filter(c => c.risk === "High" && c.status === "Active").length;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>Contract Management Dashboard</h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b" }}>Centralized visibility across your contract lifecycle</p>
        </div>
        <button onClick={() => setUploadOpen(true)} style={{ display: "flex", alignItems: "center", gap: 8, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 10, padding: "10px 18px", cursor: "pointer", fontWeight: 700, fontSize: 13 }}>
          <Icon name="upload" size={16} /> Quick Upload
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 14, marginBottom: 24 }}>
        <StatCard label="Total Contracts" value={contracts.length} icon="contracts" accent="#6366f1" />
        <StatCard label="Active Contracts" value={active} icon="check" accent="#22c55e" />
        <StatCard label="Expired Contracts" value={expired} icon="close" accent="#ef4444" />
        <StatCard label="Expiring in 30 Days" value={expiring30} sub="Needs attention" icon="bell" accent="#f59e0b" />
        <StatCard label="High Risk Redlines" value={highRisk} sub="Review required" icon="alert" accent="#ef4444" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
        {/* Expiring Soon */}
        <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: "0 0 16px", fontSize: 14, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>⚠ Expiring Soon</h3>
          {contracts.filter(c => c.status === "Active" && daysUntil(c.expiry) <= 90).sort((a, b) => daysUntil(a.expiry) - daysUntil(b.expiry)).map(c => {
            const days = daysUntil(c.expiry);
            const color = days <= 30 ? "#ef4444" : days <= 60 ? "#f59e0b" : "#eab308";
            return (
              <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid #1e233344" }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{c.name.length > 35 ? c.name.slice(0, 35) + "…" : c.name}</div>
                  <div style={{ fontSize: 11, color: "#64748b" }}>{c.vendor}</div>
                </div>
                <span style={{ background: color + "22", color, border: `1px solid ${color}44`, borderRadius: 99, padding: "3px 10px", fontSize: 11, fontWeight: 700, whiteSpace: "nowrap" }}>{days}d left</span>
              </div>
            );
          })}
        </div>

        {/* Recent Uploads */}
        <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 20 }}>
          <h3 style={{ margin: "0 0 16px", fontSize: 14, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>📁 Recent Uploads</h3>
          {[...contracts].sort((a, b) => new Date(b.uploaded) - new Date(a.uploaded)).slice(0, 5).map(c => (
            <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid #1e233344" }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{c.name.length > 35 ? c.name.slice(0, 35) + "…" : c.name}</div>
                <div style={{ fontSize: 11, color: "#64748b" }}>{c.uploaded}</div>
              </div>
              <RiskBadge risk={c.risk} />
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 20 }}>
        <h3 style={{ margin: "0 0 16px", fontSize: 14, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: 1 }}>🕐 Recent Activity</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {ACTIVITIES.map((a, i) => {
            const icons = { upload: "upload", redline: "redline", alert: "bell", compare: "compare", sync: "sync" };
            const colors = { upload: "#6366f1", redline: "#8b5cf6", alert: "#f59e0b", compare: "#22c55e", sync: "#06b6d4" };
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: colors[a.type] + "22", display: "flex", alignItems: "center", justifyContent: "center", color: colors[a.type], flexShrink: 0 }}>
                  <Icon name={icons[a.type]} size={15} />
                </div>
                <div style={{ flex: 1 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{a.action} </span>
                  <span style={{ fontSize: 13, color: "#94a3b8" }}>— {a.contract}</span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 11, color: "#6366f1", fontWeight: 600 }}>{a.user}</div>
                  <div style={{ fontSize: 11, color: "#475569" }}>{a.time}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ─── Contracts View ───────────────────────────────────────────────────────────
const ContractsView = ({ contracts, setContracts }) => {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(null);
  const PER_PAGE = 5;

  const filtered = contracts.filter(c => {
    const matchSearch = c.name.toLowerCase().includes(search.toLowerCase()) || c.vendor.toLowerCase().includes(search.toLowerCase());
    const matchFilter = filter === "All" || c.status === filter || c.risk === filter;
    return matchSearch && matchFilter;
  });
  const pages = Math.ceil(filtered.length / PER_PAGE);
  const paginated = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div>
      {selected && (
        <Modal title={selected.name} onClose={() => setSelected(null)}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            {[["Contract ID", selected.id], ["Vendor", selected.vendor], ["Expiry Date", selected.expiry], ["Version", selected.version], ["Status", selected.status], ["Risk Level", selected.risk], ["Redlines", selected.redlines], ["Clauses", selected.clauses], ["Uploaded", selected.uploaded]].map(([k, v]) => (
              <div key={k} style={{ background: "#070a10", borderRadius: 10, padding: 14 }}>
                <div style={{ fontSize: 11, color: "#475569", fontWeight: 600, marginBottom: 4 }}>{k}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{v}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20 }}>
            <div style={{ fontSize: 11, color: "#475569", fontWeight: 600, marginBottom: 8 }}>VERSION HISTORY</div>
            {["v1.0 — Initial", "v1.1 — Redline updates", selected.version + " — Current"].map((v, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "1px solid #1e2333" }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: i === 2 ? "#6366f1" : "#1e2333" }} />
                <span style={{ fontSize: 13, color: i === 2 ? "#a5b4fc" : "#64748b" }}>{v}</span>
              </div>
            ))}
          </div>
        </Modal>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>All Contracts</h1>
        <div style={{ display: "flex", gap: 8 }}>
          {["All", "Active", "Expired", "High", "Medium", "Low"].map(f => (
            <button key={f} onClick={() => { setFilter(f); setPage(1); }}
              style={{ padding: "6px 14px", borderRadius: 8, border: `1px solid ${filter === f ? "#6366f1" : "#1e2333"}`, background: filter === f ? "#6366f122" : "transparent", color: filter === f ? "#a5b4fc" : "#64748b", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>
              {f}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 10, padding: "10px 14px", marginBottom: 16 }}>
        <Icon name="search" size={16} />
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search contracts by name or vendor…"
          style={{ border: "none", background: "transparent", color: "#e2e8f0", fontSize: 13, flex: 1, outline: "none" }} />
      </div>

      <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#070a10" }}>
              {["ID", "Contract Name", "Vendor", "Expiry", "Redlines", "Version", "Risk", "Status", "Actions"].map(h => (
                <th key={h} style={{ padding: "12px 14px", textAlign: "left", fontSize: 11, color: "#475569", fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.5, borderBottom: "1px solid #1e2333" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((c, i) => (
              <tr key={c.id} style={{ borderBottom: "1px solid #1e233344", background: i % 2 === 0 ? "transparent" : "#ffffff04" }}>
                <td style={{ padding: "12px 14px", fontSize: 12, color: "#6366f1", fontWeight: 700 }}>{c.id}</td>
                <td style={{ padding: "12px 14px", fontSize: 13, color: "#e2e8f0", fontWeight: 600, maxWidth: 200 }}>{c.name}</td>
                <td style={{ padding: "12px 14px", fontSize: 12, color: "#94a3b8" }}>{c.vendor}</td>
                <td style={{ padding: "12px 14px", fontSize: 12, color: daysUntil(c.expiry) < 60 && c.status === "Active" ? "#f59e0b" : "#94a3b8" }}>{c.expiry}</td>
                <td style={{ padding: "12px 14px", fontSize: 13, color: c.redlines > 0 ? "#ef4444" : "#22c55e", fontWeight: 700, textAlign: "center" }}>{c.redlines}</td>
                <td style={{ padding: "12px 14px", fontSize: 12, color: "#64748b" }}>{c.version}</td>
                <td style={{ padding: "12px 14px" }}><RiskBadge risk={c.risk} /></td>
                <td style={{ padding: "12px 14px" }}><StatusBadge status={c.status} /></td>
                <td style={{ padding: "12px 14px" }}>
                  <button onClick={() => setSelected(c)} style={{ background: "#6366f122", border: "1px solid #6366f144", borderRadius: 6, padding: "4px 10px", color: "#a5b4fc", cursor: "pointer", fontSize: 11, fontWeight: 700 }}>View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", borderTop: "1px solid #1e2333" }}>
          <span style={{ fontSize: 12, color: "#475569" }}>Showing {Math.min((page - 1) * PER_PAGE + 1, filtered.length)}–{Math.min(page * PER_PAGE, filtered.length)} of {filtered.length}</span>
          <div style={{ display: "flex", gap: 6 }}>
            {Array.from({ length: pages }, (_, i) => (
              <button key={i} onClick={() => setPage(i + 1)}
                style={{ width: 28, height: 28, borderRadius: 6, border: `1px solid ${page === i + 1 ? "#6366f1" : "#1e2333"}`, background: page === i + 1 ? "#6366f122" : "transparent", color: page === i + 1 ? "#a5b4fc" : "#64748b", cursor: "pointer", fontSize: 12, fontWeight: 700 }}>
                {i + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Clause Repository View ───────────────────────────────────────────────────
const ClauseView = () => {
  const [clauses, setClauses] = useState(CLAUSES);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", category: "Legal", risk: "Medium" });

  const add = () => {
    setClauses([...clauses, { id: `CL-00${clauses.length + 1}`, ...form, version: "v1.0", status: "Pending" }]);
    setAdding(false);
    setForm({ name: "", category: "Legal", risk: "Medium" });
  };

  return (
    <div>
      {adding && (
        <Modal title="Add New Clause" onClose={() => setAdding(false)}>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[["Clause Name", "name", "text"], ["Category", "category", "select", ["Legal", "Finance", "Liability", "Operational"]], ["Risk Level", "risk", "select", ["High", "Medium", "Low"]]].map(([label, field, type, opts]) => (
              <div key={field}>
                <label style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: 6 }}>{label}</label>
                {type === "select" ? (
                  <select value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}
                    style={{ width: "100%", background: "#070a10", border: "1px solid #1e2333", borderRadius: 8, padding: "10px 12px", color: "#e2e8f0", fontSize: 13 }}>
                    {opts.map(o => <option key={o}>{o}</option>)}
                  </select>
                ) : (
                  <input value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}
                    style={{ width: "100%", background: "#070a10", border: "1px solid #1e2333", borderRadius: 8, padding: "10px 12px", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
                )}
              </div>
            ))}
            <button onClick={add} style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 10, padding: "12px", cursor: "pointer", fontWeight: 700, fontSize: 14, marginTop: 8 }}>Add Clause</button>
          </div>
        </Modal>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>Standard Clause Repository</h1>
        <button onClick={() => setAdding(true)} style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 10, padding: "10px 18px", cursor: "pointer", fontWeight: 700, fontSize: 13 }}>+ Add Clause</button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
        {clauses.map(c => (
          <div key={c.id} style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: "#6366f1", fontWeight: 700 }}>{c.id}</div>
              <StatusBadge status={c.status} />
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#e2e8f0", marginBottom: 6 }}>{c.name}</div>
            <div style={{ fontSize: 12, color: "#64748b", marginBottom: 12 }}>{c.category} · {c.version}</div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <RiskBadge risk={c.risk} />
              <button style={{ background: "transparent", border: "1px solid #1e2333", borderRadius: 6, padding: "4px 10px", color: "#64748b", cursor: "pointer", fontSize: 11 }}>Edit</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Redline Engine View ──────────────────────────────────────────────────────
const RedlineView = ({ contracts }) => {
  const [selected, setSelected] = useState(contracts[0].id);
  const [status, setStatus] = useState({});
  const contract = contracts.find(c => c.id === selected);

  const suggestions = [
    { id: 1, clause: "7.2 Liability Cap", standard: "Liability shall be capped at 12 months of fees paid.", current: "Liability shall be capped at 6 months of fees paid.", risk: "High", suggestion: "Increase liability cap to 12 months as per standard." },
    { id: 2, clause: "9.1 Payment Terms", standard: "Payment due within 30 days of invoice.", current: "Payment due within 60 days of invoice.", risk: "Medium", suggestion: "Negotiate to standard 30-day payment terms." },
    { id: 3, clause: "12.3 Termination", standard: "30-day notice required for termination.", current: "90-day notice required for termination.", risk: "Medium", suggestion: "Reduce notice period to 30 days per standard clause." },
  ];

  return (
    <div>
      <h1 style={{ margin: "0 0 6px", fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>Redline Recommendation Engine</h1>
      <p style={{ margin: "0 0 20px", fontSize: 13, color: "#64748b" }}>AI-assisted clause deviation analysis and redline suggestions</p>

      <div style={{ marginBottom: 16 }}>
        <select value={selected} onChange={e => setSelected(e.target.value)}
          style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 10, padding: "10px 16px", color: "#e2e8f0", fontSize: 13, width: 320 }}>
          {contracts.filter(c => c.redlines > 0).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      {contract && (
        <div style={{ background: "#0a0d14", border: "1px solid #6366f144", borderRadius: 14, padding: 18, marginBottom: 16, display: "flex", gap: 20, alignItems: "center" }}>
          <div><div style={{ fontSize: 11, color: "#6366f1", fontWeight: 700 }}>CONTRACT</div><div style={{ fontSize: 14, color: "#e2e8f0", fontWeight: 600 }}>{contract.name}</div></div>
          <div><div style={{ fontSize: 11, color: "#64748b", fontWeight: 700 }}>VENDOR</div><div style={{ fontSize: 13, color: "#94a3b8" }}>{contract.vendor}</div></div>
          <div><div style={{ fontSize: 11, color: "#64748b", fontWeight: 700 }}>REDLINES</div><div style={{ fontSize: 13, color: "#ef4444", fontWeight: 700 }}>{contract.redlines} found</div></div>
          <div><div style={{ fontSize: 11, color: "#64748b", fontWeight: 700 }}>RISK</div><RiskBadge risk={contract.risk} /></div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {suggestions.map(s => {
          const st = status[s.id];
          return (
            <div key={s.id} style={{ background: "#0a0d14", border: `1px solid ${st === "accepted" ? "#22c55e44" : st === "rejected" ? "#ef444444" : "#1e2333"}`, borderRadius: 14, padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{s.clause}</div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <RiskBadge risk={s.risk} />
                  {st ? <StatusBadge status={st === "accepted" ? "Approved" : "Pending"} /> : null}
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 }}>
                <div style={{ background: "#ef444411", border: "1px solid #ef444433", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 10, color: "#ef4444", fontWeight: 700, marginBottom: 6 }}>CURRENT CLAUSE</div>
                  <div style={{ fontSize: 12, color: "#fca5a5" }}>{s.current}</div>
                </div>
                <div style={{ background: "#22c55e11", border: "1px solid #22c55e33", borderRadius: 8, padding: 12 }}>
                  <div style={{ fontSize: 10, color: "#22c55e", fontWeight: 700, marginBottom: 6 }}>STANDARD CLAUSE</div>
                  <div style={{ fontSize: 12, color: "#86efac" }}>{s.standard}</div>
                </div>
              </div>
              <div style={{ background: "#6366f111", borderRadius: 8, padding: 10, marginBottom: 14 }}>
                <span style={{ fontSize: 11, color: "#818cf8", fontWeight: 700 }}>AI Suggestion: </span>
                <span style={{ fontSize: 12, color: "#c7d2fe" }}>{s.suggestion}</span>
              </div>
              {!st && (
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => setStatus({ ...status, [s.id]: "accepted" })}
                    style={{ display: "flex", alignItems: "center", gap: 6, background: "#22c55e22", border: "1px solid #22c55e44", borderRadius: 8, padding: "8px 14px", color: "#22c55e", cursor: "pointer", fontWeight: 700, fontSize: 12 }}>
                    <Icon name="check" size={14} /> Accept
                  </button>
                  <button onClick={() => setStatus({ ...status, [s.id]: "rejected" })}
                    style={{ display: "flex", alignItems: "center", gap: 6, background: "#ef444422", border: "1px solid #ef444444", borderRadius: 8, padding: "8px 14px", color: "#ef4444", cursor: "pointer", fontWeight: 700, fontSize: 12 }}>
                    <Icon name="close" size={14} /> Reject
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─── Compare View ─────────────────────────────────────────────────────────────
const CompareView = ({ contracts }) => {
  const [a, setA] = useState(contracts[0].id);
  const [b, setB] = useState(contracts[1].id);
  const [compared, setCompared] = useState(false);
  const cA = contracts.find(c => c.id === a);
  const cB = contracts.find(c => c.id === b);

  const diffs = [
    { field: "Liability Cap", valA: "6 months fees", valB: "12 months fees", deviation: true },
    { field: "Payment Terms", valA: "60 days", valB: "30 days", deviation: true },
    { field: "Termination Notice", valA: "90 days", valB: "30 days", deviation: true },
    { field: "Governing Law", valA: "India", valB: "India", deviation: false },
    { field: "Dispute Resolution", valA: "Arbitration", valB: "Courts", deviation: true },
    { field: "IP Ownership", valA: "Shared", valB: "Shared", deviation: false },
  ];

  return (
    <div>
      <h1 style={{ margin: "0 0 6px", fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>Contract Comparison</h1>
      <p style={{ margin: "0 0 20px", fontSize: 13, color: "#64748b" }}>Side-by-side clause deviation analysis</p>

      <div style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "flex-end" }}>
        {[["Contract A", a, setA], ["Contract B", b, setB]].map(([label, val, setter]) => (
          <div key={label} style={{ flex: 1 }}>
            <label style={{ fontSize: 11, color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: 6 }}>{label}</label>
            <select value={val} onChange={e => { setter(e.target.value); setCompared(false); }}
              style={{ width: "100%", background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 10, padding: "10px 14px", color: "#e2e8f0", fontSize: 13 }}>
              {contracts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        ))}
        <button onClick={() => setCompared(true)}
          style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 10, padding: "10px 20px", cursor: "pointer", fontWeight: 700, fontSize: 13, whiteSpace: "nowrap" }}>
          Compare
        </button>
      </div>

      {compared && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
            {[cA, cB].map((c, i) => (
              <div key={i} style={{ background: "#0a0d14", border: `1px solid ${i === 0 ? "#6366f144" : "#8b5cf644"}`, borderRadius: 12, padding: 16 }}>
                <div style={{ fontSize: 11, color: i === 0 ? "#6366f1" : "#8b5cf6", fontWeight: 700, marginBottom: 6 }}>CONTRACT {i === 0 ? "A" : "B"}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{c.name}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>{c.vendor} · {c.version} · <RiskBadge risk={c.risk} /></div>
              </div>
            ))}
          </div>

          <div style={{ background: "#f59e0b11", border: "1px solid #f59e0b33", borderRadius: 10, padding: "10px 16px", marginBottom: 16, fontSize: 13, color: "#fbbf24" }}>
            ⚠ {diffs.filter(d => d.deviation).length} deviations found across {diffs.length} clauses
          </div>

          <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, overflow: "hidden" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 80px", background: "#070a10", borderBottom: "1px solid #1e2333" }}>
              {["Clause", "Contract A", "Contract B", ""].map(h => (
                <div key={h} style={{ padding: "12px 16px", fontSize: 11, color: "#475569", fontWeight: 700, textTransform: "uppercase" }}>{h}</div>
              ))}
            </div>
            {diffs.map((d, i) => (
              <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 80px", borderBottom: "1px solid #1e233344", background: d.deviation ? "#f59e0b08" : "transparent" }}>
                <div style={{ padding: "14px 16px", fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{d.field}</div>
                <div style={{ padding: "14px 16px", fontSize: 13, color: d.deviation ? "#fca5a5" : "#86efac" }}>{d.valA}</div>
                <div style={{ padding: "14px 16px", fontSize: 13, color: d.deviation ? "#86efac" : "#86efac" }}>{d.valB}</div>
                <div style={{ padding: "14px 16px", display: "flex", alignItems: "center" }}>
                  {d.deviation ? <span style={{ fontSize: 11, background: "#f59e0b22", color: "#f59e0b", border: "1px solid #f59e0b44", borderRadius: 99, padding: "2px 8px", fontWeight: 700 }}>Diff</span>
                    : <span style={{ fontSize: 11, background: "#22c55e22", color: "#22c55e", border: "1px solid #22c55e44", borderRadius: 99, padding: "2px 8px", fontWeight: 700 }}>Match</span>}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
            <button style={{ display: "flex", alignItems: "center", gap: 8, background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 10, padding: "10px 18px", color: "#a5b4fc", cursor: "pointer", fontWeight: 700, fontSize: 13 }}>
              <Icon name="export" size={15} /> Export Report
            </button>
          </div>
        </>
      )}
    </div>
  );
};

// ─── SharePoint View ──────────────────────────────────────────────────────────
const SharePointView = () => {
  const [config, setConfig] = useState({ url: "https://org.sharepoint.com/sites/Contracts", folder: "/Legal/Contracts", autoSync: true, metaSync: true });
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState("2025-05-15 06:00 AM");

  const doSync = () => {
    setSyncing(true);
    setTimeout(() => { setSyncing(false); setLastSync("2025-05-15 " + new Date().toLocaleTimeString()); }, 2000);
  };

  return (
    <div>
      <h1 style={{ margin: "0 0 6px", fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>SharePoint Integration</h1>
      <p style={{ margin: "0 0 24px", fontSize: 13, color: "#64748b" }}>Configure and monitor SharePoint synchronization</p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 24 }}>
          <h3 style={{ margin: "0 0 18px", fontSize: 14, fontWeight: 700, color: "#94a3b8" }}>Configuration</h3>
          {[["SharePoint URL", "url"], ["Folder Mapping", "folder"]].map(([label, key]) => (
            <div key={key} style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, color: "#64748b", fontWeight: 600, display: "block", marginBottom: 6 }}>{label}</label>
              <input value={config[key]} onChange={e => setConfig({ ...config, [key]: e.target.value })}
                style={{ width: "100%", background: "#070a10", border: "1px solid #1e2333", borderRadius: 8, padding: "10px 12px", color: "#e2e8f0", fontSize: 12, boxSizing: "border-box" }} />
            </div>
          ))}
          {[["Auto Sync", "autoSync"], ["Metadata Sync", "metaSync"]].map(([label, key]) => (
            <div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderTop: "1px solid #1e2333" }}>
              <span style={{ fontSize: 13, color: "#e2e8f0", fontWeight: 600 }}>{label}</span>
              <button onClick={() => setConfig({ ...config, [key]: !config[key] })}
                style={{ width: 44, height: 24, borderRadius: 99, border: "none", cursor: "pointer", background: config[key] ? "#6366f1" : "#1e2333", position: "relative", transition: "background .2s" }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#fff", position: "absolute", top: 3, left: config[key] ? 23 : 3, transition: "left .2s" }} />
              </button>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 24 }}>
            <h3 style={{ margin: "0 0 16px", fontSize: 14, fontWeight: 700, color: "#94a3b8" }}>Sync Status</h3>
            <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
              <div style={{ flex: 1, background: "#22c55e11", border: "1px solid #22c55e33", borderRadius: 10, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: "#22c55e" }}>8</div>
                <div style={{ fontSize: 11, color: "#4ade80", fontWeight: 600 }}>Synced</div>
              </div>
              <div style={{ flex: 1, background: "#f59e0b11", border: "1px solid #f59e0b33", borderRadius: 10, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: "#f59e0b" }}>0</div>
                <div style={{ fontSize: 11, color: "#fbbf24", fontWeight: 600 }}>Pending</div>
              </div>
              <div style={{ flex: 1, background: "#ef444411", border: "1px solid #ef444433", borderRadius: 10, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: "#ef4444" }}>0</div>
                <div style={{ fontSize: 11, color: "#f87171", fontWeight: 600 }}>Failed</div>
              </div>
            </div>
            <div style={{ fontSize: 12, color: "#64748b", marginBottom: 14 }}>Last sync: <span style={{ color: "#a5b4fc" }}>{lastSync}</span></div>
            <button onClick={doSync} disabled={syncing}
              style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, width: "100%", background: syncing ? "#1e2333" : "linear-gradient(135deg, #6366f1, #8b5cf6)", color: syncing ? "#64748b" : "#fff", border: "none", borderRadius: 10, padding: 12, cursor: syncing ? "not-allowed" : "pointer", fontWeight: 700, fontSize: 13 }}>
              <Icon name="sync" size={16} /> {syncing ? "Syncing…" : "Sync Now"}
            </button>
          </div>

          <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 20 }}>
            <h3 style={{ margin: "0 0 14px", fontSize: 14, fontWeight: 700, color: "#94a3b8" }}>Sync Log</h3>
            {["MSA – Accenture synced", "Oracle License synced", "AWS Cloud synced"].map((l, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "1px solid #1e233344" }}>
                <div style={{ color: "#22c55e" }}><Icon name="check" size={14} /></div>
                <span style={{ fontSize: 12, color: "#94a3b8" }}>{l}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Audit Logs View ──────────────────────────────────────────────────────────
const AuditView = () => (
  <div>
    <h1 style={{ margin: "0 0 20px", fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>Audit Logs & Activity Tracking</h1>
    <div style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, overflow: "hidden" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "#070a10" }}>
            {["#", "User", "Action", "Target", "Timestamp", "IP Address"].map(h => (
              <th key={h} style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, color: "#475569", fontWeight: 700, textTransform: "uppercase", borderBottom: "1px solid #1e2333" }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {AUDIT_LOGS.map((l, i) => (
            <tr key={l.id} style={{ borderBottom: "1px solid #1e233344" }}>
              <td style={{ padding: "12px 16px", fontSize: 12, color: "#475569" }}>{l.id}</td>
              <td style={{ padding: "12px 16px", fontSize: 13, color: "#a5b4fc", fontWeight: 600 }}>{l.user}</td>
              <td style={{ padding: "12px 16px", fontSize: 13, color: "#e2e8f0" }}>{l.action}</td>
              <td style={{ padding: "12px 16px", fontSize: 12, color: "#94a3b8" }}>{l.target}</td>
              <td style={{ padding: "12px 16px", fontSize: 12, color: "#64748b" }}>{l.time}</td>
              <td style={{ padding: "12px 16px", fontSize: 12, color: "#475569", fontFamily: "monospace" }}>{l.ip}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

// ─── Users View ───────────────────────────────────────────────────────────────
const UsersView = () => {
  const [users, setUsers] = useState(USERS);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", role: "Viewer" });

  const add = () => {
    setUsers([...users, { id: users.length + 1, ...form, status: "Active" }]);
    setAdding(false);
    setForm({ name: "", email: "", role: "Viewer" });
  };

  const toggle = (id) => setUsers(users.map(u => u.id === id ? { ...u, status: u.status === "Active" ? "Inactive" : "Active" } : u));

  return (
    <div>
      {adding && (
        <Modal title="Add New User" onClose={() => setAdding(false)}>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[["Full Name", "name"], ["Email Address", "email"]].map(([label, field]) => (
              <div key={field}>
                <label style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: 6 }}>{label}</label>
                <input value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}
                  style={{ width: "100%", background: "#070a10", border: "1px solid #1e2333", borderRadius: 8, padding: "10px 12px", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
              </div>
            ))}
            <div>
              <label style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: 6 }}>Role</label>
              <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}
                style={{ width: "100%", background: "#070a10", border: "1px solid #1e2333", borderRadius: 8, padding: "10px 12px", color: "#e2e8f0", fontSize: 13 }}>
                {["Admin", "Contract Manager", "Legal Reviewer", "Viewer"].map(r => <option key={r}>{r}</option>)}
              </select>
            </div>
            <button onClick={add} style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 10, padding: 12, cursor: "pointer", fontWeight: 700, fontSize: 14, marginTop: 8 }}>Add User</button>
          </div>
        </Modal>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: "#f1f5f9" }}>User & Role Management</h1>
        <button onClick={() => setAdding(true)} style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 10, padding: "10px 18px", cursor: "pointer", fontWeight: 700, fontSize: 13 }}>+ Add User</button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
        {users.map(u => (
          <div key={u.id} style={{ background: "#0a0d14", border: "1px solid #1e2333", borderRadius: 14, padding: 20 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
              <div style={{ width: 40, height: 40, borderRadius: "50%", background: "linear-gradient(135deg, #6366f1, #ec4899)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 800, color: "#fff" }}>
                {u.name[0]}
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{u.name}</div>
                <div style={{ fontSize: 12, color: "#64748b" }}>{u.email}</div>
              </div>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 12, color: "#6366f1", background: "#6366f122", border: "1px solid #6366f133", borderRadius: 99, padding: "3px 10px", fontWeight: 600 }}>{u.role}</span>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <StatusBadge status={u.status} />
                <button onClick={() => toggle(u.id)} style={{ background: "transparent", border: "1px solid #1e2333", borderRadius: 6, padding: "3px 8px", color: "#64748b", cursor: "pointer", fontSize: 11 }}>
                  {u.status === "Active" ? "Disable" : "Enable"}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Upload Modal ─────────────────────────────────────────────────────────────
const UploadModal = ({ onClose, onUpload }) => {
  const [form, setForm] = useState({ name: "", vendor: "", expiry: "", risk: "Medium" });
  const submit = () => {
    if (!form.name || !form.vendor || !form.expiry) return;
    onUpload({ id: `C-00${Math.floor(Math.random() * 900) + 100}`, ...form, redlines: 0, version: "v1.0", status: "Active", uploaded: new Date().toISOString().slice(0, 10), clauses: 0 });
    onClose();
  };
  return (
    <Modal title="Upload New Contract" onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {[["Contract Name", "name", "text"], ["Vendor / Party", "vendor", "text"], ["Expiry Date", "expiry", "date"], ["Risk Level", "risk", "select", ["High", "Medium", "Low"]]].map(([label, field, type, opts]) => (
          <div key={field}>
            <label style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600, display: "block", marginBottom: 6 }}>{label}</label>
            {type === "select" ? (
              <select value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}
                style={{ width: "100%", background: "#070a10", border: "1px solid #1e2333", borderRadius: 8, padding: "10px 12px", color: "#e2e8f0", fontSize: 13 }}>
                {opts.map(o => <option key={o}>{o}</option>)}
              </select>
            ) : (
              <input type={type} value={form[field]} onChange={e => setForm({ ...form, [field]: e.target.value })}
                style={{ width: "100%", background: "#070a10", border: "1px solid #1e2333", borderRadius: 8, padding: "10px 12px", color: "#e2e8f0", fontSize: 13, boxSizing: "border-box" }} />
            )}
          </div>
        ))}
        <div style={{ border: "2px dashed #1e2333", borderRadius: 10, padding: "24px", textAlign: "center", color: "#475569", fontSize: 13, marginTop: 4 }}>
          📎 Drag & drop contract file here, or click to browse<br />
          <span style={{ fontSize: 11 }}>PDF, DOCX supported</span>
        </div>
        <button onClick={submit} style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 10, padding: 12, cursor: "pointer", fontWeight: 700, fontSize: 14 }}>Upload Contract</button>
      </div>
    </Modal>
  );
};

// ─── App Root ─────────────────────────────────────────────────────────────────
export default function App() {
  const [view, setView] = useState("dashboard");
  const [contracts, setContracts] = useState(CONTRACTS);
  const [uploadOpen, setUploadOpen] = useState(false);

  const addContract = (c) => setContracts([c, ...contracts]);

  const views = {
    dashboard: <DashboardView contracts={contracts} setActive={setView} setUploadOpen={setUploadOpen} />,
    contracts: <ContractsView contracts={contracts} setContracts={setContracts} />,
    clauses: <ClauseView />,
    redline: <RedlineView contracts={contracts.filter(c => c.redlines > 0)} />,
    compare: <CompareView contracts={contracts} />,
    sharepoint: <SharePointView />,
    audit: <AuditView />,
    users: <UsersView />,
  };

  return (
    <div style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif", background: "#080b12", minHeight: "100vh", color: "#e2e8f0" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      {uploadOpen && <UploadModal onClose={() => setUploadOpen(false)} onUpload={addContract} />}
      <Sidebar active={view} setActive={setView} />
      <main style={{ marginLeft: 240, padding: "32px 36px", minHeight: "100vh" }}>
        {views[view]}
      </main>
    </div>
  );
}
