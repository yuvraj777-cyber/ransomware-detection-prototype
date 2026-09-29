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

  // =========================================
  // FETCH ALL DASHBOARD DATA
  // =========================================

  const fetchData = async () => {
    try {
      const [statusRes, statsRes, alertsRes, historyRes] =
        await Promise.all([
          axios.get(`${API_BASE}/status`),
          axios.get(`${API_BASE}/stats?hours=24`),
          axios.get(`${API_BASE}/alerts?limit=10`),
          axios.get(`${API_BASE}/history?hours=24&limit=30`)
        ]);

      setStats(statsRes.data || null);
      setAlerts(Array.isArray(alertsRes.data) ? alertsRes.data : []);

      const historyItems = Array.isArray(historyRes.data)
        ? historyRes.data
        : Array.isArray(historyRes.data?.items)
        ? historyRes.data.items
        : [];

      setHistory(historyItems);

      setStatus(
        statsRes.data?.latest?.risk_level ||
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

  // =========================================
  // AUTO UPDATE EVERY 5 SEC
  // =========================================

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 5000);

    return () => clearInterval(interval);
  }, []);

  // =========================================
  // LATEST DETECTION
  // =========================================

  const latestAlert = alerts.length > 0 ? alerts[0] : null;

  // =========================================
  // RISK SCORE
  // =========================================

  let riskScore = 0;

  if (stats?.latest?.probability !== undefined) {
    const probability = Number(stats.latest.probability);

    if (!Number.isNaN(probability)) {
      riskScore =
        probability <= 1
          ? Math.round(probability * 100)
          : Math.round(probability);
    }
  }

  // =========================================
  // RISK TYPE
  // =========================================

  const riskType =
    stats?.latest?.risk_level ||
    status ||
    "Safe";

  // =========================================
  // STATUS CLASS
  // =========================================

  const getStatusClass = (value = status) => {
    const normalized = String(value).toLowerCase();

    if (normalized === "safe") {
      return "safe";
    }

    if (
      normalized === "suspicious" ||
      normalized === "medium"
    ) {
      return "warning";
    }

    if (
      normalized === "high risk" ||
      normalized === "high" ||
      normalized === "critical"
    ) {
      return "danger";
    }

    if (
      normalized === "backend offline" ||
      normalized === "offline"
    ) {
      return "offline";
    }

    return "safe";
  };

  // =========================================
  // RISK CLASS
  // =========================================

  const getRiskClass = () => {
    if (riskScore >= 70) {
      return "danger";
    }

    if (riskScore >= 35) {
      return "warning";
    }

    return "safe";
  };

  // =========================================
  // STATISTICS
  // =========================================

  const dashboardStats = {
    cycles: stats?.total_cycles ?? 0,
    filesObserved: stats?.files_observed ?? 0,
    suspiciousActivities: stats?.suspicious_activities ?? 0,
    highRiskDetections: stats?.high_risk_detections ?? 0,
    filesystemEvents: stats?.filesystem_events ?? 0,
    ransomwareIncidents: stats?.ransomware_incidents ?? 0
  };

  // =========================================
  // XAI INDICATORS
  // =========================================

  const getIndicators = () => {
    const raw =
      latestAlert?.main_contributing_indicators ??
      latestAlert?.indicators ??
      latestAlert?.factors ??
      [];

    if (Array.isArray(raw)) {
      return raw;
    }

    if (typeof raw === "string") {
      try {
        const parsed = JSON.parse(raw);

        if (Array.isArray(parsed)) {
          return parsed;
        }

        return [parsed];
      } catch {
        return raw
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean);
      }
    }

    if (raw && typeof raw === "object") {
      return Object.entries(raw).map(
        ([key, value]) => `${key}: ${value}`
      );
    }

    return [];
  };

  const indicators = getIndicators();

  const formatIndicator = (indicator) => {
    if (typeof indicator === "string") {
      return indicator;
    }

    if (indicator && typeof indicator === "object") {
      if (indicator.name) {
        return indicator.value !== undefined
          ? `${indicator.name}: ${indicator.value}`
          : indicator.name;
      }

      const entries = Object.entries(indicator);

      if (entries.length > 0) {
        return entries
          .map(([key, value]) => `${key}: ${value}`)
          .join(" • ");
      }
    }

    return String(indicator);
  };

  // =========================================
  // HISTORY FOR CHART
  // =========================================

  const chartData = useMemo(() => {
    return [...history]
      .reverse()
      .map((item) => ({
        time: new Date(item.timestamp).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit"
        }),
        probability:
          Number(item.probability ?? 0) <= 1
            ? Math.round(Number(item.probability ?? 0) * 100)
            : Math.round(Number(item.probability ?? 0))
      }));
  }, [history]);

  // =========================================
  // CURRENT MONITORING STATE
  // =========================================

  const monitoringActive =
    !error &&
    (
      stats?.latest?.timestamp
        ? Date.now() -
            new Date(stats.latest.timestamp).getTime() <
          30000
        : false
    );

  // =========================================
  // RISK CIRCLE
  // =========================================

  const riskAngle = Math.max(
    0,
    Math.min(riskScore, 100) * 3.6
  );

  const riskCircleStyle = {
    background: `conic-gradient(
      var(--risk-color) 0deg ${riskAngle}deg,
      #e4e9ec ${riskAngle}deg 360deg
    )`
  };

  return (
    <div className="dashboard">

      {/* =========================================
          HEADER
      ========================================= */}

      <header className="header">

        <div className="header-left">

          <div className="logo-icon">
            🛡
          </div>

          <div>
            <h1>
              Ransomware Detection Dashboard
            </h1>

            <p>
              AI-powered early detection and system monitoring
            </p>
          </div>

        </div>

        <div className="header-right">

          <div
            className={`status-badge ${getStatusClass()}`}
          >
            <span></span>

            {error
              ? "BACKEND OFFLINE"
              : status.toUpperCase()}
          </div>

          <div className="updated">
            Updated {lastUpdated}
          </div>

        </div>

      </header>

      {/* =========================================
          MAIN CONTENT
      ========================================= */}

      <main className="main-content">

        <div className="section-title">
          <h2>System Overview</h2>

          <p>
            Real-time ransomware detection status
          </p>
        </div>

        {/* =========================================
            FOUR MAIN CARDS
        ========================================= */}

        <div className="overview-grid">

          {/* SYSTEM STATUS */}

          <div
            className={`overview-card status-card ${getStatusClass()}`}
          >

            <div className="card-top">
              <span>SYSTEM STATUS</span>

              <div className="card-icon green-icon">
                ●
              </div>
            </div>

            <div className="status-main">

              <div className="status-circle">
                {error ? "!" : "✓"}
              </div>

              <div>

                <h3>
                  {status}
                </h3>

                <p>
                  Monitoring system activity
                </p>

              </div>

            </div>

            <div className="card-bottom">
              <span className="live-dot"></span>

              {monitoringActive
                ? "Sensor monitoring active"
                : error
                ? "Backend connection unavailable"
                : "Waiting for monitoring cycle"}
            </div>

          </div>

          {/* RECENT ALERTS */}

          <div className="overview-card">

            <div className="card-top">

              <span>
                RECENT DETECTIONS
              </span>

              <div className="card-icon alert-icon">
                ⚠
              </div>

            </div>

            <div className="number">
              {alerts.length}
            </div>

            <p className="description">
              Non-safe detections shown
            </p>

            <div className="card-bottom alert-bottom">

              {dashboardStats.suspiciousActivities > 0
                ? `${dashboardStats.suspiciousActivities} suspicious activities in 24h`
                : "No suspicious activity"}

            </div>

          </div>

          {/* RISK SCORE */}

          <div
            className={`overview-card risk-score-card ${getRiskClass()}`}
          >

            <div className="card-top">

              <span>
                RISK SCORE
              </span>

              <div className="card-icon">
                ◉
              </div>

            </div>

            <div className="score-content">

              <div
                className="risk-circle"
                style={riskCircleStyle}
              >

                <div className="risk-inner">

                  <strong>
                    {riskScore}%
                  </strong>

                  <small>
                    Risk
                  </small>

                </div>

              </div>

            </div>

            <div
              className={`score-label ${getRiskClass()}`}
            >
              {riskScore >= 70
                ? "HIGH RISK"
                : riskScore >= 35
                ? "SUSPICIOUS"
                : "LOW RISK"}
            </div>

          </div>

          {/* RISK TYPE */}

          <div className="overview-card">

            <div className="card-top">

              <span>
                RISK TYPE
              </span>

              <div className="card-icon type-icon">
                ◆
              </div>

            </div>

            <div
              className={`risk-type ${getRiskClass()}`}
            >
              {riskType}
            </div>

            <p className="description">
              Current detected threat level
            </p>

            <div className="card-bottom">
              Based on ML prediction
            </div>

          </div>

        </div>

        {/* =========================================
            MONITORING STATISTICS
        ========================================= */}

        <section className="statistics-section">

          <div className="section-title statistics-title">
            <h2>Monitoring Statistics</h2>

            <p>
              Continuous monitoring summary for the last 24 hours
            </p>
          </div>

          <div className="statistics-grid">

            <div className="stat-card">
              <span>MONITORING CYCLES</span>
              <strong>{dashboardStats.cycles}</strong>
              <small>Analysis cycles completed</small>
            </div>

            <div className="stat-card">
              <span>FILES OBSERVED</span>
              <strong>{dashboardStats.filesObserved}</strong>
              <small>Files seen by the monitor</small>
            </div>

            <div className="stat-card warning-stat">
              <span>SUSPICIOUS ACTIVITIES</span>
              <strong>{dashboardStats.suspiciousActivities}</strong>
              <small>Suspicious monitoring results</small>
            </div>

            <div className="stat-card danger-stat">
              <span>HIGH-RISK DETECTIONS</span>
              <strong>{dashboardStats.highRiskDetections}</strong>
              <small>High-risk ML detections</small>
            </div>

            <div className="stat-card">
              <span>FILESYSTEM EVENTS</span>
              <strong>{dashboardStats.filesystemEvents}</strong>
              <small>Meaningful filesystem events</small>
            </div>

            <div className="stat-card danger-stat">
              <span>RANSOMWARE INCIDENTS</span>
              <strong>{dashboardStats.ransomwareIncidents}</strong>
              <small>Detected incident transitions</small>
            </div>

          </div>

        </section>

        {/* =========================================
            24 HOUR ACTIVITY
        ========================================= */}

        <section className="history-panel">

          <div className="history-header">

            <div>
              <h2>24-Hour Detection History</h2>

              <p>
                Risk probability across completed monitoring cycles
              </p>
            </div>

            <div className="history-badge">
              LAST 24 HOURS
            </div>

          </div>

          <div className="chart-wrapper">

            {chartData.length > 0 ? (

              <ResponsiveContainer
                width="100%"
                height={260}
              >

                <LineChart data={chartData}>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#e5eaed"
                  />

                  <XAxis
                    dataKey="time"
                    tick={{
                      fontSize: 9,
                      fill: "#82909a"
                    }}
                    axisLine={{
                      stroke: "#dce4e8"
                    }}
                    tickLine={false}
                  />

                  <YAxis
                    domain={[0, 100]}
                    tick={{
                      fontSize: 9,
                      fill: "#82909a"
                    }}
                    axisLine={{
                      stroke: "#dce4e8"
                    }}
                    tickLine={false}
                  />

                  <Tooltip
                    formatter={(value) => [
                      `${value}%`,
                      "Risk Probability"
                    ]}
                    contentStyle={{
                      border: "1px solid #dce4e8",
                      borderRadius: "6px",
                      fontSize: "10px"
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey="probability"
                    stroke="#62869c"
                    strokeWidth={2}
                    dot={{
                      r: 3
                    }}
                    activeDot={{
                      r: 5
                    }}
                  />

                </LineChart>

              </ResponsiveContainer>

            ) : (

              <div className="empty-history">
                <span>◌</span>

                <p>
                  No monitoring history available yet.
                </p>

              </div>

            )}

          </div>

        </section>

        {/* =========================================
            XAI SECTION
        ========================================= */}

        <section className="xai-panel">

          <div className="xai-header">

            <div className="xai-title">

              <div className="brain-icon">
                🧠
              </div>

              <div>

                <h2>
                  Explainable AI
                </h2>

                <p>
                  Why was this risk detected?
                </p>

              </div>

            </div>

            <div className="ai-badge">
              AI ANALYSIS
            </div>

          </div>

          {latestAlert ? (

            <div className="xai-content">

              {/* MODEL PROBABILITY */}

              <div className="model-result">

                <div>

                  <span>
                    MODEL PROBABILITY
                  </span>

                  <p>
                    Probability of ransomware activity
                  </p>

                </div>

                <strong>
                  {riskScore}%
                </strong>

              </div>

              {/* FACTORS */}

              <div className="factors-section">

                <h3>
                  Contributing Indicators
                </h3>

                <p className="factor-subtitle">
                  Behavioral indicators associated with the latest detection.
                </p>

                <div className="factor-list">

                  {indicators.length > 0 ? (

                    indicators
                      .slice(0, 6)
                      .map((indicator, index) => {

                        const width = Math.max(
                          35,
                          90 - index * 10
                        );

                        return (

                          <div
                            className="factor-row"
                            key={`${index}-${formatIndicator(indicator)}`}
                          >

                            <div className="factor-number">
                              {index + 1}
                            </div>

                            <div className="factor-info">

                              <div className="factor-name">
                                {formatIndicator(indicator)}
                              </div>

                              <div className="factor-bar">

                                <div
                                  style={{
                                    width: `${width}%`
                                  }}
                                ></div>

                              </div>

                            </div>

                          </div>

                        );
                      })

                  ) : (

                    <div className="no-indicators">
                      No specific contributing indicators were returned
                      for this detection.
                    </div>

                  )}

                </div>

              </div>

              {/* SIMPLE EXPLANATION */}

              <div className="explanation-box">

                <div className="explanation-icon">
                  ✦
                </div>

                <div>

                  <strong>
                    Detection Explanation
                  </strong>

                  <p>
                    {riskScore >= 70
                      ? "The AI model detected multiple behavioral patterns strongly associated with ransomware activity."
                      : riskScore >= 35
                      ? indicators.length > 0
                        ? "The AI model detected behavioral patterns that may indicate suspicious activity and require attention."
                        : "The model assigned a suspicious probability from the combined behavioral feature pattern, but no individual high-signal indicator was triggered in this cycle."
                      : "The AI model currently detects no strong indicators of ransomware activity."}
                  </p>

                </div>

              </div>

            </div>

          ) : (

            <div className="no-xai">

              <div className="no-xai-icon">
                🧠
              </div>

              <h3>
                No AI explanation available
              </h3>

              <p>
                XAI factors will appear when the system
                records a non-safe detection.
              </p>

            </div>

          )}

        </section>

        {/* =========================================
            RECENT DETECTION HISTORY
        ========================================= */}

        <section className="detections-panel">

          <div className="detections-header">

            <div>
              <h2>Recent Detection History</h2>

              <p>
                Latest non-safe monitoring detections
              </p>
            </div>

            <div className="history-count">
              {alerts.length} recorded
            </div>

          </div>

          {alerts.length > 0 ? (

            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>TIME</th>
                    <th>RISK</th>
                    <th>PROBABILITY</th>
                    <th>FILES</th>
                    <th>RESPONSE</th>
                  </tr>

                </thead>

                <tbody>

                  {alerts.map((alert, index) => {

                    const probability =
                      Number(alert.probability ?? 0);

                    const probabilityPercent =
                      probability <= 1
                        ? Math.round(probability * 100)
                        : Math.round(probability);

                    const alertClass =
                      getStatusClass(alert.risk_level);

                    return (

                      <tr key={alert.id ?? index}>

                        <td>
                          {alert.timestamp
                            ? new Date(
                                alert.timestamp
                              ).toLocaleTimeString()
                            : "--:--:--"}
                        </td>

                        <td>
                          <span
                            className={`table-risk ${alertClass}`}
                          >
                            {alert.risk_level || "Unknown"}
                          </span>
                        </td>

                        <td>
                          {probabilityPercent}%
                        </td>

                        <td>
                          {alert.files_affected ?? 0}
                        </td>

                        <td>
                          {alert.response_action || "No action"}
                        </td>

                      </tr>

                    );

                  })}

                </tbody>

              </table>

            </div>

          ) : (

            <div className="empty-detections">
              No non-safe detections recorded in the current history.
            </div>

          )}

        </section>

        {/* =========================================
            FOOTER
        ========================================= */}

        <div className="footer">

          <span>
            ● {monitoringActive
              ? "Monitoring active"
              : "Monitoring status unavailable"}
          </span>

          <span>
            Last update: {lastUpdated}
          </span>

        </div>

      </main>

    </div>
  );
}

export default App;
