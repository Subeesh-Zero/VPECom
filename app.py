import os
import json
import time
import base64
import io
import subprocess
import webbrowser
import sys
import shutil
from threading import Timer

# --- 1. லைப்ரரி இல்லாத பட்சத்தில் தானாக இன்ஸ்டால் செய்தல் ---
def install_libs():
    try:
        import flask
        import PIL
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask", "Pillow"])

install_libs()

from flask import Flask, request, jsonify, render_template_string
from PIL import Image

app = Flask(__name__)

# --- 2. செட்டிங்ஸ் ---
CONFIG_FILE = "shop_config.json"
IMAGE_FOLDER = "images"
JSON_FILE = "all_products.json"
SETTINGS_FILE = "settings.json"

# ==========================================
# 🎨 SCREEN 1: SETUP
# ==========================================
SETUP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Shop Setup Wizard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; width: 90%; max-width: 400px; }
        h2 { color: #4F46E5; margin-bottom: 10px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #4F46E5; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition:0.3s; }
        button:hover { background: #4338ca; }
        .loader { display: none; border: 4px solid #f3f3f3; border-top: 4px solid #4F46E5; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; margin: 10px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="card">
        <h2>🚀 Ultimate Shop Setup</h2>
        <p>Supports 100k+ Images & Full Delete</p>
        <input type="text" id="repoUrl" placeholder="Paste GitHub Repo Link Here...">
        <button onclick="startSetup()" id="btn">Connect Now</button>
        <div class="loader" id="loader"></div>
        <p id="msg" style="margin-top:15px; font-size:13px; color:#4F46E5;"></p>
    </div>
    <script>
        async function startSetup() {
            const url = document.getElementById('repoUrl').value.trim();
            if(!url) return alert("GitHub Link தேவை!");
            document.getElementById('btn').style.display = 'none';
            document.getElementById('loader').style.display = 'block';
            document.getElementById('msg').innerText = "Configuring Git... (Wait)";
            try {
                const res = await fetch('/api/setup', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ url: url }) });
                const data = await res.json();
                if(data.success) {
                    document.getElementById('msg').innerText = "Success! Redirecting...";
                    setTimeout(() => location.reload(), 2000);
                } else {
                    alert("Error: " + data.error); location.reload();
                }
            } catch(e) { alert("Connection Failed"); location.reload(); }
        }
    </script>
</body>
</html>
"""

# ==========================================
# 🎨 SCREEN 2: ADMIN DASHBOARD
# ==========================================
ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>VPECom Admin Pro</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root { --primary: #4F46E5; --secondary: #10B981; --warning: #F59E0B; --danger: #EF4444; --dark: #1F2937; --light: #F3F4F6; --sidebar-width: 260px; }
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--light); margin: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: var(--sidebar-width); background: var(--dark); color: white; display: flex; flex-direction: column; padding: 20px; transition: 0.3s; z-index: 100; }
        .brand { font-size: 22px; font-weight: 800; color: white; margin-bottom: 40px; display: flex; align-items: center; gap: 10px; }
        .menu-item { padding: 12px 15px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; color: #9CA3AF; display: flex; align-items: center; gap: 12px; font-weight: 500; transition: 0.2s; }
        .menu-item:hover, .menu-item.active { background: var(--primary); color: white; }
        .main { flex: 1; padding: 20px; overflow-y: auto; padding-bottom: 100px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .page-title { font-size: 20px; font-weight: 700; color: var(--dark); }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        label { display: block; margin-bottom: 6px; font-weight: 600; color: #4B5563; font-size: 13px; }
        input, select, textarea { width: 100%; padding: 10px; border: 1px solid #D1D5DB; border-radius: 6px; outline: none; font-size: 14px; background: #F9FAFB; }
        .upload-area { border: 2px dashed #D1D5DB; border-radius: 10px; padding: 20px; text-align: center; cursor: pointer; background: #F9FAFB; transition: 0.2s; }
        .preview-grid { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 5px; margin-top: 10px; }
        .preview-box { flex: 0 0 60px; height: 60px; border-radius: 6px; overflow: hidden; position: relative; border: 1px solid #ddd; }
        .preview-img { width: 100%; height: 100%; object-fit: cover; }
        .remove-btn { position: absolute; top: 0; right: 0; background: rgba(239, 68, 68, 0.9); color: white; width: 18px; height: 18px; font-size: 10px; display: flex; align-items: center; justify-content: center; cursor: pointer; border:none; }
        button { padding: 10px 16px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 14px; transition: 0.2s; }
        .btn-primary { background: var(--primary); color: white; width: 100%; }
        .btn-success { background: var(--secondary); color: white; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-warning { background: var(--warning); color: white; }
        .action-btn { padding: 6px 10px; font-size: 12px; margin-right: 5px; }
        @media (max-width: 768px) {
            .sidebar { width: 100%; height: 60px; flex-direction: row; position: fixed; bottom: 0; left: 0; padding: 0; justify-content: space-around; align-items: center; background: white; border-top: 1px solid #E5E7EB; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
            .brand { display: none; }
            .menu-item { flex-direction: column; gap: 4px; padding: 8px; margin: 0; background: none; }
            .menu-item i { font-size: 20px; }
            .menu-text { font-size: 10px; font-weight: 600; }
            .main { padding: 15px; padding-bottom: 80px; }
            .form-grid { grid-template-columns: 1fr; }
        }
        .table-wrapper { width: 100%; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 600px; }
        th, td { padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: left; vertical-align: middle; }
        th { background: #F3F4F6; color: #6B7280; font-size: 12px; text-transform: uppercase; font-weight: 600; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="brand"><i class="fas fa-layer-group"></i> VPECom</div>
        <div class="menu-item active" onclick="nav('dashboard', this)"><i class="fas fa-home"></i> <span class="menu-text">Home</span></div>
        <div class="menu-item" onclick="nav('add-product', this)"><i class="fas fa-plus-circle"></i> <span class="menu-text">Single</span></div>
        <div class="menu-item" onclick="nav('bulk-upload', this)"><i class="fas fa-th-list"></i> <span class="menu-text">Bulk</span></div>
        <div class="menu-item" onclick="nav('categories', this)"><i class="fas fa-tags"></i> <span class="menu-text">Cats</span></div>
        <div class="menu-item" onclick="nav('manage-products', this)"><i class="fas fa-boxes"></i> <span class="menu-text">Items</span></div>
    </div>
    <div class="main">
        <div id="dashboard" class="section active">
            <div class="header"><div class="page-title">Dashboard Overview</div></div>
            <div class="form-grid">
                <div class="card" style="text-align:center; border-left:4px solid var(--primary);"><div style="font-size:24px; font-weight:700; color:var(--primary);" id="totalProds">0</div><div style="font-size:12px; color:#6B7280;">Total Products</div></div>
                <div class="card" style="text-align:center; border-left:4px solid var(--secondary);"><div style="font-size:24px; font-weight:700; color:var(--secondary);" id="totalCats">0</div><div style="font-size:12px; color:#6B7280;">Categories</div></div>
            </div>
        </div>
        <div id="add-product" class="section" style="display:none;">
            <div class="header"><div class="page-title" id="formTitle">Single Upload</div><button class="btn-danger" style="width:auto; padding:6px 12px;" onclick="resetForm()">New / Clear</button></div>
            <div class="card">
                <input type="hidden" id="editIndex" value="-1">
                <div class="upload-area" onclick="document.getElementById('multiFileInput').click()"><i class="fas fa-images" style="font-size:24px; color:#9CA3AF;"></i><p style="font-size:12px; margin:5px 0;">Tap to Add Images</p></div>
                <input type="file" id="multiFileInput" multiple accept="image/*" style="display:none;" onchange="handleMultiSelect()">
                <div class="preview-grid" id="multiPreview"></div>
                <div class="form-grid" style="margin-top:15px;"><div><label>Title</label><input type="text" id="pTitle" placeholder="Product Name"></div><div><label>Category</label><select id="pCategory" class="cat-drop"></select></div></div>
                <div class="form-grid" style="margin-top:10px;"><div><label>Price (₹)</label><input type="number" id="pPrice" placeholder="₹"></div><div><label>Offer (%)</label><input type="number" id="pOffer" placeholder="0"></div></div>
                <div class="form-grid" style="margin-top:10px;"><div><label>Link</label><input type="text" id="pLink" placeholder="Buy Link"></div></div>
                <div style="margin-top:10px;"><label>Desc</label><textarea id="pDesc" rows="3"></textarea></div>
                <button id="saveBtn" class="btn-primary" style="margin-top:15px;" onclick="saveMultiProduct()">🚀 Upload Product</button>
            </div>
        </div>
        <div id="bulk-upload" class="section" style="display:none;">
            <div class="header"><div class="page-title">Bulk Bundle</div><button class="btn-success" style="width:auto; padding:6px 12px;" onclick="addBulkRow()">+ Row</button></div>
            <div class="card" style="padding:10px;">
                <div class="table-wrapper"><table id="bulkTable"><thead><tr><th style="width:120px;">Images</th><th style="width:180px;">Info</th><th style="width:180px;">Details</th><th style="width:40px;">X</th></tr></thead><tbody id="bulkTableBody"></tbody></table></div>
                <div style="margin-top:15px; text-align:right;"><button class="btn-primary" style="width:auto;" onclick="uploadBulk()">🚀 START BATCH UPLOAD</button></div>
            </div>
        </div>
        <div id="categories" class="section" style="display:none;">
            <div class="header"><div class="page-title">Manage Categories</div></div>
            <div class="card"><div style="display:flex; gap:10px;"><input type="text" id="newCatInput" placeholder="New Category Name"><button class="btn-success" style="width:auto;" onclick="addCategory()">Add</button></div><div id="categoryList" style="display:flex; flex-wrap:wrap; gap:10px; margin-top:15px;"></div></div>
        </div>
        <div id="manage-products" class="section" style="display:none;">
            <div class="header"><div class="page-title">Inventory</div></div>
            <div class="card" style="padding:0;"><div class="table-wrapper"><div id="inventoryContainer" style="padding:10px;">Loading...</div></div></div>
        </div>
    </div>
    <script>
        let products = []; let categories = ["General", "Fashion", "Electronics"]; let multiFiles = []; let existingImages = []; let bulkData = [];
        window.onload = async () => { await loadData(); };
        async function loadData() { try { const res = await fetch('/api/get-data'); const data = await res.json(); if(data.products) products = data.products; if(data.categories) categories = data.categories; updateUI(); } catch(e) { console.log("Init Error"); } }
        function updateUI() {
            document.getElementById('totalProds').innerText = products.length; document.getElementById('totalCats').innerText = categories.length;
            document.querySelectorAll('.cat-drop').forEach(sel => { const v = sel.value; sel.innerHTML = `<option value="">Select</option>` + categories.map(c => `<option value="${c}">${c}</option>`).join(''); if(v) sel.value = v; });
            document.getElementById('categoryList').innerHTML = categories.map((c, i) => `<span style="background:#eef2ff; padding:6px 12px; border-radius:15px; color:#4F46E5; border:1px solid #c7d2fe; font-size:13px;">${c} <i class="fas fa-times" onclick="delCat(${i})" style="color:red;cursor:pointer;margin-left:5px;"></i></span>`).join('');
            let html = `<table style="width:100%"><tr><th>Img</th><th>Name</th><th>Act</th></tr>` + products.map((p, i) => `<tr><td><img src="${p.image}" style="width:40px; height:40px; border-radius:4px; object-fit:cover;"></td><td><span style="font-size:13px; font-weight:600;">${p.title}</span><br><span style="font-size:11px; color:#666;">₹${p.price}</span></td><td><button class="action-btn btn-warning" onclick="editProduct(${i})"><i class="fas fa-edit"></i></button><button class="action-btn btn-danger" onclick="deleteProduct(${i})"><i class="fas fa-trash"></i></button></td></tr>`).join('') + `</table>`;
            document.getElementById('inventoryContainer').innerHTML = html;
        }
        function handleMultiSelect() { Array.from(document.getElementById('multiFileInput').files).forEach(file => { multiFiles.push(file); }); renderPreviews(); }
        function renderPreviews() {
            let html = existingImages.map(url => `<div class="preview-box"><img src="${url}" class="preview-img"></div>`).join('');
            multiFiles.forEach((f, i) => { const reader = new FileReader(); reader.onload = (e) => document.getElementById(`new-${i}`).src = e.target.result; reader.readAsDataURL(f); html += `<div class="preview-box"><img id="new-${i}" class="preview-img"><div class="remove-btn" onclick="multiFiles.splice(${i},1);renderPreviews()">×</div></div>`; });
            document.getElementById('multiPreview').innerHTML = html;
        }
        function editProduct(i) {
            const p = products[i]; document.getElementById('editIndex').value = i; nav('add-product', document.querySelectorAll('.menu-item')[1]); document.getElementById('formTitle').innerText = "Edit Product"; document.getElementById('saveBtn').innerText = "Update Product";
            document.getElementById('pTitle').value = p.title; document.getElementById('pCategory').value = p.category; document.getElementById('pPrice').value = p.price; document.getElementById('pOffer').value = p.offer || 0; document.getElementById('pLink').value = p.buyLink || ""; document.getElementById('pDesc').value = p.description || ""; existingImages = p.images || [p.image]; multiFiles = []; renderPreviews();
        }
        function resetForm() { document.getElementById('editIndex').value = "-1"; document.getElementById('formTitle').innerText = "Single Upload"; document.getElementById('saveBtn').innerText = "🚀 Upload Product"; multiFiles = []; existingImages = []; renderPreviews(); document.querySelectorAll('#add-product input, #add-product textarea').forEach(i => i.value=""); }
        async function saveMultiProduct() {
            const title = document.getElementById('pTitle').value; const price = document.getElementById('pPrice').value; if(!title || !price) return Swal.fire("Error", "Title & Price Required", "error");
            Swal.fire({ title: 'Uploading...', text: 'Smart Upload (Updated JSON Only)...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });
            let imagesBase64 = []; for(let f of multiFiles) { const r = new FileReader(); const p = new Promise(res => { r.onload = e => res(e.target.result); }); r.readAsDataURL(f); imagesBase64.push(await p); }
            const payload = { editIndex: document.getElementById('editIndex').value, products: [{ title, price, category: document.getElementById('pCategory').value, offer: document.getElementById('pOffer').value, desc: document.getElementById('pDesc').value, link: document.getElementById('pLink').value, images: imagesBase64, existingImages: existingImages }] };
            await sendToServer(payload); resetForm();
        }
        function addBulkRow() { if(bulkData.length >= 15) return Swal.fire("Limit", "Max 15 items", "info"); bulkData.push({ id: Date.now(), files: [], title: '', category: categories[0]||'', price: '', offer: '', link: '', desc: '' }); renderBulkRows(); }
        function renderBulkRows() {
            document.getElementById('bulkTableBody').innerHTML = bulkData.map((row, idx) => `<tr><td style="vertical-align:top"><div class="upload-area" style="padding:10px" onclick="document.getElementById('f-${row.id}').click()">+ Img</div><input type="file" id="f-${row.id}" multiple accept="image/*" style="display:none" onchange="handleRowFile(${idx}, this)"><div class="preview-grid">${row.files.map((f, fi) => `<div class="preview-box" style="width:40px;height:40px"><img src="${f.preview}" class="preview-img"><div class="remove-btn" onclick="bulkData[${idx}].files.splice(${fi},1);renderBulkRows()">×</div></div>`).join('')}</div></td><td style="vertical-align:top"><input type="text" placeholder="Title" value="${row.title}" onchange="bulkData[${idx}].title=this.value" style="margin-bottom:5px"><div style="display:flex;gap:5px"><select class="cat-drop" onchange="bulkData[${idx}].category=this.value" style="width:60%">${categories.map(c=>`<option value="${c}" ${row.category===c?'selected':''}>${c}</option>`).join('')}</select><input type="number" placeholder="₹" value="${row.price}" onchange="bulkData[${idx}].price=this.value" style="width:40%"></div></td><td style="vertical-align:top"><input type="number" placeholder="Offer %" value="${row.offer}" onchange="bulkData[${idx}].offer=this.value" style="margin-bottom:5px"><input type="text" placeholder="Link" value="${row.link}" onchange="bulkData[${idx}].link=this.value" style="margin-bottom:5px"><textarea placeholder="Desc" rows="1" onchange="bulkData[${idx}].desc=this.value">${row.desc}</textarea></td><td style="vertical-align:top"><button class="btn-danger" style="padding:5px" onclick="bulkData.splice(${idx},1);renderBulkRows()">×</button></td></tr>`).join('');
        }
        function handleRowFile(idx, input) { Array.from(input.files).forEach(file => { const r = new FileReader(); r.onload = (e) => { bulkData[idx].files.push({ file, preview: e.target.result }); renderBulkRows(); }; r.readAsDataURL(file); }); }
        async function uploadBulk() {
            if(!bulkData.length) return; Swal.fire({ title: 'Batch Uploading...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });
            let payload = { products: [], editIndex: -1 }; for(let row of bulkData) { if(!row.title || !row.price || !row.files.length) continue; let imgs = row.files.map(f => f.preview); payload.products.push({ title: row.title, price: row.price, category: row.category, offer: row.offer, desc: row.desc, link: row.link, images: imgs, existingImages: [] }); }
            await sendToServer(payload); bulkData = []; addBulkRow();
        }
        async function addCategory() { const val = document.getElementById('newCatInput').value.trim(); if(val && !categories.includes(val)) { categories.push(val); await fetch('/api/update-cats', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({categories}) }); updateUI(); document.getElementById('newCatInput').value = ""; } }
        async function delCat(i) { if(!confirm("Remove Category?")) return; categories.splice(i, 1); await fetch('/api/update-cats', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({categories}) }); updateUI(); }
        async function deleteProduct(i) { if(!confirm("Delete Item?")) return; Swal.showLoading(); await fetch('/api/delete', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({index: i}) }); await loadData(); Swal.fire("Deleted", "Item Removed", "success"); }
        async function sendToServer(payload) { try { const res = await fetch('/api/upload', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }); const data = await res.json(); if(data.success) { await loadData(); Swal.fire("Success!", "Updated & Synced!", "success"); } else { Swal.fire("Error", data.error, "error"); } } catch(e) { Swal.fire("Error", "Server Error", "error"); } }
        function nav(id, el) { document.querySelectorAll('.section').forEach(s => s.style.display = 'none'); document.getElementById(id).style.display = 'block'; document.querySelectorAll('.menu-item').forEach(m => m.classList.remove('active')); el.classList.add('active'); }
    </script>
</body>
</html>
"""

# ==========================================
# 🐍 PYTHON BACKEND (FIXED & FULLY FUNCTIONAL)
# ==========================================

@app.route('/')
def home():
    if os.path.exists(CONFIG_FILE): return render_template_string(ADMIN_TEMPLATE)
    else: return render_template_string(SETUP_TEMPLATE)

@app.route('/api/setup', methods=['POST'])
def setup_api():
    try:
        data = request.json
        repo_url = data.get('url')
        if not repo_url: return jsonify({"success": False, "error": "No URL"})

        if os.path.exists(".git"): subprocess.run("rmdir /s /q .git", shell=True)
        if os.path.exists(IMAGE_FOLDER): shutil.rmtree(IMAGE_FOLDER)

        # 1. INIT & CONFIGURE
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "branch", "-M", "main"], check=True) 
        subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)
        
        # 2. SPARSE CHECKOUT
        subprocess.run(["git", "config", "core.sparseCheckout", "true"], check=True)
        sparse_path = os.path.join(".git", "info", "sparse-checkout")
        with open(sparse_path, "w") as f:
            f.write("all_products.json\n")
            f.write("shop_config.json\n")
            f.write("settings.json\n")
        
        # 3. PULL
        subprocess.run(["git", "pull", "origin", "main", "--allow-unrelated-histories"], check=False)

        with open(CONFIG_FILE, 'w') as f: json.dump({"repo": repo_url}, f)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/get-data')
def get_data():
    prods = []
    cats = ["General", "Fashion", "Electronics"]
    
    # --- SYNTAX ERROR FIXED ---
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r') as f:
                prods = json.load(f)
        except:
            pass

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                cats = json.load(f).get('categories', cats)
        except:
            pass
    return jsonify({"products": prods, "categories": cats})

@app.route('/api/update-cats', methods=['POST'])
def update_cats():
    data = request.json
    with open(SETTINGS_FILE, 'w') as f: json.dump(data, f)
    return jsonify({"success": True})

@app.route('/api/delete', methods=['POST'])
def delete_item():
    try:
        idx = request.json.get('index')
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f: products = json.load(f)
            
            if 0 <= idx < len(products):
                # 1. DELETE IMAGES FROM GIT (NEW FIX)
                item = products[idx]
                if 'images' in item:
                    for img in item['images']:
                        # Force delete from git even if file missing locally
                        subprocess.run(["git", "rm", "-f", img], check=False)

                # 2. REMOVE FROM JSON
                products.pop(idx)
                with open(JSON_FILE, 'w') as f: json.dump(products, f, indent=2)
                
                # 3. PUSH CHANGES
                smart_push("Deleted Item")
                
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/upload', methods=['POST'])
def upload():
    try:
        data = request.json
        product_list = data.get('products', [])
        edit_index = int(data.get('editIndex', -1))

        if not os.path.exists(IMAGE_FOLDER): os.makedirs(IMAGE_FOLDER)
        
        current_products = []
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                try: current_products = json.load(f)
                except: pass

        new_entries = []
        for prod in product_list:
            safe_title = "".join(x for x in prod['title'] if x.isalnum()).lower()
            ts = int(time.time() * 1000)
            final_images = prod.get('existingImages', [])
            
            for i, img_b64 in enumerate(prod['images']):
                header, encoded = img_b64.split(",", 1)
                img = Image.open(io.BytesIO(base64.b64decode(encoded))).convert('RGB')
                img.thumbnail((800, 800))
                fname = f"{safe_title}_{ts}_{i}.webp"
                fpath = os.path.join(IMAGE_FOLDER, fname)
                img.save(fpath, format='WEBP', quality=80)
                final_images.append(f"images/{fname}")

            product_obj = { "id": ts if edit_index == -1 else current_products[edit_index]['id'], "title": prod['title'], "price": prod['price'], "category": prod['category'], "offer": prod['offer'], "description": prod['desc'], "buyLink": prod['link'], "images": final_images, "image": final_images[0] if final_images else "" }
            new_entries.append(product_obj)

        if edit_index > -1 and len(new_entries) == 1:
            current_products[edit_index] = new_entries[0]
        else:
            current_products = new_entries + current_products
            
        with open(JSON_FILE, 'w') as f: json.dump(current_products, f, indent=2)

        smart_push(f"Updated {len(new_entries)} items")
        return jsonify({"success": True})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "error": str(e)})

# ==========================================
# 🚀 SMART PUSH (FIXED: SPARSE CHECKOUT ADD)
# ==========================================
def smart_push(msg):
    try:
        subprocess.run(["git", "branch", "-M", "main"], check=False)

        # FIX: 'git add --sparse .' allows adding files outside sparse definition
        subprocess.run(["git", "add", "--sparse", "."], check=True)
        
        subprocess.run(["git", "commit", "-m", msg], check=False)
        
        res = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
        
        if res.returncode != 0:
            print("Syncing JSON...")
            subprocess.run(["git", "pull", "origin", "main", "--no-rebase", "--allow-unrelated-histories"], check=False)
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

    except Exception as e:
        print(f"Git Error: {e}")
        raise e

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000)
