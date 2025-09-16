from ai_proxy_admin_dashboard.sqlite_logger import init_db, log_masking_event

init_db()
log_masking_event("api_keys", "txt", 1)
print("Added a test log for api_keys in txt file.")