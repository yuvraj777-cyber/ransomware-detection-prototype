import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [status, setStatus] = useState("Loading...");
  const [alerts, setAlerts] = useState([]);
  const [lastUpdated, setLastUpdated] = useState("--:--:--");
  const [error, setError] = useState(false);

  // =========================
  // FETCH DATA FROM BACKEND
  // =========================

  const fetchData = async () => {
    try {
      const statusRes = await axios.get("http://localhost:8000/status");
      const alertsRes = await axios.get("http://localhost:8000/alerts");

      setStatus(statusRes.data.latest_risk);
      setAlerts(alertsRes.data);

      setLastUpdated(new Date().toLocaleTimeString());
      setError(false);
    } catch (err) {
      console.error("Backend connection error:", err);

      setError(true);
      setStatus("Backend Offline");
    }
  };

  // =========================
  // AUTO UPDATE EVERY 5 SEC
  // =========================

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 5000);

    return () => clearInterval(interval);
  }, []);

  // =========================
  // LATEST ALERT
  // =========================

  const latestAlert = alerts.length > 0 ? alerts[0] : null;

  // =========================
  // RISK SCORE
  // =========================

  let riskScore = 0;

  if (latestAlert) {
    const probability = Number(latestAlert.probability);

    if (!isNaN(probability)) {
      riskScore =
        probability <= 1
          ? Math.round(probability * 100)
          : Math.round(probability);
    }
  }

  // =========================
  // RISK TYPE
  // =========================

  let riskType = "Safe";

  if (latestAlert?.risk_level) {
    riskType = latestAlert.risk_level;
  } else if (status && status !== "Loading...") {
    riskType = status;
  }

  // =========================
  // ACTIVE ALERTS
  // =========================

  const activeAlerts = alerts.length;

  // =========================
  // STATUS CLASS
  // =========================

  const getStatusClass = () => {
    const value = status?.toLowerCase();

    if (value === "safe") return "safe";

    if (
      value === "suspicious" ||
      value === "medium"
    ) {
      return "warning";
    }

    if (
      value === "high risk" ||
      value === "high" ||
      value === "critical"
    ) {
      return "danger";
    }

    if (value === "backend offline") {
      return "offline";
    }

    return "safe";
  };

  // =========================
  // RISK CLASS
  // =========================

  const getRiskClass = () => {
    if (riskScore >= 75) return "danger";

    if (riskScore >= 40) return "warning";

    return "safe";
  };

  // =========================
  // FACTORS
  // =========================

  const getFactors = () => {
    if (!latestAlert?.factors) {
      return [
        "No contributing factors available"
      ];
    }

    if (Array.isArray(latestAlert.factors)) {
      return latestAlert.factors;
    }

    return String(latestAlert.factors)
      .split(",")
      .map((factor) => factor.trim())
      .filter(Boolean);
  };

  const factors = getFactors();

  // =========================
  // RISK CIRCLE
  // =========================

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

      {/* =========================
          HEADER
      ========================= */}

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


      {/* =========================
          MAIN CONTENT
      ========================= */}

      <main className="main-content">

        <div className="section-title">
          <h2>System Overview</h2>

          <p>
            Real-time ransomware detection status
          </p>
        </div>


        {/* =========================
            FOUR MAIN CARDS
        ========================= */}

        <div className="overview-grid">


          {/* SYSTEM STATUS */}

          <div
            className={`overview-card status-card ${getStatusClass()}`}
          >

            <div className="card-top">

              <span>
                SYSTEM STATUS
              </span>

              <div className="card-icon green-icon">
                ●
              </div>

            </div>

            <div className="status-main">

              <div className="status-circle">
                ✓
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
              Sensor monitoring active
            </div>

          </div>


          {/* ACTIVE ALERTS */}

          <div className="overview-card">

            <div className="card-top">

              <span>
                ACTIVE ALERTS
              </span>

              <div className="card-icon alert-icon">
                ⚠
              </div>

            </div>

            <div className="number">
              {activeAlerts}
            </div>

            <p className="description">
              Detected ransomware alerts
            </p>

            <div className="card-bottom alert-bottom">
              {activeAlerts > 0
                ? "Attention required"
                : "No active threats"}
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
              {riskScore >= 75
                ? "HIGH RISK"
                : riskScore >= 40
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


        {/* =========================
            XAI SECTION
        ========================= */}

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
                  Top Contributing Factors
                </h3>

                <p className="factor-subtitle">
                  These system behaviors contributed
                  to the model's prediction.
                </p>


                <div className="factor-list">

                  {factors
                    .slice(0, 4)
                    .map((factor, index) => {

                      const width =
                        Math.max(
                          35,
                          90 - index * 15
                        );

                      return (

                        <div
                          className="factor-row"
                          key={index}
                        >

                          <div className="factor-number">
                            {index + 1}
                          </div>

                          <div className="factor-info">

                            <div className="factor-name">
                              {factor}
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

                    })}

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

                    The AI model detected
                    {riskScore >= 75
                      ? " several behaviors strongly associated with ransomware activity."
                      : riskScore >= 40
                      ? " some behaviors that may indicate suspicious activity."
                      : " no strong indicators of ransomware activity."}

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
                XAI factors will appear when
                the system detects an event.
              </p>

            </div>

          )}

        </section>


        {/* =========================
            FOOTER
        ========================= */}

        <div className="footer">

          <span>
            ● Monitoring active
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