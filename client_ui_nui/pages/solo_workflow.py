# pages/solo_workflow.py
from nicegui import ui
from nicegui.events import UploadEventArguments
import state
import client_crypto
import uuid
import asyncio
import tempfile
import os
import requests
from components.layout import inject_theme

API_URL = "http://localhost:8080"

@ui.page('/solo')
def solo_page():
    inject_theme()
    client_id = state.APP_STATE.get('client_id')
    if not client_id:
        ui.notify('Please login first', color='warning')
        ui.navigate.to('/')
        return
    with ui.column().classes('items-center w-full mt-8'):
        # ui.markdown('# Welcome to **YellowSense Cleanroom UI**!')
        # ui.label('Upload your datasets to analyze fraud patterns in a secure clean room').classes('text-gray-600')
        ui.markdown('# 👤 Solo Workflow')
        ui.markdown('Create a workflow, upload your datasets, then run the workflow.')

        with ui.card().classes('main-card'):
            client_label = ui.markdown(f'Client ID: **{client_id}**')
            workflow_label = ui.label(get_workflow_text())

            def create_workflow():
                wid = str(uuid.uuid4())
                state.APP_STATE['workflow_id'] = wid
                ui.notify(f'Workflow created: {wid}', color='positive')
                workflow_label.set_text(get_workflow_text())

            ui.button('🚀 Create Solo Workflow', on_click=create_workflow).props('flat color=white text-color=white').classes('btn-primary')

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

            # uploader = ui.upload(label='Upload one or more datasets (CSV)', multiple=True)
            uploader = ui.upload(
                label='Upload your files',
                on_upload=handle_upload,
                auto_upload=True,  # This is important!
                multiple=True
            )
            status = ui.label('')
            results_box = ui.markdown('')

            async def run_workflow():
                wid = state.APP_STATE.get('workflow_id')
                if not wid:
                    ui.notify('Create a workflow first.', color='warning')
                    return
                # files = uploader.files
                files = uploaded_file_contents.copy()
                if not files:
                    ui.notify('Please upload at least one dataset.', color='warning')
                    return

                # Get executor pubkey (blocking call executed in thread to avoid blocking UI)
                status.set_text('⏳ Fetching executor public key...')
                try:
                    pubkey = await asyncio.to_thread(client_crypto.get_executor_pubkey)
                    state.APP_STATE['pubkey'] = pubkey
                except Exception as e:
                    status.set_text(f'❌ Failed to fetch executor public key: {e}')
                    return

                status.set_text(f'⏳ Encrypting and uploading {len(files)} file(s)...')
                uploaded_paths = []
                # For each uploaded NiceGUI file, save to temp file and call your existing encrypt_and_upload
                for f in files:
                    # f.content is bytes for NiceGUI UploadFile; if not present, fallback to .data
                    # content = None
                    # if hasattr(f, 'content'):
                    #     content = f.content
                    # elif hasattr(f, 'data'):
                    #     content = f.data
                    # else:
                    #     # read from file-like interface
                    #     try:
                    #         content = f.read()
                    #     except Exception:
                    #         content = None
                    content = f.get('content')
                    status.set_text('⏳ Processing file: ' + f['name'])
                    if content is None:
                        ui.notify(f'Could not read uploaded file {f['name']}', color='negative')
                        continue

                    tmp = tempfile.NamedTemporaryFile(delete=False)
                    try:
                        tmp.write(content)
                        tmp.flush()
                        tmp.close()
                        # call encrypt_and_upload in a thread because it uses blocking requests
                        try:
                            result = await asyncio.to_thread(client_crypto.encrypt_and_upload, wid, pubkey, tmp.name, f['name'], client_id)
                            # result structure depends on your client_crypto implementation
                            uploaded_paths.append(result.get('ciphertext_gcs') or result.get('ciphertext_gcs', ''))
                        except Exception as e:
                            ui.notify(f'Upload failed for {f['name']}: {e}', color='negative')
                        finally:
                            os.unlink(tmp.name)
                    except Exception as ex:
                        ui.notify(f'Failed to write temp file for {f['name']}: {ex}', color='negative')

                if not uploaded_paths:
                    # status.set_text('❌ No files uploaded successfully.')
                    return

                status.set_text('⏳ Registering workflow with orchestrator...')
                payload = {'workflow_id': wid, 'creator': client_id, 'collaborator': [client_id]}
                try:
                    # resp = requests.post(f'{API_URL}/workflows', params=payload)
                    resp = await asyncio.to_thread(requests.post, f'{API_URL}/workflows', params=payload)
                    if resp.status_code != 200:
                        status.set_text(f'❌ Failed to register workflow: {resp.text}')
                        return
                except Exception as e:
                    status.set_text(f'❌ Failed to register workflow: {e}')
                    return

                # Approve workflow for self
                try:
                    # requests.post(f'{API_URL}/workflows/{wid}/approve', params={'workflow_id': wid, 'client_id': client_id})
                    resp = await asyncio.to_thread(requests.post, f'{API_URL}/workflows/{wid}/approve', params={'workflow_id': wid, 'client_id': client_id})
                except Exception:
                    pass

                status.set_text('⏳ Executing workflow...')
                try:
                    # run_resp = requests.post(f'{API_URL}/workflows/{wid}/run', params={'workflow_id': wid, 'creator': client_id, 'collaborators': [client_id]})
                    run_resp = await asyncio.to_thread(requests.post, f'{API_URL}/workflows/{wid}/run', params={'workflow_id': wid, 'creator': client_id, 'collaborators': [client_id]})
                    if run_resp.status_code != 200:
                        status.set_text(f'❌ Execution failed: {run_resp.text}')
                        return
                except Exception as e:
                    status.set_text(f'❌ Execution failed: {e}')
                    return

                status.set_text('⏳ Fetching logs...')
                try:
                    # logs_resp = requests.get(f'{API_URL}/logs/{wid}')
                    logs_resp = await asyncio.to_thread(requests.get, f'{API_URL}/logs/{wid}')
                    if logs_resp.status_code == 200:
                        logs = logs_resp.json().get('logs', [])
                        results_box.set_text('### 📜 Execution Logs\n\n' + '\n'.join(logs))
                    else:
                        results_box.set_text('⚠️ Failed to fetch logs')
                except Exception:
                    results_box.set_text('⚠️ Failed to fetch logs')

                # Fetch result files
                status.set_text('⏳ Fetching result files...')
                try:
                    # res = requests.get(f'{API_URL}/workflows/{wid}/result')
                    res = await asyncio.to_thread(requests.get, f'{API_URL}/workflows/{wid}/result')
                    if res.status_code != 200:
                        status.set_text(f'❌ Failed to fetch results: {res.text}')
                        return
                    rows = res.json()
                    results = rows if isinstance(rows, list) else [rows]
                    if not results:
                        status.set_text('No result files found.')
                        return
                    # render lightweight result summary with download links (if present)
                    md = '### 📦 Workflow Results\n'
                    for r in results:
                        path = r.get('result_path') or r.get('result_path', '')
                        name = path.split('/')[-1] if path else r.get('filename', 'result')
                        dl = r.get('download_url') or ''
                        md += f'- **{name}**'
                        if dl:
                            md += f' — [Download]({dl})'
                        md += '\n'
                    results_box.set_text(md)
                    uploaded_file_contents.clear()
                    status.set_text('✅ Workflow executed successfully!')
                except Exception as e:
                    status.set_text(f'❌ Failed to fetch results: {e}')

            ui.button('▶️ Run Solo Workflow', on_click=run_workflow).props('flat color=white text-color=white').classes('btn-primary')
            ui.button('Back to Mode Select', on_click=lambda: ui.navigate.to('/mode')).props('flat color=white text-color=white').classes('btn-primary')

        ui.markdown('')
        ui.link('Home', '/')
        ui.link('Mode select', '/mode')

def get_workflow_text():
    wid = state.APP_STATE.get('workflow_id')
    return f'Workflow ID: {wid}' if wid else 'No workflow created yet.'
