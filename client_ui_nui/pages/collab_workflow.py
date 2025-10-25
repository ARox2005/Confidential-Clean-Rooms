# pages/collab_workflow.py
from nicegui import ui
from nicegui.events import UploadEventArguments
import state
import client_crypto
import uuid
import asyncio
import tempfile
import os
import requests
from components.layout import inject_theme, navbar

API_URL = "http://localhost:8080"

@ui.page('/collab')
def collab_page():
    inject_theme()
    client_id = state.APP_STATE.get('client_id')
    if not client_id:
        ui.notify('Please login first', color='warning')
        ui.navigate.to('/')
        return

    with ui.column().classes('items-center w-full mt-8'):
        ui.markdown('# 🤝 Collaborative Workflow')
        # role = ui.radio(['Creator', 'Collaborator'], label='Login as:', value='Creator')
        # role = ui.select(['Creator', 'Collaborator'], label='Login as:', value='Creator')
        with ui.card().classes('main-card'):
            role = ui.select(
                ['Creator', 'Collaborator'],
                label='Login as:',
                value='Creator',
                on_change=lambda e: on_role_change(e.value)
            )
            status = ui.label('')
            results_box = ui.markdown('')

        # Creator view
            with ui.element('div').classes('space-y-4 mt-4') as creator_area:
                creator_id_input = ui.input(label='Your ID (Creator)', value=client_id)
                workflow_label = ui.label(get_workflow_text())
                with ui.row():
                    ui.button('🆕 Create New Workflow', on_click=lambda: create_workflow(creator_id_input.value)).props('flat color=white text-color=white').classes('btn-primary')
                    # ui.input(placeholder='Or enter existing Workflow ID to continue', on_change=None, id='existing_workflow')
                    ui.input(placeholder='Or enter existing Workflow ID to continue', on_change=None).props('id=existing_workflow')

                ui.markdown('---')

                collaborators_input = ui.input(label='Add Collaborator IDs (comma-separated)', value='ClientB')

                uploaded_file_contents = []

                async def handle_upload(e: UploadEventArguments):
                    """Called once for each uploaded file."""
                    try:
                        # e.file is a SpooledTemporaryFile (file-like object)
                        content = await e.file.read()
                        
                        # Store the content for later
                        uploaded_file_contents.append({
                            'name': e.file.name,
                            'content': content
                        })
                        ui.notify(f'Successfully uploaded {e.file.name}')
                    except Exception as err:
                        ui.notify(f'Failed to read {e.file.name}: {err}', type='negative')

                # uploader = ui.upload(label='Upload creator datasets (CSV)', multiple=True)
                uploader = ui.upload(
                    label='Upload your files',
                    on_upload=handle_upload,
                    auto_upload=True,  # This is important!
                    multiple=True
                )
                with ui.row().classes('space-x-4'):
                    ui.button('⬆️ Upload Creator Datasets', on_click=lambda: asyncio.create_task(upload_creator_files(creator_id_input.value, uploader))).props('flat color=white text-color=white').classes('btn-primary')

                    ui.button('✅ Submit Workflow', on_click=lambda: asyncio.create_task(submit_workflow(creator_id_input.value, collaborators_input.value))).props('flat color=white text-color=white').classes('btn-primary')

                ui.markdown('---')

                run_workflow_id_input = ui.input(label='Enter Workflow ID to Run', value=state.APP_STATE.get('workflow_id') or '')
                ui.button('▶️ Run Collaborative Workflow', on_click=lambda: asyncio.create_task(run_collab_workflow(creator_id_input.value, collaborators_input.value, run_workflow_id_input.value))).props('flat color=white text-color=white').classes('btn-primary')

            # Collaborator view
            with ui.element('div').classes('mt-4 hidden') as collaborator_area:
                collab_id_input = ui.input(label='Your ID (Collaborator)', value='ClientB')
                workflow_id_input = ui.input(label='Workflow ID to join')
                collab_uploader = ui.upload(label='Upload your datasets (CSV)', multiple=True)
                ui.button('✅ Approve & Upload Datasets', on_click=lambda: asyncio.create_task(collaborator_upload(collab_id_input.value, workflow_id_input.value, collab_uploader))).props('color=primary')

            # Toggle visibility on role change
            def on_role_change(r):
                if r == 'Creator':
                    creator_area.classes(remove='hidden')
                    collaborator_area.classes(add='hidden')
                else:
                    creator_area.classes(add='hidden')
                    collaborator_area.classes(remove='hidden')
                status.set_text('')

            # role.on_change(lambda e: on_role_change(e.value))

            ui.button('Back to Mode Select', on_click=lambda: ui.navigate.to('/mode')).props('flat color=white text-color=white').classes('btn-primary')

            async def create_workflow(creator_id):
                wid = str(uuid.uuid4())
                state.APP_STATE['workflow_id'] = wid
                ui.notify(f'Workflow created: {wid}', color='positive')
                workflow_label.set_text(get_workflow_text())

            async def upload_creator_files(creator_id, uploader):
                wid = state.APP_STATE.get('workflow_id')
                if not wid:
                    ui.notify('Create or enter workflow ID first', color='warning')
                    return
                files = uploader.files
                if not files:
                    ui.notify('No files selected', color='warning')
                    return

                status.set_text('⏳ Uploading creator datasets...')
                try:
                    pubkey = await asyncio.to_thread(client_crypto.get_executor_pubkey)
                except Exception as e:
                    status.set_text(f'❌ Failed to get executor public key: {e}')
                    return

                uploaded = 0
                for f in files:
                    content = getattr(f, 'content', None) or getattr(f, 'data', None)
                    if content is None:
                        try:
                            content = f.read()
                        except Exception:
                            content = None
                    if content is None:
                        ui.notify(f'Could not read {f.name}', color='negative')
                        continue

                    tmp = tempfile.NamedTemporaryFile(delete=False)
                    try:
                        tmp.write(content)
                        tmp.flush()
                        tmp.close()
                        try:
                            await asyncio.to_thread(client_crypto.encrypt_and_upload, wid, pubkey, tmp.name, f.name, creator_id)
                            uploaded += 1
                        except Exception as e:
                            ui.notify(f'Upload failed for {f.name}: {e}', color='negative')
                        finally:
                            os.unlink(tmp.name)
                    except Exception as ex:
                        ui.notify(f'Failed to write temp file for {f.name}: {ex}', color='negative')

                status.set_text(f'Uploaded {uploaded} files.')
                if uploaded > 0:
                    # store dataset paths could be added in state if needed
                    ui.notify('Creator files uploaded ✅', color='positive')

            async def submit_workflow(creator_id, collab_csv):
                wid = state.APP_STATE.get('workflow_id')
                if not wid:
                    ui.notify('No workflow created/entered', color='warning')
                    return
                collaborator_list = [creator_id] + [c.strip() for c in collab_csv.split(',') if c.strip()]
                params = {'workflow_id': wid, 'creator': creator_id, 'collaborator': collaborator_list}
                try:
                    resp = requests.post(f'{API_URL}/workflows', params=params)
                    if resp.status_code == 200:
                        # auto-approve creator
                        requests.post(f'{API_URL}/workflows/{wid}/approve', params={'workflow_id': wid, 'client_id': creator_id})
                        ui.notify('Workflow submitted ✅ Waiting for collaborator approvals.', color='positive')
                    else:
                        ui.notify(f'Error submitting workflow: {resp.text}', color='negative')
                except Exception as e:
                    ui.notify(f'Error submitting workflow: {e}', color='negative')

            async def run_collab_workflow(creator_id, collab_csv, workflow_to_run):
                wid = workflow_to_run or state.APP_STATE.get('workflow_id')
                if not wid:
                    ui.notify('Enter workflow id', color='warning')
                    return
                collaborator_list = [creator_id] + [c.strip() for c in collab_csv.split(',') if c.strip()]
                try:
                    resp = requests.post(f'{API_URL}/workflows/{wid}/run', params={'workflow_id': wid, 'creator': creator_id, 'collaborators': collaborator_list})
                    if resp.status_code == 403:
                        ui.notify('Workflow not yet approved by all collaborators.', color='warning')
                        return
                    elif resp.status_code != 200:
                        ui.notify(f'Execution failed: {resp.text}', color='negative')
                        return
                except Exception as e:
                    ui.notify(f'Execution failed: {e}', color='negative')
                    return

                status.set_text('⏳ Workflow running... Fetching logs...')
                try:
                    logs_resp = requests.get(f'{API_URL}/logs/{wid}')
                    if logs_resp.status_code == 200:
                        logs = logs_resp.json().get('logs', [])
                        results_box.set_text('### 📜 Execution Logs\n\n' + '\n'.join(logs))
                    else:
                        results_box.set_text('⚠️ Failed to fetch logs')
                except Exception:
                    results_box.set_text('⚠️ Failed to fetch logs')

                # fetch results (same pattern as Solo)
                try:
                    res = requests.get(f'{API_URL}/workflows/{wid}/result')
                    if res.status_code == 200:
                        rows = res.json()
                        results = rows.get('results', []) if isinstance(rows, dict) else rows
                        if not results:
                            status.set_text('No result files found.')
                            return
                        md = '### 📦 Workflow Results\n'
                        for r in results:
                            path = r.get('result_path') or ''
                            name = path.split('/')[-1] if path else r.get('filename', 'result')
                            dl = r.get('download_url') or ''
                            md += f'- **{name}**'
                            if dl:
                                md += f' — [Download]({dl})'
                            md += '\n'
                        results_box.set_text(md)
                        status.set_text('✅ Workflow executed successfully!')
                    else:
                        status.set_text(f'❌ Failed to fetch results: {res.text}')
                except Exception as e:
                    status.set_text(f'❌ Failed to fetch results: {e}')

            async def collaborator_upload(collab_id, workflow_id, uploader):
                if not workflow_id:
                    ui.notify('Enter a Workflow ID to join', color='warning')
                    return
                files = uploader.files
                if not files:
                    ui.notify('No files selected', color='warning')
                    return

                try:
                    pubkey = await asyncio.to_thread(client_crypto.get_executor_pubkey)
                except Exception as e:
                    ui.notify(f'Failed to fetch executor pubkey: {e}', color='negative')
                    return

                uploaded = 0
                for f in files:
                    content = getattr(f, 'content', None) or getattr(f, 'data', None)
                    if content is None:
                        try:
                            content = f.read()
                        except Exception:
                            content = None
                    if content is None:
                        ui.notify(f'Could not read {f.name}', color='negative')
                        continue

                    tmp = tempfile.NamedTemporaryFile(delete=False)
                    try:
                        tmp.write(content)
                        tmp.flush()
                        tmp.close()
                        try:
                            await asyncio.to_thread(client_crypto.encrypt_and_upload, workflow_id, pubkey, tmp.name, f.name, collab_id)
                            uploaded += 1
                        except Exception as e:
                            ui.notify(f'Upload failed for {f.name}: {e}', color='negative')
                        finally:
                            os.unlink(tmp.name)
                    except Exception as ex:
                        ui.notify(f'Failed to write temp file for {f.name}: {ex}', color='negative')

                if uploaded > 0:
                    # Approve collaborator
                    try:
                        resp = requests.post(f'{API_URL}/workflows/{workflow_id}/approve', params={'client_id': collab_id})
                        if resp.status_code == 200:
                            ui.notify('Uploaded & approved workflow successfully!', color='positive')
                        else:
                            ui.notify(f'Approval failed: {resp.text}', color='negative')
                    except Exception as e:
                        ui.notify(f'Approval failed: {e}', color='negative')

def get_workflow_text():
    wid = state.APP_STATE.get('workflow_id')
    return f'Workflow ID: {wid}' if wid else 'No workflow created yet.'