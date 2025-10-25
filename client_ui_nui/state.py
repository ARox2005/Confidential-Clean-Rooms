# state.py
# Simple process-global state. NiceGUI runs in a single process by default,
# so this is sufficient for session-like storage for a demo / single-user usage.
APP_STATE = {
    'client_id': None,
    'workflow_id': None,
    'pubkey': None
}
