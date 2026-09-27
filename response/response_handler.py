import logging
import psutil

logging.basicConfig(
    filename="response_log.txt",
    level=logging.INFO,
    format="%(asctime)s %(message)s"
)


def handle_response(alert: dict, test_process_name: str = None):
    level = alert["risk_level"]

    if level == "Safe":
        logging.info(
            f"SAFE — normal activity. Probability: {alert['probability']}"
        )
        return {"action": "none"}

    elif level == "Suspicious":
        logging.warning(
            f"SUSPICIOUS — increased monitoring. "
            f"Factors: {alert['main_contributing_indicators']}"
        )
        return {
            "action": "warn",
            "message": "Suspicious activity detected — monitoring increased."
        }

    elif level == "High Risk":
        logging.critical(
            f"HIGH RISK — {alert['main_contributing_indicators']}"
        )

        action_taken = "alert_only"

        # Controlled mitigation demo.
        # ONLY target a designated test process.
        if test_process_name:
            for proc in psutil.process_iter(["pid", "name"]):
                if proc.info["name"] == test_process_name:
                    proc.terminate()
                    action_taken = (
                        f"terminated_test_process:{test_process_name}"
                    )
                    logging.critical(
                        f"Controlled mitigation: terminated "
                        f"{test_process_name} (pid {proc.info['pid']})"
                    )

        return {
            "action": "high_risk_alert",
            "mitigation": action_taken,
            "message": (
                f"HIGH RISK — ransomware-like activity detected. "
                f"Indicators: {alert['main_contributing_indicators']}"
            )
        }