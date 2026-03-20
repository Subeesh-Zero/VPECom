def start_my_app():
    import os
    import json
    import base64
    import sys
    import subprocess
    import webbrowser
    import time
    import logging
    import traceback
    from threading import Thread, Timer
    import tempfile
    from pathlib import Path
    import signal
    import atexit
    import hashlib
    import re
    
    global flask_thread, flask_app
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('run.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    def is_frozen():
        return getattr(sys, 'frozen', False)

    def get_base_path():
        if is_frozen():
            return sys._MEIPASS
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def install_libs():
        if is_frozen():
            logger.info("Running as EXE, skipping auto-install")
            return
        
        logger.info("Running as script, checking dependencies...")
        
        required = [
            ("flask", "Flask"),
            ("requests", "requests"),
            ("pillow", "PIL")
        ]
        
        for package, import_name in required:
            try:
                __import__(import_name if package == "pillow" else package)
                logger.info(f"✓ {package} is already installed")
            except ImportError:
                logger.info(f"Installing {package}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    logger.info(f"✓ {package} installed successfully")
                except Exception as e:
                    logger.error(f"Failed to install {package}: {e}")
                    try:
                        subprocess.check_call(["pip3", "install", package])
                    except:
                        logger.error(f"Please install {package} manually: pip install {package}")

    install_libs()

    try:
        from flask import Flask, request, jsonify, render_template_string
        import requests
        logger.info("All imports successful")
    except ImportError as e:
        logger.error(f"Import failed: {e}")
        if is_frozen():
            logger.error("EXE is missing dependencies. Rebuild with proper hidden imports.")
        else:
            logger.error("Run: pip install flask requests pillow")
        sys.exit(1)

    if is_frozen():
        CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.vpecom')
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, exist_ok=True)
        CONFIG_FILE = os.path.join(CONFIG_DIR, "shop_config.json")
        logger.info(f"EXE mode: Config stored in {CONFIG_FILE}")
    else:
        CONFIG_FILE = "shop_config.json"
        logger.info(f"Script mode: Config stored in {CONFIG_FILE}")

    flask_app = Flask(__name__)

    # Helper functions for file naming and deletion
    def clean_filename(text):
        """Clean text to create safe filenames"""
        if not text:
            return ""
        # Remove special characters and replace spaces with underscores
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text[:50].strip('_').lower()  # Limit length
    
    def generate_filename(title, description, timestamp, suffix):
        """Generate consistent filename for all uploads"""
        title_part = clean_filename(title)[:20]
        desc_part = clean_filename(description)[:15]
        filename = f"{title_part}_{desc_part}_{timestamp}_{suffix}"
        return hashlib.md5(filename.encode()).hexdigest()[:12] + ".webp"
    
    def extract_image_path_from_url(url, repo):
        """Extract relative path from raw GitHub URL"""
        if not url:
            return None
        pattern = rf"https://raw\.githubusercontent\.com/{re.escape(repo)}/main/(.+)"
        match = re.match(pattern, url)
        return match.group(1) if match else None

    SETUP_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Setup</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            body {
                background: #f5f5f5;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .setup-container {
                width: 100%;
                max-width: 480px;
            }
            
            .setup-card {
                background: white;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            .logo {
                margin-bottom: 30px;
            }
            
            .logo-text {
                font-size: 24px;
                font-weight: 600;
                color: #2563eb;
            }
            
            .setup-title {
                font-size: 20px;
                font-weight: 600;
                color: #1F2937;
                margin-bottom: 10px;
            }
            
            .setup-subtitle {
                color: #6B7280;
                margin-bottom: 32px;
                line-height: 1.6;
            }
            
            .input-group {
                margin-bottom: 20px;
                text-align: left;
            }
            
            .input-label {
                display: block;
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 8px;
            }
            
            .input-field {
                width: 100%;
                padding: 12px 16px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 15px;
                transition: all 0.3s ease;
                background: white;
            }
            
            .input-field:focus {
                outline: none;
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }
            
            .setup-btn {
                width: 100%;
                padding: 12px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                transition: all 0.3s ease;
                margin-top: 10px;
            }
            
            .setup-btn:hover {
                background: #1d4ed8;
            }
            
            .tip-box {
                background: #f8f9fa;
                border-radius: 6px;
                padding: 16px;
                margin-top: 24px;
                text-align: left;
                border-left: 4px solid #2563eb;
            }
            
            .tip-title {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            
            .tip-text {
                font-size: 13px;
                color: #6B7280;
                line-height: 1.5;
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        <div class="setup-container">
            <div class="setup-card">
                <div class="logo">
                    <div class="logo-text">ProjectAxis Admin</div>
                </div>
                
                <h2 class="setup-title">Connect Your Store</h2>
                <p class="setup-subtitle">Enter your GitHub details to sync products</p>
                
                <div class="input-group">
                    <label class="input-label">
                        <i class="fas fa-folder"></i> Repository Path
                    </label>
                    <input type="text" id="repo" class="input-field" 
                        placeholder="username/repository" 
                        value="Subeesh/Shop">
                </div>
                
                <div class="input-group">
                    <label class="input-label">
                        <i class="fas fa-key"></i> GitHub Token
                    </label>
                    <input type="password" id="token" class="input-field" 
                        placeholder="ghp_your_token_here">
                </div>
                
                <button class="setup-btn" onclick="connectRepo()">
                    <i class="fas fa-plug"></i> Connect Repository
                </button>
                
                <div class="tip-box">
                    <div class="tip-title">
                        <i class="fas fa-info-circle"></i> Instructions
                    </div>
                    <p class="tip-text">
                        1. Create a personal access token with "repo" permissions<br>
                        2. Format: username/repository (case sensitive)<br>
                        3. Ensure repository contains all_products.json
                    </p>
                </div>
            </div>
        </div>
        
        <script>
            async function connectRepo() {
                const repo = document.getElementById('repo').value.trim();
                const token = document.getElementById('token').value.trim();
                
                if (!repo || !token) {
                    alert('Both fields are required');
                    return;
                }
                
                const btn = document.querySelector('.setup-btn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
                btn.disabled = true;
                
                try {
                    const res = await fetch('/api/setup', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ repo, token })
                    });
                    
                    const data = await res.json();
                    
                    if (data.success) {
                        btn.innerHTML = '<i class="fas fa-check"></i> Connected!';
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                        alert('Connection failed. Check your credentials.');
                    }
                } catch (error) {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    alert('Network error. Please try again.');
                }
            }
            
            document.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') connectRepo();
            });
        </script>
    </body>
    </html>
    """

    ADMIN_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ProjectAxis Admin</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <style>
            :root {
                --primary: #2563eb;
                --primary-dark: #1d4ed8;
                --secondary: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --dark: #111827;
                --dark-light: #1f2937;
                --light: #f9fafb;
                --gray: #6b7280;
                --gray-light: #e5e7eb;
                --sidebar-width: 260px;
                --border-radius: 8px;
                --shadow: 0 1px 3px rgba(0,0,0,0.1);
                --shadow-lg: 0 4px 6px -1px rgba(0,0,0,0.1);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            
            body {
                background: var(--light);
                color: var(--dark);
                display: flex;
                min-height: 100vh;
                overflow-x: hidden;
            }
            
            .sidebar {
                width: var(--sidebar-width);
                background: var(--dark);
                color: white;
                display: flex;
                flex-direction: column;
                position: fixed;
                height: 100vh;
                z-index: 100;
            }
            
            .sidebar-header {
                padding: 24px 20px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .brand {
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 18px;
                font-weight: 700;
            }
            
            .brand-icon {
                width: 32px;
                height: 32px;
                background: var(--primary);
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .sidebar-nav {
                padding: 20px;
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .nav-item {
                padding: 12px 16px;
                border-radius: var(--border-radius);
                display: flex;
                align-items: center;
                gap: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                color: rgba(255,255,255,0.8);
                text-decoration: none;
            }
            
            .nav-item:hover {
                background: rgba(255,255,255,0.1);
                color: white;
            }
            
            .nav-item.active {
                background: var(--primary);
                color: white;
            }
            
            .nav-item i {
                width: 20px;
                font-size: 16px;
            }
            
            .sidebar-footer {
                padding: 20px;
                border-top: 1px solid rgba(255,255,255,0.1);
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: rgba(255,255,255,0.05);
                border-radius: var(--border-radius);
            }
            
            .main-content {
                flex: 1;
                margin-left: var(--sidebar-width);
                padding: 24px;
                min-height: 100vh;
                overflow-y: auto;
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
                padding-bottom: 20px;
                border-bottom: 1px solid var(--gray-light);
            }
            
            .page-title {
                font-size: 24px;
                font-weight: 600;
                color: var(--dark);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: var(--border-radius);
                box-shadow: var(--shadow);
                border-left: 4px solid var(--primary);
            }
            
            .stat-icon {
                width: 40px;
                height: 40px;
                border-radius: 8px;
                background: rgba(37, 99, 235, 0.1);
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 12px;
                color: var(--primary);
                font-size: 18px;
            }
            
            .stat-number {
                font-size: 28px;
                font-weight: 700;
                color: var(--dark);
                margin-bottom: 4px;
            }
            
            .stat-label {
                color: var(--gray);
                font-size: 14px;
                font-weight: 500;
            }
            
            .card {
                background: white;
                border-radius: var(--border-radius);
                padding: 24px;
                box-shadow: var(--shadow);
                margin-bottom: 24px;
            }
            
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .card-title {
                font-size: 18px;
                font-weight: 600;
                color: var(--dark);
            }
            
            .form-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 16px;
                margin-bottom: 16px;
            }
            
            .form-group {
                margin-bottom: 16px;
            }
            
            .form-label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: var(--dark);
                font-size: 14px;
            }
            
            .form-control {
                width: 100%;
                padding: 12px 14px;
                border: 1px solid var(--gray-light);
                border-radius: 6px;
                font-size: 14px;
                transition: all 0.2s ease;
                background: white;
            }
            
            .form-control:focus {
                outline: none;
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }
            
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .btn-primary {
                background: var(--primary);
                color: white;
            }
            
            .btn-primary:hover {
                background: var(--primary-dark);
            }
            
            .btn-success {
                background: var(--secondary);
                color: white;
            }
            
            .btn-danger {
                background: var(--danger);
                color: white;
            }
            
            .btn-secondary {
                background: var(--gray-light);
                color: var(--dark);
            }
            
            .image-upload-container {
                border: 2px dashed var(--gray-light);
                border-radius: var(--border-radius);
                padding: 30px 20px;
                text-align: center;
                margin-bottom: 16px;
                background: var(--light);
                cursor: pointer;
            }
            
            .upload-icon {
                font-size: 36px;
                color: var(--gray);
                margin-bottom: 12px;
            }
            
            .preview-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
                gap: 12px;
                margin-top: 12px;
            }
            
            .preview-box {
                position: relative;
                aspect-ratio: 1;
                border-radius: 6px;
                overflow: hidden;
                border: 1px solid var(--gray-light);
            }
            
            .preview-img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .remove-btn {
                position: absolute;
                top: 4px;
                right: 4px;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: rgba(239, 68, 68, 0.9);
                color: white;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                z-index: 2;
            }
            
            .progress-container {
                margin: 16px 0;
                display: none;
            }
            
            .progress-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            
            .progress-bar {
                height: 6px;
                background: var(--gray-light);
                border-radius: 3px;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                background: var(--primary);
                width: 0%;
                transition: width 0.3s ease;
            }
            
            .table-container {
                overflow-x: auto;
                border-radius: var(--border-radius);
                border: 1px solid var(--gray-light);
            }
            
            .table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .table th {
                background: var(--light);
                padding: 14px 16px;
                text-align: left;
                font-weight: 600;
                color: var(--gray);
                font-size: 12px;
                border-bottom: 1px solid var(--gray-light);
            }
            
            .table td {
                padding: 14px 16px;
                border-bottom: 1px solid var(--gray-light);
                vertical-align: middle;
            }
            
            .table tr:hover {
                background: rgba(37, 99, 235, 0.02);
            }
            
            .product-img {
                width: 50px;
                height: 50px;
                border-radius: 6px;
                object-fit: cover;
                border: 1px solid var(--gray-light);
            }
            
            .action-buttons {
                display: flex;
                gap: 6px;
            }
            
            .action-btn {
                width: 32px;
                height: 32px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 13px;
                transition: all 0.2s ease;
            }
            
            .action-btn:hover {
                transform: translateY(-1px);
            }
            
            .bulk-row {
                background: var(--light);
                margin-bottom: 12px;
                padding: 16px;
                border-radius: var(--border-radius);
                border: 1px solid var(--gray-light);
            }
            
            .bulk-row-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }
            
            .bulk-images-preview {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
                gap: 8px;
                margin-top: 8px;
            }
            
            .bulk-preview-box {
                position: relative;
                aspect-ratio: 1;
                border-radius: 4px;
                overflow: hidden;
                border: 1px solid var(--gray-light);
            }
            
            .bulk-preview-img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .banner-preview-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 16px;
                margin-top: 16px;
            }
            
            .banner-preview-box {
                position: relative;
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid var(--gray-light);
                background: white;
            }
            
            .banner-preview-img {
                width: 100%;
                height: 150px;
                object-fit: cover;
            }
            
            .banner-link {
                padding: 10px;
                font-size: 12px;
                color: var(--gray);
                word-break: break-all;
                background: var(--light);
                border-top: 1px solid var(--gray-light);
            }
            
            /* Responsive Quick Actions */
            .quick-actions {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }
            
            .quick-actions .btn {
                flex: 1;
                min-width: 150px;
                max-width: 250px;
            }
            
            /* FLOATING ADD BUTTON FOR BULK UPLOAD */
            .floating-add-btn {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: var(--primary);
                color: white;
                border: none;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
                font-size: 24px;
                cursor: pointer;
                z-index: 1000;
                display: none;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }
            
            .floating-add-btn:hover {
                background: var(--primary-dark);
                transform: scale(1.05);
                box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
            }
            
            .floating-add-btn:active {
                transform: scale(0.95);
            }
            
            .floating-add-btn.visible {
                display: flex;
            }
            
            @media (max-width: 768px) {
                .quick-actions .btn {
                    min-width: 100%;
                }
                
                .floating-add-btn {
                    bottom: 20px;
                    right: 20px;
                    width: 56px;
                    height: 56px;
                    font-size: 20px;
                }
            }
            
            /* Multiple selection styles */
            .select-checkbox {
                width: 18px;
                height: 18px;
                cursor: pointer;
            }
            
            .delete-selected-btn {
                background: var(--danger);
                color: white;
                display: none;
                align-items: center;
                gap: 8px;
            }
            
            .delete-selected-btn.show {
                display: inline-flex;
            }
            
            @media (max-width: 1200px) {
                .sidebar {
                    width: 70px;
                }
                
                .sidebar .nav-text, .brand-text {
                    display: none;
                }
                
                .main-content {
                    margin-left: 70px;
                }
            }
            
            @media (max-width: 768px) {
                .main-content {
                    padding: 16px;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .form-grid {
                    grid-template-columns: 1fr;
                }
                
                .card {
                    padding: 16px;
                }
                
                .header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 12px;
                }
                
                .page-title {
                    font-size: 20px;
                }
            }
            
            /* Loading animation for deletion */
            .deleting-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                flex-direction: column;
            }
            
            .deleting-overlay.active {
                display: flex;
            }
            
            .deleting-content {
                background: white;
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .deleting-spinner {
                width: 60px;
                height: 60px;
                border: 4px solid #f3f3f3;
                border-top: 4px solid #ef4444;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>

        <!-- Deleting Overlay -->
        <div class="deleting-overlay" id="deletingOverlay">
            <div class="deleting-content">
                <div class="deleting-spinner"></div>
                <h3 style="margin-bottom: 10px; color: #111827;" id="deletingTitle">Deleting...</h3>
                <p style="color: #6b7280; margin-bottom: 20px;" id="deletingMessage">Please wait while we delete the selected items</p>
                <div class="progress-bar" style="background: #e5e7eb;">
                    <div class="progress-fill" id="deletingProgress" style="background: #ef4444;"></div>
                </div>
            </div>
        </div>

        <!-- Floating Add Button for Bulk Upload -->
        <button class="floating-add-btn" id="floatingAddBtn" title="Add New Product Row">
            <i class="fas fa-plus"></i>
        </button>

        <div class="overlay" onclick="toggleSidebar()"></div>

        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="brand">
                    <div class="brand-icon">
                        <i class="fas fa-cube"></i>
                    </div>
                    <span class="brand-text">ProjectAxis</span>
                </div>
            </div>
            
            <div class="sidebar-nav">
                <a href="#" class="nav-item active" onclick="nav('dashboard', this)">
                    <i class="fas fa-tachometer-alt"></i>
                    <span class="nav-text">Dashboard</span>
                </a>
                <a href="#" class="nav-item" onclick="nav('add-product', this)">
                    <i class="fas fa-plus"></i>
                    <span class="nav-text">Add Product</span>
                </a>
                <a href="#" class="nav-item" onclick="nav('bulk-upload', this)">
                    <i class="fas fa-upload"></i>
                    <span class="nav-text">Bulk Upload</span>
                </a>
                <a href="#" class="nav-item" onclick="nav('categories', this)">
                    <i class="fas fa-tags"></i>
                    <span class="nav-text">Categories</span>
                </a>
                <a href="#" class="nav-item" onclick="nav('manage-products', this)">
                    <i class="fas fa-box"></i>
                    <span class="nav-text">Products</span>
                </a>
                <a href="#" class="nav-item" onclick="nav('banners', this)">
                    <i class="fas fa-image"></i>
                    <span class="nav-text">Banners</span>
                </a>
                <!-- New Store Settings Tab -->
                <a href="#" class="nav-item" onclick="nav('store-settings', this)">
                    <i class="fas fa-cog"></i>
                    <span class="nav-text">Store Settings</span>
                </a>
            </div>
            
            <div class="sidebar-footer">
                <div class="user-info">
                    <i class="fas fa-user-circle" style="font-size: 20px;"></i>
                    <div>
                        <div style="font-weight: 600; font-size: 13px;">Admin</div>
                        <div style="font-size: 11px; opacity: 0.8;">Connected</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="main-content">
            
            <div id="dashboard" class="section active">
                <div class="header">
                    <h1 class="page-title">Dashboard</h1>
                    <button class="btn btn-secondary" onclick="refreshData()">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fas fa-box"></i>
                        </div>
                        <div class="stat-number" id="totalProds">0</div>
                        <div class="stat-label">Total Products</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon" style="background: rgba(16, 185, 129, 0.1); color: #10b981;">
                            <i class="fas fa-tags"></i>
                        </div>
                        <div class="stat-number" id="totalCats">0</div>
                        <div class="stat-label">Categories</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-icon" style="background: rgba(245, 158, 11, 0.1); color: #f59e0b;">
                            <i class="fas fa-image"></i>
                        </div>
                        <div class="stat-number" id="totalImages">0</div>
                        <div class="stat-label">Total Images</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3 class="card-title">Quick Actions</h3>
                    <div class="quick-actions">
                        <button class="btn btn-primary" onclick="nav('add-product', document.querySelectorAll('.nav-item')[1])">
                            <i class="fas fa-plus"></i> Add Product
                        </button>
                        <button class="btn btn-secondary" onclick="nav('bulk-upload', document.querySelectorAll('.nav-item')[2])">
                            <i class="fas fa-upload"></i> Bulk Upload
                        </button>
                        <button class="btn btn-success" onclick="nav('categories', document.querySelectorAll('.nav-item')[3])">
                            <i class="fas fa-tags"></i> Manage Categories
                        </button>
                        <button class="btn btn-secondary" onclick="nav('banners', document.querySelectorAll('.nav-item')[5])">
                            <i class="fas fa-image"></i> Manage Banners
                        </button>
                        <button class="btn btn-secondary" onclick="nav('store-settings', document.querySelectorAll('.nav-item')[6])">
                            <i class="fas fa-cog"></i> Store Settings
                        </button>
                    </div>
                </div>
            </div>

            <div id="add-product" class="section" style="display:none;">
                <div class="header">
                    <h1 class="page-title" id="formTitle">Add New Product</h1>
                    <button class="btn btn-secondary" onclick="resetForm()">
                        <i class="fas fa-times"></i> Clear Form
                    </button>
                </div>
                
                <div class="card">
                    <input type="hidden" id="editIndex" value="-1">
                    <input type="hidden" id="existingImages" value="">
                    
                    <div class="form-group">
                        <label class="form-label">Product Images</label>
                        <div class="image-upload-container" onclick="document.getElementById('pFiles').click()">
                            <i class="fas fa-cloud-upload-alt upload-icon"></i>
                            <p style="color: var(--gray); margin-bottom: 8px;">Click to upload new images</p>
                            <p style="font-size: 13px; color: var(--gray);">Supports JPG, PNG, WEBP</p>
                        </div>
                        <input type="file" id="pFiles" multiple accept="image/*" style="display:none" onchange="previewNewImages()">
                        
                        <div id="existingImagesContainer">
                            <p style="font-size: 14px; font-weight: 600; margin: 16px 0 8px 0; color: var(--dark);">
                                Existing Images (click × to remove)
                            </p>
                            <div id="existingPreview" class="preview-grid"></div>
                        </div>
                        
                        <div id="newImagesContainer" style="display: none;">
                            <p style="font-size: 14px; font-weight: 600; margin: 16px 0 8px 0; color: var(--dark);">
                                New Images
                            </p>
                            <div id="newPreview" class="preview-grid"></div>
                        </div>
                    </div>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Product Title *</label>
                            <input type="text" id="pTitle" class="form-control" placeholder="Enter product name">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Category *</label>
                            <select id="pCategory" class="form-control cat-drop">
                                <option value="">Select Category</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">Price *</label>
                            <input type="number" id="pPrice" class="form-control" placeholder="Enter price" step="0.01">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Discount (%)</label>
                            <input type="number" id="pOffer" class="form-control" value="0" min="0" max="100">
                        </div>
                    </div>
                    
                    <!-- Buy Link removed from here -->
                    
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea id="pDesc" class="form-control" rows="3" placeholder="Enter product description"></textarea>
                    </div>
                    
                    <div class="progress-container" id="singleProgress">
                        <div class="progress-header">
                            <span>Uploading...</span>
                            <span id="singleProgressText">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="singleProgressBar"></div>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary" onclick="uploadSingle()" style="width: 100%; padding: 12px;">
                        <i class="fas fa-upload"></i> <span id="uploadBtnText">Upload Product</span>
                    </button>
                </div>
            </div>

            <div id="bulk-upload" class="section" style="display:none;">
                <div class="header">
                    <h1 class="page-title">Bulk Upload</h1>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-primary" onclick="addBulkRow()">
                            <i class="fas fa-plus"></i> Add Row
                        </button>
                    </div>
                </div>
                
                <div class="card">
                    <div style="margin-bottom: 16px;">
                        <p style="color: var(--gray); margin-bottom: 12px;">Add multiple products at once</p>
                        <div id="bulkBody"></div>
                    </div>
                    
                    <div id="bulkUploadButton" style="text-align: center; display: none;">
                        <button class="btn btn-primary" onclick="processBulk()" style="padding: 12px 32px;">
                            <i class="fas fa-play"></i> Start Upload
                        </button>
                    </div>
                </div>
            </div>

            <div id="categories" class="section" style="display:none;">
                <div class="header">
                    <h1 class="page-title">Categories</h1>
                </div>
                
                <div class="card">
                    <h3 class="card-title" style="margin-bottom: 16px;">Add New Category</h3>
                    <div style="display: flex; gap: 8px; margin-bottom: 24px;">
                        <input type="text" id="newCatInput" class="form-control" placeholder="Enter category name">
                        <button class="btn btn-primary" onclick="addCategory()" style="width: 80px;">
                            <i class="fas fa-plus"></i> Add
                        </button>
                    </div>
                    
                    <h3 class="card-title" style="margin-bottom: 16px;">Existing Categories</h3>
                    <div id="categoryList" style="display: flex; flex-wrap: wrap; gap: 8px;"></div>
                </div>
            </div>

            <div id="manage-products" class="section" style="display:none;">
                <div class="header">
                    <div>
                        <h1 class="page-title">Products</h1>
                        <button class="btn btn-danger delete-selected-btn" id="deleteSelectedBtn" onclick="deleteSelectedProducts()">
                            <i class="fas fa-trash"></i> Delete Selected
                        </button>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="searchInput" class="form-control" placeholder="Search products..." style="width: 200px;">
                        <button class="btn btn-secondary" onclick="searchProducts()">
                            <i class="fas fa-search"></i>
                        </button>
                    </div>
                </div>
                
                <div class="card" style="padding: 0;">
                    <div class="table-container">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th style="width: 40px;">
                                        <input type="checkbox" id="selectAllCheckbox" class="select-checkbox" onchange="toggleSelectAll(this)">
                                    </th>
                                    <th>Image</th>
                                    <th>Product Details</th>
                                    <th>Category</th>
                                    <th>Price</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="inventoryContainer"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="banners" class="section" style="display:none;">
                <div class="header">
                    <h1 class="page-title">Banner Management</h1>
                </div>
                
                <div class="card">
                    <h3 class="card-title" style="margin-bottom: 16px;">Add New Banner</h3>
                    
                    <div class="form-group">
                        <label class="form-label">Banner Image *</label>
                        <div class="image-upload-container" onclick="document.getElementById('bannerFile').click()">
                            <i class="fas fa-cloud-upload-alt upload-icon"></i>
                            <p style="color: var(--gray); margin-bottom: 8px;">Click to upload banner image</p>
                            <p style="font-size: 13px; color: var(--gray);">Recommended size: 1200x400px</p>
                        </div>
                        <input type="file" id="bannerFile" accept="image/*" style="display:none" onchange="previewBannerImage()">
                        
                        <div id="bannerPreviewContainer" style="display: none; margin-top: 16px;">
                            <p style="font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--dark);">
                                Banner Preview
                            </p>
                            <div id="bannerPreview" class="preview-grid" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));"></div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Banner Link (Optional)</label>
                        <input type="text" id="bannerLink" class="form-control" placeholder="https://example.com/offer">
                        <p style="font-size: 12px; color: var(--gray); margin-top: 4px;">Leave empty if banner shouldn't be clickable</p>
                    </div>
                    
                    <button class="btn btn-primary" onclick="uploadBanner()" style="width: 100%; padding: 12px;">
                        <i class="fas fa-upload"></i> Upload Banner
                    </button>
                </div>
                
                <div class="card">
                    <h3 class="card-title" style="margin-bottom: 16px;">Existing Banners</h3>
                    <div id="bannersList" style="color: var(--gray); font-size: 14px;">
                        Loading banners...
                    </div>
                </div>
            </div>

            <!-- NEW Store Settings Section -->
            <div id="store-settings" class="section" style="display:none;">
                <div class="header">
                    <h1 class="page-title">Store Settings</h1>
                </div>
                
                <div class="card">
                    <h3 class="card-title" style="margin-bottom: 16px;">WhatsApp Configuration</h3>
                    <p style="color: var(--gray); margin-bottom: 20px;">Set the global WhatsApp number for all products. This number will be used for customer inquiries and orders.</p>
                    
                    <div class="form-group">
                        <label class="form-label">WhatsApp Number (without country code)</label>
                        <input type="text" id="storeWhatsapp" class="form-control" placeholder="e.g., 9876543210">
                        <p style="font-size: 12px; color: var(--gray); margin-top: 4px;">Enter only digits, without +91 or spaces.</p>
                    </div>
                    
                    <button class="btn btn-primary" onclick="saveSettings()" style="margin-top: 8px;">
                        <i class="fas fa-save"></i> Save Settings
                    </button>
                </div>
            </div>
        </div>

    <script>
        let products = [], categories = [], filteredProducts = [];
        let editingProductImages = []; // Stores existing image URLs
        let newProductImages = []; // Stores new image base64 strings
        let removedExistingImages = []; // Track removed existing images
        let banners = []; // Store banners data
        let bulkRowImagePreviews = {}; // Store bulk row image previews
        let selectedProducts = new Set(); // Store selected product indices
        let whatsappNumber = ''; // Global WhatsApp number

        window.onload = function() {
            loadData();
            // Setup floating button click handler
            document.getElementById('floatingAddBtn').onclick = addBulkRow;
        };

        async function loadData() {
            try {
                const res = await fetch('/api/get-data');
                const data = await res.json();
                products = data.products || [];
                filteredProducts = [...products];
                categories = data.categories || [];
                banners = data.banners || [];
                whatsappNumber = data.whatsapp || '';
                updateUI();
            } catch (error) {
                console.error('Failed to load data:', error);
                Swal.fire('Error', 'Failed to load data', 'error');
            }
        }

        function updateUI() {
            document.getElementById('totalProds').innerText = products.length;
            document.getElementById('totalCats').innerText = categories.length;
            
            let totalImages = 0;
            products.forEach(p => totalImages += (p.images ? p.images.length : (p.image ? 1 : 0)));
            document.getElementById('totalImages').innerText = totalImages;
            
            document.querySelectorAll('.cat-drop').forEach(sel => {
                const currentVal = sel.value;
                sel.innerHTML = '<option value="">Select Category</option>' + 
                            categories.map(c => `<option value="${c}">${c}</option>`).join('');
                if (currentVal && categories.includes(currentVal)) {
                    sel.value = currentVal;
                }
            });

            const categoryList = document.getElementById('categoryList');
            if (categoryList) {
                categoryList.innerHTML = categories.map((c, i) => `
                    <div style="background: #e0f2fe; border: 1px solid #bae6fd; border-radius: 16px; padding: 6px 12px; display: inline-flex; align-items: center; gap: 6px;">
                        <i class="fas fa-tag" style="color: #0284c7;"></i>
                        <span style="color: #0369a1; font-weight: 500;">${c}</span>
                        <button onclick="delCat(${i})" style="background: none; border: none; color: #dc2626; cursor: pointer; padding: 2px 6px;">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `).join('');
            }

            renderBannersList();
            renderProductTable();
            
            // Bind WhatsApp number to input field
            const whatsappInput = document.getElementById('storeWhatsapp');
            if (whatsappInput) {
                whatsappInput.value = whatsappNumber;
            }
        }

        function renderProductTable(searchTerm = '') {
            const container = document.getElementById('inventoryContainer');
            let itemsToRender = filteredProducts;
            
            if (searchTerm) {
                itemsToRender = filteredProducts.filter(p => 
                    (p.title && p.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
                    (p.category && p.category.toLowerCase().includes(searchTerm.toLowerCase())) ||
                    (p.description && p.description.toLowerCase().includes(searchTerm.toLowerCase()))
                );
            }
            
            if (itemsToRender.length === 0) {
                container.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; padding: 40px; color: var(--gray);">
                            <i class="fas fa-box-open" style="font-size: 36px; margin-bottom: 12px; display: block; opacity: 0.3;"></i>
                            No products found
                        </td>
                    </tr>
                `;
                return;
            }
            
            container.innerHTML = itemsToRender.map((p, i) => {
                const originalIndex = products.findIndex(prod => prod.id === p.id);
                const isSelected = selectedProducts.has(originalIndex);
                return `
                    <tr>
                        <td>
                            <input type="checkbox" class="select-checkbox" 
                                   data-index="${originalIndex}"
                                   onchange="toggleProductSelection(${originalIndex}, this)"
                                   ${isSelected ? 'checked' : ''}>
                        </td>
                        <td>
                            <img src="${p.image || p.images?.[0] || 'https://via.placeholder.com/50'}" 
                                class="product-img" 
                                alt="${p.title}"
                                onerror="this.src='https://via.placeholder.com/50'">
                        </td>
                        <td>
                            <div style="font-weight: 600; margin-bottom: 4px;">${p.title || 'No title'}</div>
                            <div style="font-size: 13px; color: var(--gray); max-width: 300px;">
                                ${p.description ? p.description.substring(0, 100) + (p.description.length > 100 ? '...' : '') : 'No description'}
                            </div>
                        </td>
                        <td>
                            <span style="background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 16px; font-size: 12px; font-weight: 500;">
                                ${p.category || 'General'}
                            </span>
                        </td>
                        <td>
                            <div style="font-weight: 700; color: var(--dark);">₹${parseFloat(p.price || 0).toFixed(2)}</div>
                            ${p.offer ? `<div style="font-size: 12px; color: var(--secondary);">${p.offer}% off</div>` : ''}
                        </td>
                        <td>
                            <div class="action-buttons">
                                <button class="action-btn" style="background: #f59e0b; color: white;" onclick="editProduct(${originalIndex})">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="action-btn" style="background: #ef4444; color: white;" onclick="deleteProduct(${originalIndex})">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
            
            updateDeleteSelectedButton();
        }

        // --- MULTIPLE SELECTION FUNCTIONS ---
        function toggleProductSelection(index, checkbox) {
            if (checkbox.checked) {
                selectedProducts.add(index);
            } else {
                selectedProducts.delete(index);
                document.getElementById('selectAllCheckbox').checked = false;
            }
            updateDeleteSelectedButton();
        }

        function toggleSelectAll(checkbox) {
            const allCheckboxes = document.querySelectorAll('.select-checkbox');
            const container = document.getElementById('inventoryContainer');
            
            if (checkbox.checked) {
                // Select all visible products
                filteredProducts.forEach((p, i) => {
                    const originalIndex = products.findIndex(prod => prod.id === p.id);
                    if (originalIndex !== -1) {
                        selectedProducts.add(originalIndex);
                    }
                });
                allCheckboxes.forEach(cb => cb.checked = true);
            } else {
                // Deselect all
                selectedProducts.clear();
                allCheckboxes.forEach(cb => cb.checked = false);
            }
            updateDeleteSelectedButton();
        }

        function updateDeleteSelectedButton() {
            const deleteBtn = document.getElementById('deleteSelectedBtn');
            if (selectedProducts.size > 0) {
                deleteBtn.classList.add('show');
                deleteBtn.innerHTML = `<i class="fas fa-trash"></i> Delete Selected (${selectedProducts.size})`;
            } else {
                deleteBtn.classList.remove('show');
            }
        }

        // --- DELETION FUNCTIONS WITH LOADING ---
        async function showDeletingOverlay(title, message) {
            const overlay = document.getElementById('deletingOverlay');
            const progressBar = document.getElementById('deletingProgress');
            
            document.getElementById('deletingTitle').textContent = title;
            document.getElementById('deletingMessage').textContent = message;
            progressBar.style.width = '0%';
            
            overlay.classList.add('active');
            
            // Disable body scroll
            document.body.style.overflow = 'hidden';
        }

        async function hideDeletingOverlay() {
            const overlay = document.getElementById('deletingOverlay');
            const progressBar = document.getElementById('deletingProgress');
            
            // Complete the progress bar
            progressBar.style.width = '100%';
            
            // Wait for animation to complete
            await new Promise(resolve => setTimeout(resolve, 500));
            
            overlay.classList.remove('active');
            document.body.style.overflow = 'auto';
        }

        async function updateDeletionProgress(progress) {
            const progressBar = document.getElementById('deletingProgress');
            progressBar.style.width = `${progress}%`;
        }

        async function deleteSelectedProducts() {
            if (selectedProducts.size === 0) return;
            
            const { value: confirm } = await Swal.fire({
                title: `Delete ${selectedProducts.size} Products?`,
                text: 'This action cannot be undone. All product images will also be deleted.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Delete',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#ef4444'
            });
            
            if (!confirm) return;
            
            const indices = Array.from(selectedProducts);
            
            // Show deleting overlay
            await showDeletingOverlay('Deleting Products', `Deleting ${indices.length} products...`);
            
            try {
                // Sort indices in descending order to avoid index shifting
                indices.sort((a, b) => b - a);
                
                const total = indices.length;
                let completed = 0;
                
                for (const index of indices) {
                    await updateDeletionProgress(Math.round((completed / total) * 100));
                    
                    const res = await fetch('/api/delete', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({index: index})
                    });
                    
                    if (!res.ok) {
                        throw new Error('Failed to delete product');
                    }
                    
                    completed++;
                    await updateDeletionProgress(Math.round((completed / total) * 100));
                    
                    // Small delay between deletions
                    await new Promise(resolve => setTimeout(resolve, 300));
                }
                
                // Update UI
                selectedProducts.clear();
                await loadData();
                
                // Show success message
                await hideDeletingOverlay();
                
                Swal.fire({
                    icon: 'success',
                    title: 'Deleted Successfully!',
                    text: `${total} products have been deleted.`,
                    timer: 2000,
                    showConfirmButton: false
                });
                
            } catch (error) {
                console.error('Delete multiple error:', error);
                await hideDeletingOverlay();
                Swal.fire('Error', 'Failed to delete products', 'error');
            }
        }

        async function deleteProduct(index) {
            const { value: confirm } = await Swal.fire({
                title: 'Delete Product?',
                text: 'This action cannot be undone. All product images will also be deleted.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Delete',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#ef4444'
            });
            
            if (!confirm) return;
            
            // Show deleting overlay
            await showDeletingOverlay('Deleting Product', 'Deleting product and associated images...');
            
            try {
                await updateDeletionProgress(30);
                
                const res = await fetch('/api/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({index: index})
                });
                
                await updateDeletionProgress(70);
                
                if (!res.ok) {
                    throw new Error('Delete failed');
                }
                
                // Remove from selected products if present
                selectedProducts.delete(index);
                
                await updateDeletionProgress(100);
                await loadData();
                
                // Hide overlay and show success
                await hideDeletingOverlay();
                
                Swal.fire({
                    icon: 'success',
                    title: 'Deleted Successfully!',
                    text: 'Product has been deleted.',
                    timer: 1500,
                    showConfirmButton: false
                });
                
            } catch (error) {
                console.error('Delete error:', error);
                await hideDeletingOverlay();
                Swal.fire('Error', 'Failed to delete product', 'error');
            }
        }

        async function deleteBanner(index) {
            const { value: confirm } = await Swal.fire({
                title: 'Delete Banner?',
                text: 'This banner will be removed from the homepage',
                icon: 'warning',
                showCancelButton: true,
                showCancelButton: true,
                confirmButtonText: 'Delete',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#ef4444'
            });
            
            if (!confirm) return;
            
            // Show deleting overlay
            await showDeletingOverlay('Deleting Banner', 'Deleting banner image...');
            
            try {
                await updateDeletionProgress(30);
                
                const res = await fetch('/api/delete-banner', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({index: index})
                });
                
                await updateDeletionProgress(70);
                
                if (!res.ok) {
                    throw new Error('Delete failed');
                }
                
                await updateDeletionProgress(100);
                await loadData();
                
                // Hide overlay and show success
                await hideDeletingOverlay();
                
                Swal.fire({
                    icon: 'success',
                    title: 'Deleted Successfully!',
                    text: 'Banner has been deleted.',
                    timer: 1500,
                    showConfirmButton: false
                });
                
            } catch (error) {
                console.error('Delete banner error:', error);
                await hideDeletingOverlay();
                Swal.fire('Error', 'Failed to delete banner', 'error');
            }
        }

        // --- IMAGE FUNCTIONS ---
        function previewNewImages() {
            const files = document.getElementById('pFiles').files;
            const preview = document.getElementById('newPreview');
            preview.innerHTML = '';
            
            if (!files || files.length === 0) {
                document.getElementById('newImagesContainer').style.display = 'none';
                return;
            }
            
            document.getElementById('newImagesContainer').style.display = 'block';
            
            Array.from(files).forEach((file, index) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const div = document.createElement('div');
                    div.className = 'preview-box';
                    div.innerHTML = `
                        <img src="${e.target.result}" class="preview-img" alt="New image ${index + 1}">
                        <button class="remove-btn" onclick="removeNewImage(this, '${e.target.result}')">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                    preview.appendChild(div);
                    
                    // Store base64 data (remove data:image/...;base64, prefix)
                    newProductImages.push(e.target.result.split(',')[1]);
                };
                reader.readAsDataURL(file);
            });
        }

        function removeNewImage(btn, imgData) {
            // Remove from newProductImages array
            const base64Data = imgData.split(',')[1];
            const index = newProductImages.indexOf(base64Data);
            if (index > -1) {
                newProductImages.splice(index, 1);
            }
            
            // Remove from DOM
            btn.closest('.preview-box').remove();
            
            // Hide container if no new images left
            if (document.getElementById('newPreview').children.length === 0) {
                document.getElementById('newImagesContainer').style.display = 'none';
            }
        }

        function removeExistingImage(index) {
            // Add to removed images list
            if (editingProductImages[index]) {
                removedExistingImages.push(editingProductImages[index]);
            }
            
            // Remove from editingProductImages
            editingProductImages.splice(index, 1);
            
            // Update preview
            updateExistingImagesPreview();
        }

        function updateExistingImagesPreview() {
            const existingPreview = document.getElementById('existingPreview');
            existingPreview.innerHTML = '';
            
            if (editingProductImages.length === 0) {
                document.getElementById('existingImagesContainer').style.display = 'none';
                return;
            }
            
            document.getElementById('existingImagesContainer').style.display = 'block';
            
            editingProductImages.forEach((img, i) => {
                const div = document.createElement('div');
                div.className = 'preview-box';
                div.innerHTML = `
                    <img src="${img}" class="preview-img" alt="Existing image ${i + 1}" onerror="this.src='https://via.placeholder.com/80'">
                    <button class="remove-btn" onclick="removeExistingImage(${i})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                existingPreview.appendChild(div);
            });
        }

        async function getBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result.split(',')[1]);
                reader.onerror = error => reject(error);
            });
        }

        // --- SINGLE PRODUCT UPLOAD ---
        async function uploadSingle() {
            const title = document.getElementById('pTitle').value.trim();
            const price = document.getElementById('pPrice').value.trim();
            const category = document.getElementById('pCategory').value;
            const description = document.getElementById('pDesc').value.trim();
            const editIndex = parseInt(document.getElementById('editIndex').value);
            const files = document.getElementById('pFiles').files;
            
            if (!title || !price || !category) {
                Swal.fire('Missing Info', 'Please fill all required fields', 'error');
                return;
            }
            
            if (price <= 0) {
                Swal.fire('Invalid Price', 'Price must be greater than 0', 'error');
                return;
            }
            
            // If adding new product and no images
            if (editIndex === -1 && newProductImages.length === 0 && files.length === 0) {
                Swal.fire('No Images', 'Please select at least one image for new product', 'warning');
                return;
            }
            
            const btn = document.querySelector('#add-product .btn-primary');
            const btnText = document.getElementById('uploadBtnText');
            const progressContainer = document.getElementById('singleProgress');
            const progressBar = document.getElementById('singleProgressBar');
            const progressText = document.getElementById('singleProgressText');
            
            progressContainer.style.display = 'block';
            progressBar.style.width = '0%';
            progressText.textContent = '0%';
            btn.disabled = true;
            btnText.innerHTML = '<span class="loader"></span> Uploading...';
            
            try {
                // For edit: existing images + new images - removed images
                // For new: just new images
                const payload = {
                    editIndex: editIndex,
                    product: {
                        title: title,
                        price: parseFloat(price),
                        category: category,
                        offer: parseInt(document.getElementById('pOffer').value) || 0,
                        description: description,
                        existingImages: editingProductImages, // Keep these as-is
                        newImages: newProductImages, // Upload these as new
                        removedImages: removedExistingImages // Track removed for backend cleanup
                    }
                };
                
                progressBar.style.width = '50%';
                progressText.textContent = '50% - Processing...';
                
                const res = await fetch('/api/upload', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                const result = await res.json();
                
                if (result.success) {
                    progressBar.style.width = '100%';
                    progressText.textContent = '100% - Complete!';
                    
                    await Swal.fire({
                        icon: 'success',
                        title: editIndex > -1 ? 'Product Updated!' : 'Product Uploaded!',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    
                    loadData();
                    resetForm();
                } else {
                    throw new Error('Upload failed');
                }
                
            } catch (error) {
                console.error('Upload error:', error);
                Swal.fire('Upload Failed', 'Failed to upload product', 'error');
            } finally {
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    btn.disabled = false;
                    btnText.innerHTML = editIndex > -1 ? 'Update Product' : 'Upload Product';
                }, 1000);
            }
        }

        function resetForm() {
            document.getElementById('editIndex').value = "-1";
            document.getElementById('existingImages').value = "";
            document.getElementById('formTitle').textContent = "Add New Product";
            document.getElementById('uploadBtnText').textContent = "Upload Product";
            
            // Clear all form fields
            document.getElementById('pTitle').value = '';
            document.getElementById('pPrice').value = '';
            document.getElementById('pOffer').value = '0';
            document.getElementById('pDesc').value = '';
            document.getElementById('pCategory').value = '';
            document.getElementById('pFiles').value = '';
            
            // Clear previews and arrays
            document.getElementById('existingPreview').innerHTML = '';
            document.getElementById('newPreview').innerHTML = '';
            document.getElementById('existingImagesContainer').style.display = 'none';
            document.getElementById('newImagesContainer').style.display = 'none';
            
            editingProductImages = [];
            newProductImages = [];
            removedExistingImages = [];
            
            document.getElementById('singleProgress').style.display = 'none';
        }

        function editProduct(index) {
            if (index < 0 || index >= products.length) return;
            
            const product = products[index];
            
            document.getElementById('editIndex').value = index;
            document.getElementById('formTitle').textContent = "Edit Product";
            document.getElementById('uploadBtnText').textContent = "Update Product";
            
            document.getElementById('pTitle').value = product.title || '';
            document.getElementById('pPrice').value = product.price || '';
            document.getElementById('pOffer').value = product.offer || 0;
            document.getElementById('pDesc').value = product.description || product.desc || '';
            
            // Set category
            const categorySelect = document.getElementById('pCategory');
            if (product.category && categories.includes(product.category)) {
                categorySelect.value = product.category;
            }
            
            // Store existing images
            editingProductImages = [];
            if (product.images && Array.isArray(product.images)) {
                editingProductImages = [...product.images];
            } else if (product.image) {
                editingProductImages = [product.image];
            }
            
            // Clear new images
            newProductImages = [];
            removedExistingImages = [];
            
            // Update previews
            updateExistingImagesPreview();
            document.getElementById('newPreview').innerHTML = '';
            document.getElementById('newImagesContainer').style.display = 'none';
            document.getElementById('pFiles').value = '';
            
            nav('add-product', document.querySelectorAll('.nav-item')[1]);
        }

        // --- BULK UPLOAD FUNCTIONS ---
        function addBulkRow() {
            const id = Date.now() + Math.random();
            const row = document.createElement('div');
            row.className = 'bulk-row';
            row.id = `bulk-row-${id}`;
            
            row.innerHTML = `
                <div class="bulk-row-header">
                    <div style="font-weight: 600; color: var(--dark);">Product #${document.querySelectorAll('.bulk-row').length + 1}</div>
                    <button onclick="removeBulkRow('${id}')" style="background: none; border: none; color: var(--danger); cursor: pointer;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="form-grid" style="margin-bottom: 12px;">
                    <div class="form-group">
                        <label class="form-label">Title *</label>
                        <input type="text" id="bulk-title-${id}" class="form-control" placeholder="Product name">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Price *</label>
                        <input type="number" id="bulk-price-${id}" class="form-control" placeholder="Price" step="0.01">
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Images *</label>
                    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
                        <input type="file" id="bulk-files-${id}" class="form-control" multiple accept="image/*" onchange="previewBulkImages('${id}', this)" style="flex: 1;">
                        <button class="btn btn-secondary" onclick="clearBulkImages('${id}')" style="padding: 8px 12px;">
                            <i class="fas fa-times"></i> Clear
                        </button>
                    </div>
                    <div id="bulk-preview-${id}" class="bulk-images-preview"></div>
                </div>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Category</label>
                        <select id="bulk-category-${id}" class="form-control">
                            ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Discount (%)</label>
                        <input type="number" id="bulk-offer-${id}" class="form-control" value="0" min="0" max="100">
                    </div>
                </div>
                
                <!-- Buy Link removed from bulk upload -->
                
                <div class="form-group">
                    <label class="form-label">Description</label>
                    <textarea id="bulk-desc-${id}" class="form-control" rows="2" placeholder="Product description"></textarea>
                </div>
            `;
            
            document.getElementById('bulkBody').appendChild(row);
            bulkRowImagePreviews[id] = [];
            updateBulkUploadButton();
            
            // Scroll to the newly added row
            setTimeout(() => {
                row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 100);
        }

        function removeBulkRow(id) {
            const row = document.getElementById(`bulk-row-${id}`);
            if (row) {
                row.remove();
                delete bulkRowImagePreviews[id];
                updateBulkUploadButton();
                updateRowNumbers();
            }
        }

        function updateRowNumbers() {
            const rows = document.querySelectorAll('.bulk-row');
            rows.forEach((row, index) => {
                const header = row.querySelector('.bulk-row-header div');
                if (header) {
                    header.textContent = `Product #${index + 1}`;
                }
            });
        }

        function updateBulkUploadButton() {
            const rows = document.querySelectorAll('.bulk-row');
            const uploadButton = document.getElementById('bulkUploadButton');
            
            if (rows.length > 0) {
                uploadButton.style.display = 'block';
            } else {
                uploadButton.style.display = 'none';
            }
        }

        function previewBulkImages(rowId, inputElement) {
            const files = inputElement.files;
            const preview = document.getElementById(`bulk-preview-${rowId}`);
            
            if (!files || files.length === 0) {
                return;
            }
            
            // Clear existing preview
            preview.innerHTML = '';
            
            // Clear existing images array for this row
            bulkRowImagePreviews[rowId] = [];
            
            Array.from(files).forEach((file, index) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const div = document.createElement('div');
                    div.className = 'bulk-preview-box';
                    div.innerHTML = `
                        <img src="${e.target.result}" class="bulk-preview-img" alt="Image ${index + 1}">
                        <button class="remove-btn" onclick="removeBulkImage('${rowId}', ${index})" style="top: 2px; right: 2px; width: 20px; height: 20px; font-size: 10px;">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                    preview.appendChild(div);
                    
                    // Store base64 data
                    bulkRowImagePreviews[rowId].push(e.target.result.split(',')[1]);
                };
                reader.readAsDataURL(file);
            });
        }

        function clearBulkImages(rowId) {
            const input = document.getElementById(`bulk-files-${rowId}`);
            const preview = document.getElementById(`bulk-preview-${rowId}`);
            
            // Clear file input
            input.value = '';
            
            // Clear preview
            preview.innerHTML = '';
            
            // Clear stored images
            bulkRowImagePreviews[rowId] = [];
        }

        function removeBulkImage(rowId, index) {
            // Remove image from array
            if (bulkRowImagePreviews[rowId] && bulkRowImagePreviews[rowId].length > index) {
                bulkRowImagePreviews[rowId].splice(index, 1);
                
                // Update preview
                const preview = document.getElementById(`bulk-preview-${rowId}`);
                preview.innerHTML = '';
                
                // Recreate preview with remaining images
                bulkRowImagePreviews[rowId].forEach((imgBase64, i) => {
                    const div = document.createElement('div');
                    div.className = 'bulk-preview-box';
                    div.innerHTML = `
                        <img src="data:image/webp;base64,${imgBase64}" class="bulk-preview-img" alt="Image ${i + 1}">
                        <button class="remove-btn" onclick="removeBulkImage('${rowId}', ${i})" style="top: 2px; right: 2px; width: 20px; height: 20px; font-size: 10px;">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                    preview.appendChild(div);
                });
                
                // Update file input (we need to create a new FileList)
                // For simplicity, we'll just clear the file input
                const input = document.getElementById(`bulk-files-${rowId}`);
                input.value = '';
            }
        }

        async function processBulk() {
            const rows = document.querySelectorAll('.bulk-row');
            if (rows.length === 0) {
                Swal.fire('No Products', 'Add at least one product row', 'warning');
                return;
            }
            
            // Validate all rows
            let isValid = true;
            let errorMessage = '';
            
            rows.forEach(row => {
                const id = row.id.split('-')[2];
                const title = document.getElementById(`bulk-title-${id}`).value.trim();
                const price = document.getElementById(`bulk-price-${id}`).value.trim();
                
                if (!title || !price) {
                    isValid = false;
                    errorMessage = 'Each product must have a title and price';
                }
                
                if (!bulkRowImagePreviews[id] || bulkRowImagePreviews[id].length === 0) {
                    isValid = false;
                    errorMessage = `Product "${title || 'unnamed'}" must have at least one image`;
                }
            });
            
            if (!isValid) {
                Swal.fire('Validation Error', errorMessage, 'error');
                return;
            }
            
            const { value: confirm } = await Swal.fire({
                title: `Upload ${rows.length} Products?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Start Upload',
                cancelButtonText: 'Cancel'
            });
            
            if (!confirm) return;
            
            // Show uploading overlay
            await showDeletingOverlay('Uploading Products', `Uploading ${rows.length} products...`);
            
            try {
                let completed = 0;
                const total = rows.length;
                
                for (let row of rows) {
                    const id = row.id.split('-')[2];
                    const title = document.getElementById(`bulk-title-${id}`).value.trim();
                    const price = document.getElementById(`bulk-price-${id}`).value.trim();
                    const description = document.getElementById(`bulk-desc-${id}`).value.trim();
                    
                    const payload = {
                        editIndex: -1,
                        product: {
                            title: title,
                            price: parseFloat(price),
                            category: document.getElementById(`bulk-category-${id}`).value,
                            offer: parseInt(document.getElementById(`bulk-offer-${id}`).value) || 0,
                            description: description,
                            existingImages: [],
                            newImages: bulkRowImagePreviews[id],
                            removedImages: []
                        }
                    };
                    
                    const res = await fetch('/api/upload-bulk', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(payload)
                    });
                    
                    if (!res.ok) {
                        throw new Error('Failed to upload product');
                    }
                    
                    completed++;
                    await updateDeletionProgress(Math.round((completed / total) * 100));
                    
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
                
                // Hide overlay and show success
                await hideDeletingOverlay();
                
                Swal.fire({
                    icon: 'success',
                    title: 'Bulk Upload Complete!',
                    text: `${total} products have been uploaded successfully.`,
                    timer: 2000,
                    showConfirmButton: false
                });
                
                document.getElementById('bulkBody').innerHTML = '';
                bulkRowImagePreviews = {};
                updateBulkUploadButton();
                loadData();
                
            } catch (error) {
                await hideDeletingOverlay();
                Swal.fire('Upload Failed', 'Failed to upload products', 'error');
            }
        }

        // --- BANNER FUNCTIONS ---
        function previewBannerImage() {
            const file = document.getElementById('bannerFile').files[0];
            const preview = document.getElementById('bannerPreview');
            const container = document.getElementById('bannerPreviewContainer');
            
            if (!file) {
                container.style.display = 'none';
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = '';
                const div = document.createElement('div');
                div.className = 'preview-box';
                div.innerHTML = `
                    <img src="${e.target.result}" class="preview-img" alt="Banner Preview">
                `;
                preview.appendChild(div);
                container.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }

        async function uploadBanner() {
            const file = document.getElementById('bannerFile').files[0];
            const link = document.getElementById('bannerLink').value.trim();
            
            if (!file) {
                Swal.fire('Missing Image', 'Please select a banner image', 'error');
                return;
            }
            
            // Show uploading overlay
            await showDeletingOverlay('Uploading Banner', 'Uploading banner image...');
            
            try {
                const base64Image = await getBase64(file);
                
                const payload = {
                    image: base64Image,
                    link: link
                };
                
                await updateDeletionProgress(30);
                
                const res = await fetch('/api/upload-banner', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                
                await updateDeletionProgress(70);
                
                const result = await res.json();
                
                if (result.success) {
                    await updateDeletionProgress(100);
                    await hideDeletingOverlay();
                    
                    Swal.fire({
                        icon: 'success',
                        title: 'Banner Uploaded!',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    
                    // Clear form
                    document.getElementById('bannerFile').value = '';
                    document.getElementById('bannerLink').value = '';
                    document.getElementById('bannerPreviewContainer').style.display = 'none';
                    
                    loadData();
                } else {
                    throw new Error('Upload failed');
                }
                
            } catch (error) {
                console.error('Banner upload error:', error);
                await hideDeletingOverlay();
                Swal.fire('Upload Failed', 'Failed to upload banner', 'error');
            }
        }

        function renderBannersList() {
            const container = document.getElementById('bannersList');
            
            if (!banners || banners.length === 0) {
                container.innerHTML = '<p style="color: var(--gray);">No banners added yet.</p>';
                return;
            }
            
            container.innerHTML = `
                <div class="banner-preview-grid">
                    ${banners.map((banner, index) => `
                        <div class="banner-preview-box">
                            <img src="${banner.image}" class="banner-preview-img" alt="Banner ${index + 1}" onerror="this.src='https://via.placeholder.com/300x150'">
                            ${banner.link ? `<div class="banner-link">Link: ${banner.link}</div>` : ''}
                            <button class="remove-btn" onclick="deleteBanner(${index})" style="top: 8px; right: 8px;">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // --- CATEGORY MANAGEMENT ---
        async function addCategory() {
            const input = document.getElementById('newCatInput');
            const val = input.value.trim();
            
            if (!val) {
                Swal.fire('Required', 'Please enter a category name', 'warning');
                return;
            }
            
            if (categories.includes(val)) {
                Swal.fire('Duplicate', 'Category already exists', 'info');
                return;
            }
            
            // Show loading
            const btn = document.querySelector('#categories .btn-primary');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loader"></span> Adding...';
            btn.disabled = true;
            
            try {
                categories.push(val);
                
                await fetch('/api/update-cats', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({categories: categories})
                });
                
                input.value = '';
                updateUI();
                
                btn.innerHTML = originalText;
                btn.disabled = false;
                
                Swal.fire('Success', 'Category added', 'success');
            } catch (error) {
                categories.pop();
                btn.innerHTML = originalText;
                btn.disabled = false;
                Swal.fire('Error', 'Failed to add category', 'error');
            }
        }

        async function delCat(index) {
            const { value: confirm } = await Swal.fire({
                title: 'Delete Category?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Delete',
                cancelButtonText: 'Cancel'
            });
            
            if (!confirm) return;
            
            // Show loading
            await showDeletingOverlay('Deleting Category', 'Removing category from system...');
            
            try {
                categories.splice(index, 1);
                
                await fetch('/api/update-cats', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({categories: categories})
                });
                
                await hideDeletingOverlay();
                updateUI();
                Swal.fire('Deleted', 'Category removed', 'success');
            } catch (error) {
                await hideDeletingOverlay();
                Swal.fire('Error', 'Failed to delete category', 'error');
            }
        }

        function searchProducts() {
            const searchTerm = document.getElementById('searchInput').value.trim();
            renderProductTable(searchTerm);
        }

        // --- STORE SETTINGS ---
        async function saveSettings() {
            const whatsapp = document.getElementById('storeWhatsapp').value.trim();
            if (!whatsapp) {
                Swal.fire('Required', 'Please enter a WhatsApp number', 'warning');
                return;
            }
            // Basic validation: only digits
            if (!/^\d+$/.test(whatsapp)) {
                Swal.fire('Invalid Number', 'WhatsApp number should contain only digits', 'error');
                return;
            }
            
            const btn = document.querySelector('#store-settings .btn-primary');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loader"></span> Saving...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/api/update-settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ whatsappNumber: whatsapp })
                });
                const data = await res.json();
                if (data.success) {
                    whatsappNumber = whatsapp;
                    Swal.fire('Success', 'Settings saved successfully', 'success');
                } else {
                    throw new Error('Failed to save');
                }
            } catch (error) {
                console.error('Save settings error:', error);
                Swal.fire('Error', 'Failed to save settings', 'error');
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }

        // --- NAVIGATION ---
        function nav(id, el) {
            document.querySelectorAll('.section').forEach(s => s.style.display = 'none');
            document.getElementById(id).style.display = 'block';
            document.querySelectorAll('.nav-item').forEach(m => m.classList.remove('active'));
            if (el) el.classList.add('active');
            
            // Show/hide floating button based on active section
            const floatingBtn = document.getElementById('floatingAddBtn');
            if (id === 'bulk-upload') {
                floatingBtn.classList.add('visible');
            } else {
                floatingBtn.classList.remove('visible');
            }
            
            // Clear selections when leaving product management
            if (id !== 'manage-products') {
                selectedProducts.clear();
                updateDeleteSelectedButton();
            }
        }

        async function logout() {
            const { value: confirm } = await Swal.fire({
                title: 'Logout?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Logout',
                cancelButtonText: 'Cancel'
            });
            
            if (confirm) {
                await fetch('/api/logout');
                location.reload();
            }
        }

        function refreshData() {
            loadData();
            Swal.fire({
                title: 'Refreshing...',
                timer: 1000,
                timerProgressBar: true,
                didOpen: () => Swal.showLoading(),
                willClose: () => Swal.fire('Refreshed', 'Data updated', 'success')
            });
        }

        // Add logout button
        document.addEventListener('DOMContentLoaded', function() {
            const sidebarFooter = document.querySelector('.sidebar-footer');
            if (sidebarFooter) {
                const logoutBtn = document.createElement('button');
                logoutBtn.className = 'nav-item';
                logoutBtn.style.marginTop = '8px';
                logoutBtn.style.background = 'rgba(239, 68, 68, 0.1)';
                logoutBtn.style.color = '#ef4444';
                logoutBtn.innerHTML = `
                    <i class="fas fa-sign-out-alt"></i>
                    <span class="nav-text">Logout</span>
                `;
                logoutBtn.onclick = logout;
                sidebarFooter.appendChild(logoutBtn);
            }
        });

        // CSS for loader
        const style = document.createElement('style');
        style.textContent = `
            .loader {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid rgba(37, 99, 235, 0.3);
                border-radius: 50%;
                border-top-color: #2563eb;
                animation: spin 1s ease-in-out infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    </script>
    </body>
    </html>
    """

    def github_api(method, path, token, data=None):
        url = f"https://api.github.com/repos/{path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        try:
            if method == "GET":
                return requests.get(url, headers=headers, timeout=15)
            if method == "PUT":
                return requests.put(url, headers=headers, json=data, timeout=30)
            if method == "DELETE":
                return requests.delete(url, headers=headers, json=data, timeout=30)
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return None

    def delete_file_from_github(path, token, repo):
        """Delete a file from GitHub repository"""
        try:
            # First get the file's SHA
            res = github_api("GET", f"{repo}/contents/{path}", token)
            if res and res.status_code == 200:
                sha = res.json()['sha']
                # Delete the file
                delete_res = github_api("DELETE", f"{repo}/contents/{path}", token, {
                    "message": f"Delete file: {path}",
                    "sha": sha
                })
                if delete_res and delete_res.status_code in [200, 204]:
                    logger.info(f"Deleted file: {path}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False

    @flask_app.route('/')
    def home():
        logger.info("Home route accessed")
        try:
            if os.path.exists(CONFIG_FILE): 
                return render_template_string(ADMIN_TEMPLATE)
            else: 
                return render_template_string(SETUP_TEMPLATE)
        except Exception as e:
            logger.error(f"Error in home route: {e}")
            return f"Error loading application: {e}"

    @flask_app.route('/api/setup', methods=['POST'])
    def setup():
        logger.info("Setup API called")
        try:
            data = request.json
            if not data or 'repo' not in data or 'token' not in data:
                return jsonify({"success": False, "error": "Missing repository or token"})
            
            res = github_api("GET", f"{data['repo']}", data['token'])
            if res and res.status_code == 200:
                with open(CONFIG_FILE, 'w') as f: 
                    json.dump(data, f, indent=2)
                logger.info("Configuration saved")
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Invalid credentials"})
        except Exception as e:
            logger.error(f"Setup error: {e}")
            return jsonify({"success": False, "error": str(e)})

    @flask_app.route('/api/get-data')
    def get_data():
        logger.info("Get data API called")
        try:
            if not os.path.exists(CONFIG_FILE): 
                return jsonify({})
            
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            # Get products
            prods = []
            res_p = github_api("GET", f"{conf['repo']}/contents/all_products.json", conf['token'])
            if res_p and res_p.status_code == 200:
                try:
                    prods = json.loads(base64.b64decode(res_p.json()['content']).decode('utf-8'))
                    logger.info(f"Loaded {len(prods)} products")
                except Exception as e:
                    logger.error(f"Error parsing products: {e}")
                    prods = []
            
            # Get categories and whatsapp number from settings.json
            cats = []
            whatsapp = ''
            res_s = github_api("GET", f"{conf['repo']}/contents/settings.json", conf['token'])
            if res_s and res_s.status_code == 200:
                try:
                    settings = json.loads(base64.b64decode(res_s.json()['content']).decode('utf-8'))
                    cats = settings.get('categories', [])
                    whatsapp = settings.get('whatsappNumber', '')
                except Exception as e:
                    logger.error(f"Error parsing settings: {e}")
            
            # Get banners
            banner_list = []
            res_b = github_api("GET", f"{conf['repo']}/contents/banners.json", conf['token'])
            if res_b and res_b.status_code == 200:
                try:
                    banner_list = json.loads(base64.b64decode(res_b.json()['content']).decode('utf-8'))
                    logger.info(f"Loaded {len(banner_list)} banners")
                except Exception as e:
                    logger.error(f"Error parsing banners: {e}")
                    banner_list = []
            
            return jsonify({"products": prods, "categories": cats, "banners": banner_list, "whatsapp": whatsapp})
        except Exception as e:
            logger.error(f"Get data error: {e}")
            return jsonify({"products": [], "categories": [], "banners": [], "whatsapp": ""})

    @flask_app.route('/api/update-settings', methods=['POST'])
    def update_settings():
        logger.info("Update settings API called")
        try:
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            data = request.json
            whatsapp_number = data.get('whatsappNumber', '')
            
            # Get existing settings
            res = github_api("GET", f"{conf['repo']}/contents/settings.json", conf['token'])
            if res and res.status_code == 200:
                settings = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
                sha = res.json()['sha']
            else:
                settings = {"categories": []}
                sha = None
            
            # Update whatsapp number
            settings['whatsappNumber'] = whatsapp_number
            
            # Prepare content
            content = base64.b64encode(json.dumps(settings, indent=2).encode('utf-8')).decode('utf-8')
            payload = {
                "message": "Update WhatsApp number",
                "content": content,
                "sha": sha
            }
            
            put_res = github_api("PUT", f"{conf['repo']}/contents/settings.json", conf['token'], payload)
            if put_res and put_res.status_code in [200, 201]:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Failed to update settings"})
        except Exception as e:
            logger.error(f"Update settings error: {e}")
            return jsonify({"success": False, "error": str(e)})

    @flask_app.route('/api/update-cats', methods=['POST'])
    def update_cats():
        logger.info("Update categories API called")
        try:
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            res = github_api("GET", f"{conf['repo']}/contents/settings.json", conf['token'])
            sha = res.json()['sha'] if res and res.status_code == 200 else None
            
            # Update only categories in settings
            if sha:
                # Get existing settings first
                existing_settings = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
                existing_settings['categories'] = request.json['categories']
                content = base64.b64encode(json.dumps(existing_settings, indent=2).encode('utf-8')).decode('utf-8')
            else:
                content = base64.b64encode(json.dumps({"categories": request.json['categories']}, indent=2).encode('utf-8')).decode('utf-8')
            
            result = github_api("PUT", f"{conf['repo']}/contents/settings.json", conf['token'], {
                "message": "Update categories",
                "content": content, 
                "sha": sha
            })
            
            if result and result.status_code in [200, 201]:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False})
        except Exception as e:
            logger.error(f"Update categories error: {e}")
            return jsonify({"success": False})

    @flask_app.route('/api/upload', methods=['POST'])
    def upload():
        logger.info("Upload API called")
        try:
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            data = request.json
            edit_idx = int(data.get('editIndex', -1))
            
            # Get existing products
            res = github_api("GET", f"{conf['repo']}/contents/all_products.json", conf['token'])
            if res and res.status_code == 200:
                prods = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
                sha = res.json()['sha']
            else:
                prods = []
                sha = None

            prod = data['product']
            ts = int(time.time()*1000)
            
            # Handle removed images - delete them from GitHub
            removed_images = prod.get('removedImages', [])
            for img_url in removed_images:
                path = extract_image_path_from_url(img_url, conf['repo'])
                if path:
                    delete_file_from_github(path, conf['token'], conf['repo'])
                    logger.info(f"Deleted image: {path}")
            
            # Handle existing images (not removed)
            existing_images = prod.get('existingImages', [])
            
            # Handle new images
            new_images_base64 = prod.get('newImages', [])
            new_image_urls = []
            
            for i, img_b64 in enumerate(new_images_base64):
                time.sleep(0.3)
                # Generate consistent filename using title, description, timestamp
                filename = generate_filename(
                    prod.get('title', 'product'),
                    prod.get('description', ''),
                    ts,
                    f"img_{i}"
                )
                fname = f"images/{filename}"
                upload_res = github_api("PUT", f"{conf['repo']}/contents/{fname}", conf['token'], {
                    "message": "Upload product image",
                    "content": img_b64
                })
                if upload_res and upload_res.status_code in [200, 201]:
                    new_image_urls.append(f"https://raw.githubusercontent.com/{conf['repo']}/main/{fname}")
            
            # Combine existing (non-removed) images with new images
            all_image_urls = existing_images + new_image_urls
            
            # Create product object (buyLink removed)
            item = {
                "id": ts if edit_idx == -1 else prods[edit_idx].get('id', ts),
                "title": prod.get('title', ''),
                "price": prod.get('price', 0),
                "category": prod.get('category', 'General'),
                "offer": prod.get('offer', 0),
                "description": prod.get('description', prod.get('desc', '')),
                "images": all_image_urls,
                "image": all_image_urls[0] if all_image_urls else ""
            }
            
            if edit_idx > -1 and edit_idx < len(prods): 
                prods[edit_idx] = item
                logger.info(f"Updated product at index {edit_idx}")
            else: 
                prods.insert(0, item)
                logger.info("Added new product")
            
            # Update products file
            content = base64.b64encode(json.dumps(prods, indent=2).encode('utf-8')).decode('utf-8')
            update_res = github_api("PUT", f"{conf['repo']}/contents/all_products.json", conf['token'], {
                "message": "Update products",
                "content": content, 
                "sha": sha
            })
            
            if update_res and update_res.status_code in [200, 201]:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False})
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return jsonify({"success": False, "error": str(e)})

    @flask_app.route('/api/upload-bulk', methods=['POST'])
    def upload_bulk():
        logger.info("Bulk upload API called")
        try:
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            data = request.json
            edit_idx = int(data.get('editIndex', -1))
            
            # Get existing products
            res = github_api("GET", f"{conf['repo']}/contents/all_products.json", conf['token'])
            if res and res.status_code == 200:
                prods = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
                sha = res.json()['sha']
            else:
                prods = []
                sha = None

            prod = data['product']
            ts = int(time.time()*1000)
            
            # Handle new images for bulk upload
            new_images_base64 = prod.get('newImages', [])
            new_image_urls = []
            
            for i, img_b64 in enumerate(new_images_base64):
                time.sleep(0.3)
                # Generate consistent filename using title, description, timestamp
                filename = generate_filename(
                    prod.get('title', 'product'),
                    prod.get('description', ''),
                    ts,
                    f"bulk_{i}"
                )
                fname = f"images/{filename}"
                upload_res = github_api("PUT", f"{conf['repo']}/contents/{fname}", conf['token'], {
                    "message": "Upload product image",
                    "content": img_b64
                })
                if upload_res and upload_res.status_code in [200, 201]:
                    new_image_urls.append(f"https://raw.githubusercontent.com/{conf['repo']}/main/{fname}")
            
            # Create product object (buyLink removed)
            item = {
                "id": ts,
                "title": prod.get('title', ''),
                "price": prod.get('price', 0),
                "category": prod.get('category', 'General'),
                "offer": prod.get('offer', 0),
                "description": prod.get('description', ''),
                "images": new_image_urls,
                "image": new_image_urls[0] if new_image_urls else ""
            }
            
            # Always add as new product in bulk upload
            prods.insert(0, item)
            logger.info("Added new product via bulk upload")
            
            # Update products file
            content = base64.b64encode(json.dumps(prods, indent=2).encode('utf-8')).decode('utf-8')
            update_res = github_api("PUT", f"{conf['repo']}/contents/all_products.json", conf['token'], {
                "message": "Bulk upload products",
                "content": content, 
                "sha": sha
            })
            
            if update_res and update_res.status_code in [200, 201]:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False})
        except Exception as e:
            logger.error(f"Bulk upload error: {e}")
            return jsonify({"success": False, "error": str(e)})

    @flask_app.route('/api/upload-banner', methods=['POST'])
    def upload_banner():
        logger.info("Upload banner API called")
        try:
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            data = request.json
            image_b64 = data.get('image', '')
            link = data.get('link', '').strip()
            
            if not image_b64:
                return jsonify({"success": False, "error": "No image provided"})
            
            # Get existing banners
            res = github_api("GET", f"{conf['repo']}/contents/banners.json", conf['token'])
            if res and res.status_code == 200:
                banners = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
                sha = res.json()['sha']
            else:
                banners = []
                sha = None
            
            # Generate consistent filename for banner
            ts = int(time.time()*1000)
            filename = generate_filename(
                "banner",
                link or "banner",
                ts,
                "banner"
            )
            fname = f"banners/{filename}"
            upload_res = github_api("PUT", f"{conf['repo']}/contents/{fname}", conf['token'], {
                "message": "Upload banner image",
                "content": image_b64
            })
            
            if upload_res and upload_res.status_code in [200, 201]:
                image_url = f"https://raw.githubusercontent.com/{conf['repo']}/main/{fname}"
                
                # Add new banner to list
                banners.append({
                    "image": image_url,
                    "link": link
                })
                
                # Update banners file
                content = base64.b64encode(json.dumps(banners, indent=2).encode('utf-8')).decode('utf-8')
                update_res = github_api("PUT", f"{conf['repo']}/contents/banners.json", conf['token'], {
                    "message": "Add banner",
                    "content": content, 
                    "sha": sha
                })
                
                if update_res and update_res.status_code in [200, 201]:
                    return jsonify({"success": True})
            
            return jsonify({"success": False})
        except Exception as e:
            logger.error(f"Upload banner error: {e}")
            return jsonify({"success": False, "error": str(e)})

    @flask_app.route('/api/delete-banner', methods=['POST'])
    def delete_banner():
        logger.info("Delete banner API called")
        try:
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            idx = request.json.get('index', -1)
            if idx == -1:
                return jsonify({"success": False, "error": "Invalid index"})
            
            # Get existing banners
            res = github_api("GET", f"{conf['repo']}/contents/banners.json", conf['token'])
            if res and res.status_code == 200:
                banners = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
                sha = res.json()['sha']
                
                if 0 <= idx < len(banners):
                    # Delete the image file from GitHub
                    banner = banners[idx]
                    path = extract_image_path_from_url(banner['image'], conf['repo'])
                    if path:
                        delete_file_from_github(path, conf['token'], conf['repo'])
                    
                    banners.pop(idx)
                    
                    content = base64.b64encode(json.dumps(banners, indent=2).encode('utf-8')).decode('utf-8')
                    del_res = github_api("PUT", f"{conf['repo']}/contents/banners.json", conf['token'], {
                        "message": "Delete banner",
                        "content": content, 
                        "sha": sha
                    })
                    
                    if del_res and del_res.statusCode in [200, 201]:
                        return jsonify({"success": True})
            
            return jsonify({"success": False, "error": "Banner not found"})
        except Exception as e:
            logger.error(f"Delete banner error: {e}")
            return jsonify({"success": False, "error": str(e)})

    @flask_app.route('/api/delete', methods=['POST'])
    def delete():
        logger.info("Delete API called")
        try:
            with open(CONFIG_FILE, 'r') as f: 
                conf = json.load(f)
            
            idx = request.json.get('index', -1)
            if idx == -1:
                return jsonify({"success": False, "error": "Invalid index"})
            
            res = github_api("GET", f"{conf['repo']}/contents/all_products.json", conf['token'])
            if res and res.status_code == 200:
                prods = json.loads(base64.b64decode(res.json()['content']).decode('utf-8'))
                sha = res.json()['sha']
                
                if 0 <= idx < len(prods):
                    # Delete all image files associated with this product
                    product = prods[idx]
                    image_urls = []
                    if product.get('images'):
                        image_urls = product['images']
                    elif product.get('image'):
                        image_urls = [product['image']]
                    
                    for img_url in image_urls:
                        path = extract_image_path_from_url(img_url, conf['repo'])
                        if path:
                            delete_file_from_github(path, conf['token'], conf['repo'])
                    
                    prods.pop(idx)
                    
                    content = base64.b64encode(json.dumps(prods, indent=2).encode('utf-8')).decode('utf-8')
                    del_res = github_api("PUT", f"{conf['repo']}/contents/all_products.json", conf['token'], {
                        "message": "Delete product",
                        "content": content, 
                        "sha": sha
                    })
                    
                    if del_res and del_res.status_code in [200, 201]:
                        return jsonify({"success": True})
            
            return jsonify({"success": False, "error": "Product not found"})
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return jsonify({"success": False, "error": str(e)})

    @flask_app.route('/api/logout')
    def logout():
        logger.info("Logout API called")
        try:
            if os.path.exists(CONFIG_FILE): 
                os.remove(CONFIG_FILE)
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({"success": False})

    def run_flask():
        try:
            print("Starting App on http://127.0.0.1:5000")
            print("Open your browser and go to the above URL")
            
            import werkzeug.serving
            werkzeug_log = logging.getLogger('werkzeug')
            werkzeug_log.setLevel(logging.ERROR)
            
            flask_app.run(
                host='127.0.0.1',
                port=5000,
                debug=False,
                threaded=True,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Failed to start Flask: {e}")
            print(f"Error: {e}")

    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    time.sleep(2)
    
    webbrowser.open("http://127.0.0.1:5000")
    
    print("\nApp is now running!")
    print("Access at: http://127.0.0.1:5000")
    print("Check run.log for detailed logs")
    
    try:
        while flask_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down App...")