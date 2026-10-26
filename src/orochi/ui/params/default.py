
par = {
    "server": {"value": "127.0.0.1"},
    # "optuna_dashboard_url":{"value":r"http://127.0.0.1:8080/"},
    "viewer_auto_update":{"value":False},
    "viewer_update_time":{"value":10.},
    }

par_key_info = {
    "server": {"value": [str, None, 1]},
    "optuna_dashboard_url":{"value": [str, None, 1]},
    "viewer_auto_update":{"value": [bool, None, 1]},
    "viewer_update_time":{"value": [float, None, 1]},
}
