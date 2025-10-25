# pages/login.py
from nicegui import ui
import state
from components.layout import inject_theme, navbar

@ui.page('/')
def login_page():
    inject_theme()
    # navbar()
    with ui.column().classes('items-center w-full mt-8'):
        ui.markdown('# Welcome to **YellowSense Cleanroom UI**!')
        ui.label('Upload your datasets to analyze fraud patterns in a secure clean room').classes('text-gray-600')
        with ui.card().classes('main-card'):
            ui.markdown('### Login').classes('text-center w-full')
            ui.markdown('Enter your **Client ID** to continue.')

            client_input = ui.input(label='Client ID', placeholder='e.g. Auditor').props('autofocus')
            status = ui.label('')

            def on_continue():
                cid = client_input.value.strip()
                if not cid:
                    status.set_text('Please enter a client ID.')
                    return
                state.APP_STATE['client_id'] = cid
                # clear any previous workflow id stored
                state.APP_STATE['workflow_id'] = None
                status.set_text(f'Hello, {cid} — redirecting...')
                # ui.open('/mode')  # navigate to mode selection
                ui.navigate.to('/mode')

            ui.button('Continue', on_click=on_continue).props('flat color=white text-color=white').classes('btn-primary')
            # ui.link('Back to root', '/')
