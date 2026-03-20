import subprocess
import sys

# --- Auto Installer for CTkMessagebox ---
def install_dependencies():
    dependencies = ["CTkMessagebox"]
    for dependency in dependencies:
        try:
            __import__(dependency)
        except ImportError:
            print(f"📦 Installing {dependency}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dependency])

install_dependencies()

# --- Main Imports ---
import os
import base64
import webbrowser
import threading
import requests
import json
import uuid

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox

# Professional theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Firebase credentials
FIREBASE_API_KEY = "AIzaSyBZn7Lcd-LqQxxEAEJcGV0J3brlDo5wKhc"
PROJECT_ID = "projectaxis-by-subeesh"

class ProjectAxisDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("ProjectAxis Dashboard")
        self.geometry("600x500")
        try:
            self.iconbitmap("app_icon.ico")
        except:
            pass
        
        self.resizable(False, False)
        self.center_window()
        
        # Device ID (Motherboard UUID)
        self.system_uuid = self.get_motherboard_uuid()
        
        # Define secure storage path
        self.config_dir = os.path.join(os.path.expanduser('~'), '.vpecom')
        self.auth_file = os.path.join(self.config_dir, 'admin_auth.json')
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Build login screen
        self.build_login_screen()
        # Auto-fill saved credentials
        self.load_saved_credentials()

    def get_motherboard_uuid(self):
        """Hardware Binding: Retrieve motherboard UUID."""
        try:
            result = subprocess.check_output('wmic csproduct get uuid', shell=True)
            return result.decode('utf-8').split('\n')[1].strip()
        except Exception:
            mac = uuid.getnode()
            return ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ==========================================
    # 1. LOGIN SCREEN UI & LOGIC (Refined)
    # ==========================================
    def build_login_screen(self):
        self.login_container = ctk.CTkFrame(self, fg_color="transparent")
        self.login_container.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Logo & Title
        logo_frame = ctk.CTkFrame(self.login_container, fg_color="transparent")
        logo_frame.pack(pady=(20, 10))
        
        ctk.CTkLabel(logo_frame, text="⚡", font=("Arial", 45), text_color="#3B82F6").pack()
        ctk.CTkLabel(logo_frame, text="PROJECTAXIS", font=("Arial", 28, "bold"), text_color="white").pack(pady=(5, 0))
        ctk.CTkLabel(logo_frame, text="Secure Device Authentication", font=("Arial", 12), text_color="#94A3B8").pack()

        # Email entry
        self.email_entry = ctk.CTkEntry(self.login_container, placeholder_text="Customer Email", width=300, height=45, font=("Arial", 14))
        self.email_entry.pack(pady=(0, 8))

        # Password entry
        self.password_entry = ctk.CTkEntry(self.login_container, placeholder_text="Password", show="*", width=300, height=45, font=("Arial", 14))
        self.password_entry.pack(pady=(0, 8))

        # Forgot Password link (above login button)
        self.forgot_label = ctk.CTkLabel(
            self.login_container, text="Forgot Password?",
            font=("Arial", 12, "underline"), text_color="#94A3B8", cursor="hand2"
        )
        self.forgot_label.pack(pady=(0, 5))
        self.forgot_label.bind("<Button-1>", lambda e: self.show_contact_popup())

        # Login button (compact gap)
        self.login_btn = ctk.CTkButton(
            self.login_container, text="🔐 SECURE LOGIN", command=self.process_login,
            width=300, height=45, font=("Arial", 15, "bold"),
            fg_color="#3B82F6", hover_color="#2563EB", corner_radius=8
        )
        self.login_btn.pack(pady=(0, 8))

        # Create Account link (below login button)
        self.create_label = ctk.CTkLabel(
            self.login_container, text="New User? Create Account",
            font=("Arial", 12, "underline"), text_color="#94A3B8", cursor="hand2"
        )
        self.create_label.pack(pady=(0, 10))
        self.create_label.bind("<Button-1>", lambda e: self.show_contact_popup())

        # Social links (Portfolio & Instagram)
        social_frame = ctk.CTkFrame(self.login_container, fg_color="transparent")
        social_frame.pack(pady=(5, 10))
        
        self.portfolio_btn = ctk.CTkButton(
            social_frame, text="🌐 Portfolio", command=self.open_portfolio,
            width=120, height=35, font=("Arial", 12), fg_color="#1E293B", hover_color="#334155", corner_radius=8
        )
        self.portfolio_btn.pack(side="left", padx=5)
        
        self.instagram_btn = ctk.CTkButton(
            social_frame, text="📸 Instagram", command=self.open_instagram,
            width=120, height=35, font=("Arial", 12), fg_color="#1E293B", hover_color="#334155", corner_radius=8
        )
        self.instagram_btn.pack(side="left", padx=5)

        # Version label (stays at bottom)
        self.version_label = ctk.CTkLabel(
            self.login_container, text="ProjectAxis v1.0 - Secured",
            font=("Arial", 10), text_color="#6B7280"
        )
        self.version_label.pack(side="bottom", anchor="se", padx=10, pady=8)

    def load_saved_credentials(self):
        """Auto-fill email and password if saved."""
        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'r') as f:
                    data = json.load(f)
                    email = data.get('email', '')
                    password_b64 = data.get('password', '')
                    if email and password_b64:
                        try:
                            password = base64.b64decode(password_b64).decode('utf-8')
                            self.email_entry.insert(0, email)
                            self.password_entry.insert(0, password)
                        except:
                            pass
        except Exception as e:
            print(f"Error loading saved credentials: {e}")

    def save_credentials(self, email, password):
        """Securely save email and base64‑encoded password after successful login."""
        try:
            password_b64 = base64.b64encode(password.encode('utf-8')).decode('utf-8')
            data = {'email': email, 'password': password_b64}
            with open(self.auth_file, 'w') as f:
                json.dump(data, f, indent=2)
            if sys.platform != 'win32':
                os.chmod(self.auth_file, 0o600)
        except Exception as e:
            print(f"Error saving credentials: {e}")

    def show_contact_popup(self):
        """Show a unified popup with admin contact details."""
        CTkMessagebox(
            title="Access Restricted",
            message="Please contact ProjectAxis Admin to manage your credentials.\n\n📞 Phone: +91 7695958035",
            icon="info",
            option_1="OK"
        )

    def process_login(self):
        self.login_btn.configure(text="⏳ VERIFYING...", state="disabled")
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            self.show_error("Please enter email and password")
            return

        threading.Thread(target=self.verify_with_firebase, args=(email, password), daemon=True).start()

    def verify_with_firebase(self, email, password):
        try:
            # Step A: User Authentication via REST API
            auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            auth_payload = {"email": email, "password": password, "returnSecureToken": True}
            auth_req = requests.post(auth_url, json=auth_payload)
            auth_data = auth_req.json()

            if "error" in auth_data:
                self.show_error("Invalid Email or Password!")
                return

            id_token = auth_data["idToken"]

            # Step B: Get User's Device ID from Firestore
            db_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{email}"
            headers = {"Authorization": f"Bearer {id_token}"}
            db_req = requests.get(db_url, headers=headers)
            db_data = db_req.json()

            if "fields" not in db_data:
                self.show_error("Account setup incomplete. Contact Admin.")
                return

            saved_device_id = db_data["fields"].get("deviceID", {}).get("stringValue", "")

            # Step C: Device Lock Logic
            success = False
            if saved_device_id == "":
                # First time login - Save this PC's UUID to Firebase
                update_url = f"{db_url}?updateMask.fieldPaths=deviceID"
                update_payload = {"fields": {"deviceID": {"stringValue": self.system_uuid}, "createdAt": db_data["fields"].get("createdAt", {})}}
                requests.patch(update_url, headers=headers, json=update_payload)
                success = True
            elif saved_device_id == self.system_uuid:
                success = True
            else:
                self.show_error("Device Locked! This account is registered to another PC.")
                return

            if success:
                self.after(0, lambda: self.save_credentials(email, password))
                self.show_dashboard()
        except Exception as e:
            self.show_error("Network Error: Check internet connection.")

    def show_error(self, message):
        """Show error popup and re-enable login button."""
        self.after(0, lambda: CTkMessagebox(
            title="Login Failed",
            message=message,
            icon="cancel",
            option_1="OK"
        ))
        self.after(0, lambda: self.login_btn.configure(text="🔐 SECURE LOGIN", state="normal"))

    # ==========================================
    # 2. DASHBOARD (Unchanged)
    # ==========================================
    def show_dashboard(self):
        self.after(0, self.login_container.pack_forget)
        self.after(0, self._build_original_dashboard)

    def _build_original_dashboard(self):
        # --- Dashboard UI (same as before, not modified) ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(pady=(0, 30))
        
        self.logo_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.logo_frame.pack()
        
        self.logo = ctk.CTkLabel(self.logo_frame, text="⚡", font=("Arial", 40), text_color="#3B82F6")
        self.logo.pack()
        
        self.title = ctk.CTkLabel(self.logo_frame, text="PROJECTAXIS", font=("Arial", 28, "bold"), text_color="white")
        self.title.pack(pady=(5, 0))
        
        self.subtitle = ctk.CTkLabel(self.logo_frame, text="Designed & Engineered for ProjectAxis by Subeesh", font=("Arial", 12), text_color="#94A3B8")
        self.subtitle.pack(pady=(5, 0))
        
        # Status Indicator
        self.status_frame = ctk.CTkFrame(self.main_container, fg_color="#1E293B", corner_radius=20)
        self.status_frame.pack(fill="x", pady=(0, 30))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: ● Ready & Verified", font=("Arial", 12), text_color="#10B981")
        self.status_label.pack(pady=12)
        
        # Control Buttons
        self.buttons_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.buttons_frame.pack(pady=(0, 30))
        
        self.start_btn = ctk.CTkButton(
            self.buttons_frame, text="🚀 START ENGINE", command=self.start_engine,
            width=250, height=50, font=("Arial", 16, "bold"), fg_color="#3B82F6", hover_color="#2563EB", corner_radius=10
        )
        self.start_btn.pack(pady=10)
        
        self.exit_btn = ctk.CTkButton(
            self.buttons_frame, text="⏹️ EXIT", command=self.quit_app,
            width=250, height=50, font=("Arial", 16, "bold"), fg_color="#6B7280", hover_color="#4B5563", corner_radius=10
        )
        self.exit_btn.pack(pady=10)
        
        # Social Links
        self.social_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.social_frame.pack(pady=(0, 30))
        
        self.portfolio_btn = ctk.CTkButton(self.social_frame, text="🌐 Portfolio", command=self.open_portfolio, width=120, height=35, font=("Arial", 12), fg_color="#1E293B", hover_color="#334155", corner_radius=8)
        self.portfolio_btn.pack(side="left", padx=5)
        
        self.instagram_btn = ctk.CTkButton(self.social_frame, text="📸 Instagram", command=self.open_instagram, width=120, height=35, font=("Arial", 12), fg_color="#1E293B", hover_color="#334155", corner_radius=8)
        self.instagram_btn.pack(side="left", padx=5)
        
        # Footer
        self.footer_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.footer_frame.pack(fill="x")
        
        self.footer_label = ctk.CTkLabel(self.footer_frame, text="© 2024 ProjectAxis | Powered by Subeesh", font=("Arial", 10), text_color="#6B7280")
        self.footer_label.pack()

    def start_engine(self):
        self.start_btn.configure(text="▶️ ENGINE RUNNING...", state="disabled", fg_color="#6B7280")
        self.status_label.configure(text="Status: ● Running", text_color="#F59E0B")
        threading.Thread(target=self.launch_main_app, daemon=True).start()
    
    def launch_main_app(self):
        try:
            import app
            if hasattr(app, 'start_my_app'):
                app.start_my_app()
            elif hasattr(app, 'main'):
                app.main()
        except Exception as e:
            print(f"Error: {e}")
            self.reset_engine()
    
    def reset_engine(self):
        self.start_btn.configure(text="🚀 START ENGINE", state="normal", fg_color="#3B82F6")
        self.status_label.configure(text="Status: ● Ready & Verified", text_color="#10B981")
    
    def open_portfolio(self): webbrowser.open("https://subeesh-zero.github.io/Profile/")
    def open_instagram(self): webbrowser.open("https://www.instagram.com/subeesh.zero")
    def quit_app(self): self.quit()

if __name__ == "__main__":
    app = ProjectAxisDashboard()
    app.mainloop()