import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [status, setStatus] = useState("Loading...");
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [lastUpdated, setLastUpdated] = useState("--:--:--");
  const [error, setError] = useState(false);

  const fetchData = async () => {
    try {
      const [statusRes, statsRes, alertsRes, historyRes] =
        await Promise.all([
          axios.get(`${API_BASE}/status`),
          axios.get(`${API_BASE}/stats?hours=24`),
          axios.get(`${API_BASE}/alerts?limit=10`),
          axios.get(`${API_BASE}/history?hours=24&limit=30`)
        ]);

      const statsData = statsRes.data || {};
      const alertData = Array.isArray(alertsRes.data)
        ? alertsRes.data
        : Array.isArray(alertsRes.data?.items)
        ? alertsRes.data.items
        : [];

      const historyData = Array.isArray(historyRes.data)
        ? historyRes.data
        : Array.isArray(historyRes.data?.items)
        ? historyRes.data.items
        : [];

      setStats(statsData);
      setAlerts(alertData);
      setHistory(historyData);

      setStatus(
        statsData?.latest?.risk_level ||
        statusRes.data?.latest_risk ||
        "Safe"
      );

      setLastUpdated(new Date().toLocaleTimeString());
      setError(false);
    } catch (err) {
      console.error("Backend connection error:", err);
      setError(true);
      setStatus("Backend Offline");
    }
  };

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 5000);

    return () => clearInterval(interval);
  }, []);

  const latestAlert = alerts.length > 0 ? alerts[0] : null;

  const riskScore = useMemo(() => {
    const probability = Number(stats?.latest?.probability ?? 0);

    if (Number.isNaN(probability)) return 0;

    return Math.max(
      0,
      Math.min(
        100,
        probability <= 1
          ? Math.round(probability * 100)
          : Math.round(probability)
      )
    );
  }, [stats]);

  const riskType =
    stats?.latest?.risk_level ||
    status ||
    "Safe";

  const dashboardStats = {
    cycles: stats?.total_cycles ?? 0,
    filesObserved: stats?.files_observed ?? 0,
    suspiciousActivities: stats?.suspicious_activities ?? 0,
    highRiskDetections: stats?.high_risk_detections ?? 0,
    filesystemEvents: stats?.filesystem_events ?? 0,
    ransomwareIncidents: stats?.ransomware_incidents ?? 0
  };

  const getRiskTone = (value = riskType) => {
    const normalized = String(value).toLowerCase();

    if (
      normalized === "high risk" ||
      normalized === "high" ||
      normalized === "critical"
    ) {
      return "danger";
    }

    if (
      normalized === "suspicious" ||
      normalized === "medium"
    ) {
      return "warning";
    }

    if (
      normalized === "backend offline" ||
      normalized === "offline"
    ) {
      return "offline";
    }

    return "safe";
  };

  const getRiskClass = () => {
    if (riskScore >= 70) return "danger";
    if (riskScore >= 35) return "warning";
    return "safe";
  };

  const formatTime = (value) => {
    if (!value) return "--";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  };

  const formatDateTime = (value) => {
    if (!value) return "--";

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return date.toLocaleString([], {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const normalizeIndicators = (alert) => {
    const raw =
      alert?.main_contributing_indicators ??
      alert?.indicators ??
      alert?.factors ??
      [];

    if (Array.isArray(raw)) {
      return raw.map((item) => {
        if (typeof item === "string") {
          return {
            name: item,
            value: ""
          };
        }

        return {
          name:
            item?.name ||
            item?.indicator ||
            item?.feature ||
            "Behavioral indicator",
          value:
            item?.value ??
            item?.count ??
            item?.description ??
            ""
        };
      });
    }

    if (typeof raw === "object" && raw !== null) {
      return Object.entries(raw).map(([name, value]) => ({
        name,
        value
      }));
    }

    return [];
  };

  const indicators = normalizeIndicators(latestAlert);

  const chartData = useMemo(() => {
    return [...history]
      .reverse()
      .map((item, index) => {
        const probability = Number(item?.probability ?? 0);

        return {
          index: index + 1,
          time: formatTime(item?.timestamp),
          risk:
            probability <= 1
              ? Math.round(probability * 100)
              : Math.round(probability)
        };
      });
  }, [history]);

  const latestTimestamp =
    stats?.latest?.timestamp ||
    latestAlert?.timestamp;

  const liveMonitoring = !error;

  return (
    <div className="app-shell">

      {/* SIDEBAR */}
      <aside className="sidebar">
        <div className="brand">
          <img
            src="/ransomwatch-ai-logo.png"
            alt="RansomWatchAI"
            className="brand-logo"
          />

          <div className="brand-copy">
            <div className="brand-name">RansomWatchAI</div>
            <div className="brand-subtitle">Early threat detection</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-label">MONITORING</div>

          <a href="#overview" className="nav-item active">
            <span className="nav-mark">01</span>
            Overview
          </a>

          <a href="#history" className="nav-item">
            <span className="nav-mark">02</span>
            Detection history
          </a>

          <a href="#xai" className="nav-item">
            <span className="nav-mark">03</span>
            Explainability
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="environment-label">ENVIRONMENT</div>

          <div className="environment-box">
            <span className={`environment-dot ${liveMonitoring ? "online" : "offline"}`} />
            <div>
              <strong>Prototype endpoint</strong>
              <span>Controlled monitoring</span>
            </div>
          </div>

          <div className="sidebar-version">
            RansomWatchAI · v1.0
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main-content">

        {/* TOP BAR */}
        <header className="topbar">
          <div>
            <div className="eyebrow">SECURITY OPERATIONS</div>
            <h1>Monitoring overview</h1>
            <p>Live ransomware activity analysis and detection history.</p>
          </div>

          <div className="topbar-right">
            <div className={`connection-pill ${liveMonitoring ? "connected" : "disconnected"}`}>
              <span className="connection-dot" />
              {liveMonitoring ? "System connected" : "Backend offline"}
            </div>

            <div className="updated-text">
              Updated {lastUpdated}
            </div>
          </div>
        </header>

        {/* OVERVIEW */}
        <section id="overview" className="section-block">

          <div className="section-heading">
            <div>
              <span className="section-kicker">LIVE STATUS</span>
              <h2>Current protection state</h2>
            </div>

            <div className="section-note">
              Refresh interval · 5 seconds
            </div>
          </div>

          <div className="overview-grid">

            {/* SYSTEM STATUS */}
            <article className="overview-card status-card">
              <div className="card-label">SYSTEM STATUS</div>

              <div className="status-row">
                <div className={`status-orb ${getRiskTone(status)}`}>
                  <span />
                </div>

                <div>
                  <div className="status-value">
                    {liveMonitoring ? status : "Offline"}
                  </div>

                  <div className="status-caption">
                    {liveMonitoring
                      ? "Continuous monitoring active"
                      : "Waiting for backend connection"}
                  </div>
                </div>
              </div>

              <div className="card-divider" />

              <div className="card-meta">
                <span>Latest cycle</span>
                <strong>{formatTime(latestTimestamp)}</strong>
              </div>
            </article>

            {/* RISK SCORE */}
            <article className="overview-card risk-card">
              <div className="card-label">LATEST RISK SCORE</div>

              <div className="risk-layout">
                <div className={`risk-ring ${getRiskClass()}`}>
                  <div className="risk-ring-inner">
                    <strong>{riskScore}</strong>
                    <span>/ 100</span>
                  </div>
                </div>

                <div className="risk-copy">
                  <div className={`risk-badge ${getRiskClass()}`}>
                    {riskType}
                  </div>

                  <div className="risk-description">
                    Model probability for the latest monitoring cycle.
                  </div>
                </div>
              </div>
            </article>

            {/* CYCLES */}
            <article className="overview-card compact-card">
              <div className="card-label">MONITORING CYCLES</div>

              <div className="metric-number">
                {dashboardStats.cycles.toLocaleString()}
              </div>

              <div className="metric-caption">
                Analysis cycles recorded
              </div>

              <div className="metric-line">
                <span />
              </div>
            </article>

            {/* INCIDENTS */}
            <article className="overview-card compact-card incident-card">
              <div className="card-label">RANSOMWARE INCIDENTS</div>

              <div className="metric-number">
                {dashboardStats.ransomwareIncidents.toLocaleString()}
              </div>

              <div className="metric-caption">
                Detected transitions to high risk
              </div>

              <div className="incident-status">
                <span className="incident-dot" />
                Incident tracking enabled
              </div>
            </article>

          </div>
        </section>

        {/* STATISTICS */}
        <section className="section-block">
          <div className="section-heading">
            <div>
              <span className="section-kicker">24 HOUR WINDOW</span>
              <h2>Monitoring statistics</h2>
            </div>
          </div>

          <div className="statistics-grid">

            <StatCard
              label="Files observed"
              value={dashboardStats.filesObserved}
              helper="Unique file paths seen"
              tone="neutral"
            />

            <StatCard
              label="Filesystem events"
              value={dashboardStats.filesystemEvents}
              helper="Created, modified, deleted, renamed"
              tone="neutral"
            />

            <StatCard
              label="Suspicious activities"
              value={dashboardStats.suspiciousActivities}
              helper="Cycles classified as suspicious"
              tone="warning"
            />

            <StatCard
              label="High-risk detections"
              value={dashboardStats.highRiskDetections}
              helper="Cycles above the high-risk threshold"
              tone="danger"
            />

          </div>
        </section>

        {/* CHART + LATEST DETECTION */}
        <section className="content-two-column">

          <article id="history" className="panel chart-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">DETECTION HISTORY</span>
                <h2>Risk trend · last 24 hours</h2>
              </div>

              <div className="history-count">
                {history.length} records
              </div>
            </div>

            <div className="chart-area">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData}
                    margin={{
                      top: 12,
                      right: 18,
                      left: -16,
                      bottom: 4
                    }}
                  >
                    <CartesianGrid
                      vertical={false}
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="time"
                      tickLine={false}
                      axisLine={false}
                      minTickGap={30}
                    />

                    <YAxis
                      domain={[0, 100]}
                      tickLine={false}
                      axisLine={false}
                      width={34}
                    />

                    <Tooltip
                      formatter={(value) => [`${value}/100`, "Risk"]}
                      labelFormatter={(label) => `Time · ${label}`}
                    />

                    <Line
                      type="monotone"
                      dataKey="risk"
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">
                  <div className="empty-symbol">—</div>
                  <strong>No detection history yet</strong>
                  <span>
                    Monitoring data will appear here as cycles are recorded.
                  </span>
                </div>
              )}
            </div>
          </article>

          <article className="panel latest-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">LATEST CYCLE</span>
                <h2>Detection snapshot</h2>
              </div>
            </div>

            {stats?.latest ? (
              <div className="snapshot-body">

                <div className="snapshot-risk">
                  <span className={`snapshot-indicator ${getRiskTone(riskType)}`} />
                  <div>
                    <span className="snapshot-label">Risk type</span>
                    <strong>{riskType}</strong>
                  </div>
                </div>

                <div className="snapshot-grid">
                  <SnapshotMetric
                    label="Probability"
                    value={`${riskScore}%`}
                  />

                  <SnapshotMetric
                    label="Files"
                    value={stats.latest.files_observed ?? 0}
                  />

                  <SnapshotMetric
                    label="Suspicious"
                    value={stats.latest.suspicious_files ?? 0}
                  />

                  <SnapshotMetric
                    label="High risk"
                    value={stats.latest.high_risk_files ?? 0}
                  />
                </div>

                <div className="snapshot-action">
                  <span>Response</span>
                  <strong>
                    {stats.latest.response_action || "No action"}
                  </strong>
                </div>

              </div>
            ) : (
              <div className="empty-state compact">
                <div className="empty-symbol">—</div>
                <strong>Waiting for monitoring data</strong>
                <span>Start the monitoring pipeline to populate this panel.</span>
              </div>
            )}
          </article>

        </section>

        {/* XAI */}
        <section id="xai" className="section-block">

          <article className="panel xai-panel">
            <div className="panel-header">
              <div>
                <span className="section-kicker">EXPLAINABLE AI</span>
                <h2>Why the model raised the current result</h2>
              </div>

              <div className="xai-tag">BEHAVIORAL INDICATORS</div>
            </div>

            {indicators.length > 0 ? (
              <div className="xai-grid">
                <div className="xai-intro">
                  <div className="xai-mark">AI</div>

                  <h3>Observed signals</h3>

                  <p>
                    These indicators are taken from the latest detection
                    response and describe the filesystem and process behavior
                    associated with the model result.
                  </p>
                </div>

                <div className="indicator-list">
                  {indicators.slice(0, 6).map((indicator, index) => (
                    <div className="indicator-row" key={`${indicator.name}-${index}`}>
                      <div className="indicator-index">
                        0{index + 1}
                      </div>

                      <div className="indicator-main">
                        <strong>{formatIndicatorName(indicator.name)}</strong>

                        {indicator.value !== "" && (
                          <span>{String(indicator.value)}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="xai-empty">
                <div className="xai-empty-mark">AI</div>

                <div>
                  <strong>No contributing indicators reported</strong>
                  <span>
                    The latest cycle does not currently provide explainability
                    indicators.
                  </span>
                </div>
              </div>
            )}
          </article>

        </section>

        {/* RECENT DETECTIONS TABLE */}
        <section className="section-block">

          <div className="section-heading">
            <div>
              <span className="section-kicker">SECURITY LOG</span>
              <h2>Recent detections</h2>
            </div>

            <div className="section-note">
              Latest 10 records
            </div>
          </div>

          <article className="panel detections-panel">

            {alerts.length > 0 ? (
              <div className="table-wrapper">

                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Risk</th>
                      <th>Probability</th>
                      <th>Files</th>
                      <th>Filesystem</th>
                      <th>Response</th>
                    </tr>
                  </thead>

                  <tbody>
                    {alerts.map((alert, index) => {
                      const probability = Number(
                        alert?.probability ?? 0
                      );

                      const score = probability <= 1
                        ? Math.round(probability * 100)
                        : Math.round(probability);

                      const tone = getRiskTone(alert?.risk_level);

                      return (
                        <tr key={alert?.id ?? index}>

                          <td>
                            <span className="table-time">
                              {formatDateTime(alert?.timestamp)}
                            </span>
                          </td>

                          <td>
                            <span className={`table-risk ${tone}`}>
                              <span />
                              {alert?.risk_level || "Safe"}
                            </span>
                          </td>

                          <td>
                            <strong>{score}%</strong>
                          </td>

                          <td>
                            {alert?.files_affected ??
                              alert?.files_observed ??
                              0}
                          </td>

                          <td>
                            {alert?.filesystem_events ?? 0}
                          </td>

                          <td>
                            <span className="response-text">
                              {alert?.response_action || "No action"}
                            </span>
                          </td>

                        </tr>
                      );
                    })}
                  </tbody>
                </table>

              </div>
            ) : (
              <div className="empty-detections">
                <div className="empty-symbol">—</div>
                <strong>No detections recorded</strong>
                <span>
                  Security events will appear here when the monitoring system
                  records them.
                </span>
              </div>
            )}

          </article>
        </section>

        {/* FOOTER */}
        <footer className="footer">
          <span>RansomWatchAI</span>
          <span>AI-based early ransomware detection prototype</span>
          <span>Live monitoring · 24h history</span>
        </footer>

      </main>
    </div>
  );
}

function StatCard({ label, value, helper, tone }) {
  return (
    <article className={`stat-card ${tone}`}>
      <div className="stat-card-top">
        <span>{label}</span>
        <span className="stat-dot" />
      </div>

      <strong>{Number(value).toLocaleString()}</strong>

      <p>{helper}</p>
    </article>
  );
}

function SnapshotMetric({ label, value }) {
  return (
    <div className="snapshot-metric">
      <span>{label}</span>
      <strong>{Number(value).toLocaleString()}</strong>
    </div>
  );
}

function formatIndicatorName(value) {
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default App;
