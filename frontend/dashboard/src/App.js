import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [status, setStatus] = useState("Loading...");
  const [alerts, setAlerts] = useState([]);
  const [lastUpdated, setLastUpdated] = useState("--:--:--");
  const [error, setError] = useState(false);

  // =========================
  // FETCH BACKEND DATA
  // =========================

  const fetchData = async () => {
    try {
      const statusRes = await axios.get(
        "http://localhost:8000/status"
      );

      const alertsRes = await axios.get(
        "http://localhost:8000/alerts"
      );

      setStatus(statusRes.data.latest_risk || "Safe");
      setAlerts(alertsRes.data || []);

      setLastUpdated(
        new Date().toLocaleTimeString()
      );

      setError(false);
    } catch (err) {
      console.error("Backend connection error:", err);

      setError(true);
      setStatus("Backend Offline");
      setAlerts([]);
    }
  };

  useEffect(() => {
    fetchData();

    const interval = setInterval(
      fetchData,
      5000
    );

    return () => clearInterval(interval);
  }, []);

  // =========================
  // LATEST ALERT
  // =========================

  const latestAlert =
    alerts.length > 0 ? alerts[0] : null;

  // =========================
  // RISK SCORE
  // =========================

  let riskScore = 0;

  if (latestAlert) {
    const probability = Number(
      latestAlert.probability
    );

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

  let riskType = status;

  if (latestAlert) {
    riskType =
      latestAlert.risk_level || status;
  }

  // =========================
  // STATUS CLASS
  // =========================

  const getStatusClass = () => {
    const value =
      String(status).toLowerCase();

    if (value === "safe")
      return "safe";

    if (value === "suspicious")
      return "warning";

    if (
      value === "high risk" ||
      value === "high"
    )
      return "danger";

    if (
      value === "backend offline"
    )
      return "offline";

    return "safe";
  };

  // =========================
  // RISK SCORE CLASS
  // =========================

  const getRiskClass = () => {
    if (riskScore >= 75)
      return "danger";

    if (riskScore >= 40)
      return "warning";

    return "safe";
  };

  // =========================
  // XAI FACTORS
  // =========================

  const getFactors = () => {
    if (!latestAlert?.factors) {
      return [];
    }

    if (
      Array.isArray(latestAlert.factors)
    ) {
      return latestAlert.factors;
    }

    return String(
      latestAlert.factors
    )
      .split(",")
      .map((factor) => factor.trim())
      .filter(Boolean);
  };

  const factors = getFactors();

  // =========================
  // RISK CIRCLE
  // =========================

  const riskAngle =
    Math.min(riskScore, 100) * 3.6;

  return (
    <div className="app">

      {/* =================================
          HEADER
      ================================= */}

      <header className="header">

        <div className="header-left">

          <div className="logo-icon">
            <img
              src="/logo.jpeg"
              alt="RansomWatch AI Logo"
            />
          </div>

          <div>
            <h1>
              RansomWatch AI
            </h1>

            <p>
              AI-powered early ransomware detection &<br>
              </br> system monitoring
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
              : String(status).toUpperCase()}

          </div>

          <div className="updated">
            Updated {lastUpdated}
          </div>

        </div>

      </header>


      {/* =================================
          MAIN CONTENT
      ================================= */}

      <main className="content">

        {/* PAGE TITLE */}

        <div className="section-heading">

          <h2>
            System Overview
          </h2>

          <p>
            Real-time ransomware detection
            status
          </p>

        </div>


        {/* =================================
            FOUR TOP CARDS
        ================================= */}

        <div className="cards">


          {/* SYSTEM STATUS */}

          <section
            className={`card status-card ${getStatusClass()}`}
          >

            <div className="card-header">

              <span>
                SYSTEM STATUS
              </span>

              <span className="card-dot">
                ●
              </span>

            </div>


            <div className="status-content">

              <div className="status-icon">
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


            <div className="card-footer">

              <span className="green-dot"></span>

              Sensor monitoring active

            </div>

          </section>


          {/* ACTIVE ALERTS */}

          <section className="card">

            <div className="card-header">

              <span>
                ACTIVE ALERTS
              </span>

              <span className="card-icon red">
                ⚠
              </span>

            </div>


            <div className="alert-number">
              {alerts.length}
            </div>

            <p className="description">
              Detected ransomware alerts
            </p>


            <div className="card-footer red-text">

              {alerts.length > 0
                ? "Threats detected"
                : "No active threats"}

            </div>

          </section>


          {/* RISK SCORE */}

          <section
            className={`card risk-card ${getRiskClass()}`}
          >

            <div className="card-header">

              <span>
                RISK SCORE
              </span>

              <span className="card-icon blue">
                ◉
              </span>

            </div>


            <div
              className="risk-circle"
              style={{
                background: `conic-gradient(
                  ${getRiskClass() === "danger"
                    ? "#c34c3c"
                    : getRiskClass() === "warning"
                    ? "#c58927"
                    : "#397ba8"}
                  0deg,
                  ${getRiskClass() === "danger"
                    ? "#c34c3c"
                    : getRiskClass() === "warning"
                    ? "#c58927"
                    : "#397ba8"}
                  ${riskAngle}deg,
                  #e2e7ea ${riskAngle}deg,
                  #e2e7ea 360deg
                )`
              }}
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


            <div
              className={`risk-label ${getRiskClass()}`}
            >

              {riskScore >= 75
                ? "HIGH RISK"
                : riskScore >= 40
                ? "SUSPICIOUS"
                : "LOW RISK"}

            </div>

          </section>


          {/* RISK TYPE */}

          <section className="card">

            <div className="card-header">

              <span>
                RISK TYPE
              </span>

              <span className="card-icon orange">
                ◆
              </span>

            </div>


            <div
              className={`risk-type ${getRiskClass()}`}
            >
              {riskType}
            </div>


            <p className="description">
              Current detected threat level
            </p>


            <div className="card-footer">
              Based on ML prediction
            </div>

          </section>

        </div>


        {/* =================================
            EXPLAINABLE AI
        ================================= */}

        <section className="xai-panel">

          {/* XAI HEADER */}

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


            <div className="xai-badge">
              AI ANALYSIS
            </div>

          </div>


          {/* XAI CONTENT */}

          {latestAlert && factors.length > 0 ? (

            <div className="xai-content">

              <div className="model-result">

                <span>
                  Model Probability
                </span>

                <strong>
                  {riskScore}%
                </strong>

              </div>


              <p className="factor-heading">
                Top contributing factors
              </p>


              <div className="factors">

                {factors
                  .slice(0, 4)
                  .map(
                    (factor, index) => (

                      <div
                        className="factor"
                        key={index}
                      >

                        <div className="factor-number">
                          {index + 1}
                        </div>

                        <div className="factor-info">

                          <span>
                            {factor}
                          </span>

                          <div className="factor-bar">

                            <div
                              style={{
                                width: `${Math.max(
                                  35,
                                  90 -
                                    index * 15
                                )}%`
                              }}
                            ></div>

                          </div>

                        </div>

                      </div>

                    )
                  )}

              </div>

            </div>

          ) : (

            <div className="xai-empty">

              <div className="empty-brain">
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


        {/* =================================
            BOTTOM STATUS
        ================================= */}

        <div className="bottom-status">

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