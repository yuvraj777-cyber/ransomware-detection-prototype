import React, { useEffect, useState } from "react";
import axios from "axios";
function App() {
const [status, setStatus] = useState("Loading...");
const [alerts, setAlerts] = useState([]);
const fetchData = async () => {
const statusRes = await axios.get("http://localhost:8000/status");
const alertsRes = await axios.get("http://localhost:8000/alerts");
setStatus(statusRes.data.latest_risk);
setAlerts(alertsRes.data);
};
useEffect(() => {
fetchData();
const interval = setInterval(fetchData, 5000); // poll every 5s
return () => clearInterval(interval);
}, []);
const riskColor = { "Safe": "green", "Suspicious": "orange", "High Risk": "red" };
return (
<div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
<h1>Ransomware Detection Dashboard</h1>
<h2 style={{ color: riskColor[status] || "gray" }}>Current Status: {status}</h2>
<h3>Recent Alerts</h3>
<table border="1" cellPadding="8" style={{ borderCollapse: "collapse", width: "100%" }}>
<thead>
<tr><th>Time</th><th>Risk Level</th><th>Probability</th><th>Top Factors</th></tr>
</thead>
<tbody>
{alerts.map((a) => (
<tr key={a.id}>
<td>{a.timestamp}</td>
<td style={{ color: riskColor[a.risk_level] || "black" }}>{a.risk_level}</td>
<td>{a.probability}</td>
<td>{a.factors.join(", ")}</td>
</tr>
))}
</tbody>
</table>
</div>
);
}
export default App;