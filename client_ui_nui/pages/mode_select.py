# pages/mode_select.py
from nicegui import ui
import state
from components.layout import inject_theme

@ui.page('/mode')
def mode_select():
    inject_theme()
    with ui.column().classes('items-center w-full mt-8'):
        ui.markdown('# Welcome to **YellowSense Cleanroom UI**!')
        ui.label('Upload your datasets to analyze fraud patterns in a secure clean room').classes('text-gray-600')
        with ui.card().classes('main-card'):
            client_id = state.APP_STATE.get('client_id')
            if not client_id:
                ui.notify('Please login first', color='warning')
                ui.navigate.to('/')
                return

            ui.markdown(f'##👋 Welcome, **{client_id}**').classes('text-center w-full')
            ui.markdown('Choose a mode to continue:').classes('text-center w-full')

            with ui.row().classes('items-stretch gap-4'):
                with ui.card().classes('main-card'):#.style('flex:1;'):
                    ui.markdown('#### Solo Mode')
                    ui.markdown('Run a workload with only your dataset(s).')
                    ui.button('Go to Solo', on_click=lambda: ui.navigate.to('/solo')).props('flat color=white text-color=white').classes('btn-primary') #props('color=primary')

                with ui.card().classes('main-card'):#.style('flex:1;'):
                    ui.markdown('#### Collaboration Mode')
                    ui.markdown('Invite collaborators and run a joint workflow.')
                    ui.button('Go to Collaboration', on_click=lambda: ui.navigate.to('/collab')).props('flat color=white text-color=white').classes('btn-primary')#.props('color=primary')

            ui.button('Logout', on_click=lambda: logout()).props('flat color=white text-color=white').classes('btn-primary mt-6')
            ui.link('Back to login', '/')

def logout():
    state.APP_STATE['client_id'] = None
    state.APP_STATE['workflow_id'] = None
    ui.open('/')
