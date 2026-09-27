from alert_builder import build_alert

feature_row = {
    "file_modified_rate": 25,
    "file_created_rate": 10,
    "file_renamed_rate": 15,
    "file_deleted_rate": 5,
    "new_process_rate": 3,
    "avg_cpu": 75,
    "avg_mem": 60
}

alert = build_alert(feature_row)

print(alert)