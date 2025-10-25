from nicegui import ui

def inject_theme():
    ui.add_head_html("""
    <style>
    /* Google Font Import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    body {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #fffdf5, #ffffff);
        color: #3C3C3C;
    }

    /* --- NAVBAR --- */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 32px;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    .navbar .brand {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        color: #f6a700;
    }
    .navbar .subtitle {
        font-size: 0.9rem;
        color: #888;
    }
    
    /* --- BUTTONS --- */
    .btn-primary {
        background-color: #f6a700 !important;
        color: white !important;
        border-radius: 8px; !important;
        font-weight: 600; !important;
        text-transform: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .btn-primary:hover {
        background-color: #e09500 !important;
        transform: translateY(-1px);
    }
    
    /* --- CARDS & CONTAINERS --- */
    .main-card {
        background-color: white;
        border-radius: 20px;
        border: 1px solid #F0F0F0;
        box-shadow: 0 5px 25px rgba(0,0,0,0.05);
        padding: 32px;
        margin: 2rem auto;
        max-width: 800px;
        /* ✨ NEW: Add transition for the hover effect */
        transition: all 0.3s ease-in-out; 
    }

    /* ✨ NEW: Add the pop-out and yellow glow effect on hover */
    .main-card:hover {
        transform: translateY(-5px); /* Lifts the card up */
        box-shadow: 0 10px 30px rgba(246, 167, 0, 0.2); /* Yellow glow */
    }

    /* --- Inner Selectable Boxes --- */
    .role-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 24px;
        border: 1px solid #E0E0E0;
        border-radius: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .role-box:hover {
        transform: translateY(-3px);
        /* ✨ NEW: Enhanced the role-box shadow with a subtle yellow glow */
        box-shadow: 0 6px 20px rgba(246, 167, 0, 0.15);
    }
    .role-box.selected {
        border: 2px solid #f6a700;
        background-color: #fffaf0;
    }

    /* --- TYPOGRAPHY --- */
    h1, h2, h3, .page-title {
        color: #8C9E48; 
        font-weight: 700;
    }
    </style>
    """)

def navbar():
    with ui.row().classes('navbar'):
        with ui.column().classes('brand'):
            ui.label('🟡 YellowSense').classes('text-lg')
            ui.label('Confidential Clean Room').classes('subtitle')
        with ui.row().classes('actions'):
            ui.button('📊 Dashboard', on_click=lambda: ui.navigate.to('/mode')).props('flat')
            ui.button('▶ New Workflow', on_click=lambda: ui.navigate.to('/mode')).classes('btn-primary')
