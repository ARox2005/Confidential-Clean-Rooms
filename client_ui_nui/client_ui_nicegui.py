# client_ui_nicegui.py
from nicegui import ui
from nicegui import ui, app
import os

# Start the NiceGUI app
# static_dir = os.path.join(os.path.dirname(__file__), 'static')
# app.add_static_files('/static', static_dir)

# @app.on_startup
# def load_custom_css():
#     ui.add_head_html('<link rel="stylesheet" href="/static/index.css">')

import pages.login
import pages.mode_select
import pages.solo_workflow
import pages.collab_workflow

ui.run(title='YellowSense Cleanroom UI', reload=True, port=8501)
