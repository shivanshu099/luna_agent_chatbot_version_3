import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import threading
from dotenv import load_dotenv
load_dotenv()
from workflow import create_workflow
from langchain_core.messages import HumanMessage
import json

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"llm_provider": "grok", "ollama_model": "llama3"}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

HAS_AUDIO_TOOLS = True # Assume true, fallback gracefully in background thread
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

class LunaAIGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Luna AI")
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "luna_ai_icon.png")
            icon_img = ImageTk.PhotoImage(Image.open(icon_path))
            self.iconphoto(False, icon_img)
        except Exception:
            pass
        self.geometry("900x550")
        self.resizable(False, False) # Made it not able to fullscreen
        self.configure(bg="#0F172A")
        
        # Theme: Blue + Teal + Dark
        self.bg_color = "#0F172A"       # Dark background
        self.panel_bg = "#1E293B"       # Lighter dark for panels
        self.teal = "#06B6D4"           # Teal accent
        self.dark_blue = "#1D4ED8"      # Dark Blue accent
        self.light_blue = "#3B82F6"     # Blue hover state
        self.fg_color = "#F8FAFC"       # White-ish text
        self.input_bg = "#334155"       # Input field bg
        
        config_data = load_config()
        self.selected_llm = tk.StringVar(value=config_data.get("llm_provider", "grok"))
        self.ollama_model_name = config_data.get("ollama_model", "llama")
        
        self.chat_history = []
        self.app_workflow = None # Lazily loaded

        self.listener = None
        self.tts = None
        if HAS_AUDIO_TOOLS:
            threading.Thread(target=self._init_audio_models, daemon=True).start()
        
        self.create_widgets()
        
    def _init_audio_models(self):
        print("Loading audio models in background...")
        try:
            from internals_tools import Listener, KokoroTTS
            self.listener = Listener()
            self.tts = KokoroTTS()
            print("Audio models loaded successfully.")
        except Exception as e:
            print(f"Failed to load audio models: {e}")
            global HAS_AUDIO_TOOLS
            HAS_AUDIO_TOOLS = False
        
    def create_widgets(self):
        # Custom Navigation Bar for Tabs
        nav_frame = tk.Frame(self, bg=self.panel_bg, height=45)
        nav_frame.pack(fill=tk.X, side=tk.TOP)
        nav_frame.pack_propagate(False)
        
        self.btn_chat = tk.Button(nav_frame, text="CHAT", font=("Segoe UI", 10, "bold"),
                                  bg=self.teal, fg=self.fg_color, bd=0, cursor="hand2",
                                  command=self.show_chat)
        self.btn_chat.pack(side=tk.LEFT, ipadx=25, fill=tk.Y)
        
        self.btn_settings = tk.Button(nav_frame, text="SETTINGS", font=("Segoe UI", 10, "bold"),
                                      bg=self.panel_bg, fg="#94A3B8", bd=0, cursor="hand2",
                                      command=self.show_settings)
        self.btn_settings.pack(side=tk.LEFT, ipadx=25, fill=tk.Y)
        
        # Footer
        footer_frame = tk.Frame(self, bg=self.bg_color, height=25)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        footer_frame.pack_propagate(False)
        
        lbl_footer = tk.Label(footer_frame, text="made with 💖 by shivanshu prajapati", 
                              font=("Segoe UI", 9, "italic"), bg=self.bg_color, fg="#64748B")
        lbl_footer.pack(side=tk.BOTTOM, pady=2)
        
        # Container for pages
        self.container = tk.Frame(self, bg=self.bg_color)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        self.create_chat_frame()
        self.create_settings_frame()
        
        self.show_chat() # Default tab
        
    def create_chat_frame(self):
        self.chat_frame = tk.Frame(self.container, bg=self.bg_color)
        
        # Main layout container
        main_frame = tk.Frame(self.chat_frame, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        
        # Configure grid for left and right panels
        main_frame.grid_columnconfigure(0, weight=6, uniform="group1")
        main_frame.grid_columnconfigure(1, weight=4, uniform="group1")
        main_frame.grid_rowconfigure(0, weight=1)
        
        # ------------------- LEFT PANEL -------------------
        left_panel = tk.Frame(main_frame, bg=self.panel_bg, highlightbackground="#334155", highlightthickness=1)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Input Area Frame (packed first so it stays at the bottom)
        input_container = tk.Frame(left_panel, bg=self.panel_bg)
        input_container.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(10, 20))
        
        # Separator line before input (packed next at bottom)
        sep = tk.Frame(left_panel, bg="#334155", height=1)
        sep.pack(side=tk.BOTTOM, fill=tk.X, padx=20)
        
        # Chat display area (packed last to take the remaining space)
        self.chat_display = tk.Text(left_panel, bg=self.panel_bg, fg=self.fg_color, 
                                    font=("Segoe UI", 12), bd=0, highlightthickness=0,
                                    wrap=tk.WORD, state=tk.DISABLED,
                                    padx=20, pady=20)
        self.chat_display.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Entry for "ask anything"
        self.ask_entry = tk.Entry(input_container, font=("Segoe UI", 14), bg=self.input_bg, fg="#94A3B8",
                                  bd=1, relief=tk.FLAT, highlightthickness=1, highlightbackground="#475569", highlightcolor=self.teal,
                                  insertbackground=self.fg_color)
        self.ask_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 15))
        self.ask_entry.insert(0, "  Ask anything...")
        self.ask_entry.bind("<FocusIn>", self.on_entry_click)
        self.ask_entry.bind("<FocusOut>", self.on_focusout)
        
        # Send Button 
        self.send_btn = tk.Button(input_container, text="SEND", font=("Segoe UI", 11, "bold"),
                             bg=self.dark_blue, fg=self.fg_color, activebackground=self.light_blue,
                             activeforeground=self.fg_color, bd=0, cursor="hand2", relief=tk.FLAT,
                             command=self.send_text_message)
        self.send_btn.pack(side=tk.RIGHT, fill=tk.Y, ipadx=25, pady=0)
        self.ask_entry.bind("<Return>", lambda e: self.send_text_message())
        
        # ------------------- RIGHT PANEL -------------------
        right_panel = tk.Frame(main_frame, bg=self.bg_color)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Avatar Frame
        avatar_frame = tk.Frame(right_panel, bg=self.panel_bg, highlightbackground="#334155", highlightthickness=1)
        avatar_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Load Ai Avatar Image
        image_path = os.path.join(os.path.dirname(__file__), "luna_avatar.jpg")
        try:
            img = Image.open(image_path)
            img.thumbnail((280, 280), Image.Resampling.LANCZOS)
            self.avatar_img = ImageTk.PhotoImage(img)
            self.avatar_label = tk.Label(avatar_frame, image=self.avatar_img, bg=self.panel_bg)
            self.avatar_label.pack(expand=True)
        except Exception as e:
            self.avatar_label = tk.Label(avatar_frame, text="AI Avatar\n(luna_avatar.jpg not found)", 
                                    bg=self.panel_bg, fg=self.teal, font=("Segoe UI", 16))
            self.avatar_label.pack(expand=True)
            
        # Video Label for voice effect
        self.video_label = tk.Label(avatar_frame, bg=self.panel_bg)
        self.video_label.pack(side=tk.BOTTOM, pady=5)
        self.voice_mode_active = False
            
        # Voice Buttons Frame
        voice_frame = tk.Frame(right_panel, bg=self.bg_color)
        voice_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Voice Input Button
        self.voice_input_btn = tk.Button(voice_frame, text="VOICE INPUT", font=("Segoe UI", 10, "bold"),
                                    bg=self.input_bg, fg=self.fg_color, activebackground="#475569",
                                    activeforeground=self.fg_color, bd=0, cursor="hand2")
        self.voice_input_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=12, padx=(0, 8))
        self.voice_input_btn.bind("<ButtonPress-1>", self.on_voice_press)
        self.voice_input_btn.bind("<ButtonRelease-1>", self.on_voice_release)
        
        # Voice Mode On Button
        self.voice_mode_btn = tk.Button(voice_frame, text="VOICE MODE ON", font=("Segoe UI", 10, "bold"),
                                   bg=self.teal, fg=self.fg_color, activebackground="#0891B2",
                                   activeforeground=self.fg_color, bd=0, cursor="hand2", 
                                   command=self.toggle_voice_mode)
        self.voice_mode_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=12, padx=(8, 0))

    def create_settings_frame(self):
        self.settings_frame = tk.Frame(self.container, bg=self.bg_color)
        
        # Grid layout for the settings
        set_frame = tk.Frame(self.settings_frame, bg=self.bg_color)
        set_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Define Columns
        set_frame.grid_columnconfigure(0, weight=1)
        set_frame.grid_columnconfigure(1, weight=1)
        
        # --- Left Side: LLM Provider ---
        left_col = tk.Frame(set_frame, bg=self.bg_color)
        left_col.grid(row=0, column=0, sticky="nw")
        
        # Bold bordered title mimicking the sketch
        provider_title_frame = tk.Frame(left_col, bg=self.bg_color, highlightbackground=self.panel_bg, highlightthickness=3)
        provider_title_frame.pack(anchor="w", pady=(0, 20))
        
        lbl_provider = tk.Label(provider_title_frame, text="choose llm_provider", font=("Segoe UI", 14),
                                bg=self.bg_color, fg=self.fg_color, padx=10, pady=5)
        lbl_provider.pack()
        
        # Standard tk Radiobuttons for complete dark mode color control
        self.rb_gemini = tk.Radiobutton(left_col, text="gemini", variable=self.selected_llm, value="gemini", 
                                        bg=self.bg_color, fg=self.fg_color, selectcolor=self.input_bg,
                                        activebackground=self.bg_color, activeforeground=self.teal,
                                        font=("Segoe UI", 13), cursor="hand2", bd=0, command=self.on_llm_change)
        self.rb_gemini.pack(anchor="w", pady=8, padx=20)
        
        self.rb_grok = tk.Radiobutton(left_col, text="grok", variable=self.selected_llm, value="grok", 
                                      bg=self.bg_color, fg=self.fg_color, selectcolor=self.input_bg,
                                      activebackground=self.bg_color, activeforeground=self.teal,
                                      font=("Segoe UI", 13), cursor="hand2", bd=0, command=self.on_llm_change)
        self.rb_grok.pack(anchor="w", pady=8, padx=20)
        
        self.rb_ollama = tk.Radiobutton(left_col, text="ollama", variable=self.selected_llm, value="ollama", 
                                        bg=self.bg_color, fg=self.fg_color, selectcolor=self.input_bg,
                                        activebackground=self.bg_color, activeforeground=self.teal,
                                        font=("Segoe UI", 13), cursor="hand2", bd=0, command=self.on_llm_change)
        self.rb_ollama.pack(anchor="w", pady=8, padx=20)
        
        # --- Right Side: Ollama Config ---
        self.right_col = tk.Frame(set_frame, bg=self.bg_color)
        self.right_col.grid(row=0, column=1, sticky="nw", padx=(60, 0))
        
        lbl_info = tk.Label(self.right_col, text="if you chose ollama then which\nmodel", font=("Segoe UI", 12),
                            bg=self.bg_color, fg=self.fg_color, justify=tk.LEFT)
        lbl_info.pack(anchor="w", pady=(5, 20))
        
        input_row = tk.Frame(self.right_col, bg=self.bg_color)
        input_row.pack(fill=tk.X, anchor="w")
        
        lbl_model = tk.Label(input_row, text="model name", font=("Segoe UI", 12),
                             bg=self.bg_color, fg=self.fg_color)
        lbl_model.pack(side=tk.LEFT, padx=(0, 15))
        
        self.ollama_entry = tk.Entry(input_row, font=("Segoe UI", 12), bg=self.input_bg, fg=self.fg_color,
                                     bd=1, relief=tk.FLAT, highlightthickness=2, highlightbackground=self.panel_bg, highlightcolor=self.teal,
                                     insertbackground=self.fg_color, width=15)
        self.ollama_entry.pack(side=tk.LEFT, ipady=6)
        self.ollama_entry.insert(0, self.ollama_model_name)
        
        # Save Model Button
        save_model_btn = tk.Button(input_row, text="SAVE", font=("Segoe UI", 9, "bold"), 
                                   bg=self.teal, fg=self.fg_color, activebackground="#0891B2",
                                   activeforeground=self.fg_color, bd=0, cursor="hand2", 
                                   command=self.on_ollama_model_change)
        save_model_btn.pack(side=tk.LEFT, padx=10, ipadx=15, ipady=4)
        
        # --- Bottom Row: Clear Memory & Edit .env ---
        bottom_frame = tk.Frame(set_frame, bg=self.bg_color)
        bottom_frame.grid(row=1, column=0, columnspan=2, sticky="sw", pady=(40, 0))
        
        clear_mem_btn = tk.Button(bottom_frame, text="🗑  CLEAR MEMORY", font=("Segoe UI", 10, "bold"),
                                  bg="#DC2626", fg=self.fg_color, activebackground="#EF4444",
                                  activeforeground=self.fg_color, bd=0, cursor="hand2",
                                  command=self.clear_memory)
        clear_mem_btn.pack(side=tk.LEFT, ipadx=20, ipady=10, padx=(0, 15))
        
        edit_env_btn = tk.Button(bottom_frame, text="⚙  EDIT .ENV", font=("Segoe UI", 10, "bold"),
                                 bg=self.dark_blue, fg=self.fg_color, activebackground=self.light_blue,
                                 activeforeground=self.fg_color, bd=0, cursor="hand2",
                                 command=self.open_env_editor)
        edit_env_btn.pack(side=tk.LEFT, ipadx=20, ipady=10)
        
        # Make bottom row stick to bottom
        set_frame.grid_rowconfigure(1, weight=1)
        
        # Hide the right side if ollama is not initially selected
        self.on_llm_change()

    def clear_memory(self):
        """Clear all ChromaDB memories with a confirmation dialog."""
        confirm_win = tk.Toplevel(self)
        confirm_win.title("Confirm Clear Memory")
        confirm_win.geometry("380x180")
        confirm_win.resizable(False, False)
        confirm_win.configure(bg=self.panel_bg)
        confirm_win.transient(self)
        confirm_win.grab_set()
        
        # Center on parent
        confirm_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 190
        y = self.winfo_y() + (self.winfo_height() // 2) - 90
        confirm_win.geometry(f"+{x}+{y}")
        
        tk.Label(confirm_win, text="⚠️  Clear All Memories?", font=("Segoe UI", 14, "bold"),
                 bg=self.panel_bg, fg="#FBBF24").pack(pady=(25, 10))
        tk.Label(confirm_win, text="This will permanently delete all stored memories.\nThis action cannot be undone.",
                 font=("Segoe UI", 10), bg=self.panel_bg, fg="#94A3B8", justify=tk.CENTER).pack(pady=(0, 20))
        
        btn_frame = tk.Frame(confirm_win, bg=self.panel_bg)
        btn_frame.pack()
        
        def do_clear():
            try:
                import chromadb
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luna_memory_db")
                client = chromadb.PersistentClient(path=db_path)
                client.delete_collection("luna_memories")
                client.get_or_create_collection(name="luna_memories", metadata={"hnsw:space": "cosine"})
                confirm_win.destroy()
                self._show_toast("All memories cleared successfully.")
            except Exception as e:
                confirm_win.destroy()
                self._show_toast(f"Error: {e}")
        
        tk.Button(btn_frame, text="DELETE ALL", font=("Segoe UI", 10, "bold"),
                  bg="#DC2626", fg=self.fg_color, activebackground="#EF4444",
                  bd=0, cursor="hand2", command=do_clear).pack(side=tk.LEFT, ipadx=15, ipady=5, padx=(0, 10))
        tk.Button(btn_frame, text="CANCEL", font=("Segoe UI", 10, "bold"),
                  bg=self.input_bg, fg=self.fg_color, activebackground="#475569",
                  bd=0, cursor="hand2", command=confirm_win.destroy).pack(side=tk.LEFT, ipadx=15, ipady=5)

    def open_env_editor(self):
        """Open a popup window to edit the .env file."""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        
        editor_win = tk.Toplevel(self)
        editor_win.title("Edit .env")
        editor_win.geometry("600x420")
        editor_win.resizable(False, False)
        editor_win.configure(bg=self.panel_bg)
        editor_win.transient(self)
        editor_win.grab_set()
        
        # Center on parent
        editor_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 300
        y = self.winfo_y() + (self.winfo_height() // 2) - 210
        editor_win.geometry(f"+{x}+{y}")
        
        # Title bar
        title_frame = tk.Frame(editor_win, bg=self.bg_color)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        tk.Label(title_frame, text="⚙  .env Configuration", font=("Segoe UI", 13, "bold"),
                 bg=self.bg_color, fg=self.fg_color, padx=10, pady=5).pack(side=tk.LEFT)
        
        # Text editor
        text_editor = tk.Text(editor_win, font=("Consolas", 11), bg=self.input_bg, fg=self.fg_color,
                              insertbackground=self.fg_color, bd=0, highlightthickness=2,
                              highlightbackground="#475569", highlightcolor=self.teal,
                              wrap=tk.NONE, padx=10, pady=10)
        text_editor.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Load current .env content
        try:
            with open(env_path, "r") as f:
                content = f.read()
            text_editor.insert("1.0", content)
        except FileNotFoundError:
            text_editor.insert("1.0", "# Add your environment variables here\n")
        
        # Button row
        btn_frame = tk.Frame(editor_win, bg=self.panel_bg)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.env_status_label = tk.Label(btn_frame, text="", font=("Segoe UI", 9),
                                         bg=self.panel_bg, fg=self.teal)
        self.env_status_label.pack(side=tk.LEFT)
        
        def save_env():
            try:
                new_content = text_editor.get("1.0", tk.END).rstrip() + "\n"
                with open(env_path, "w") as f:
                    f.write(new_content)
                # Reload environment variables
                from dotenv import load_dotenv
                load_dotenv(env_path, override=True)
                self.env_status_label.config(text="✅ Saved & reloaded!", fg="#22C55E")
            except Exception as e:
                self.env_status_label.config(text=f"❌ {e}", fg="#DC2626")
        
        tk.Button(btn_frame, text="SAVE", font=("Segoe UI", 10, "bold"),
                  bg=self.teal, fg=self.fg_color, activebackground="#0891B2",
                  bd=0, cursor="hand2", command=save_env).pack(side=tk.RIGHT, ipadx=25, ipady=5, padx=(10, 0))
        tk.Button(btn_frame, text="CANCEL", font=("Segoe UI", 10, "bold"),
                  bg=self.input_bg, fg=self.fg_color, activebackground="#475569",
                  bd=0, cursor="hand2", command=editor_win.destroy).pack(side=tk.RIGHT, ipadx=15, ipady=5)

    def set_avatar_image(self, image_name):
        def _update():
            try:
                image_path = os.path.join(os.path.dirname(__file__), image_name)
                img = Image.open(image_path)
                img.thumbnail((280, 280), Image.Resampling.LANCZOS)
                self.avatar_img = ImageTk.PhotoImage(img)
                self.avatar_label.config(image=self.avatar_img)
            except Exception:
                pass
        self.after(0, _update)

    def _show_toast(self, message, duration=2000):
        """Show a brief toast message on screen."""
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.configure(bg=self.panel_bg)
        toast.attributes("-topmost", True)
        
        toast.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + self.winfo_height() - 80
        toast.geometry(f"300x40+{x}+{y}")
        
        tk.Label(toast, text=message, font=("Segoe UI", 10), bg=self.panel_bg, fg=self.teal).pack(expand=True)
        toast.after(duration, toast.destroy)

    def update_chat_display(self, text, sender="Luna"):
        """Thread-safe chat display update — schedules on main thread."""
        def _update():
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"{sender}: {text}\n\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        self.after(0, _update)

    def process_llm_response(self, user_text):
        """Runs in a background thread. All GUI updates go through after()."""
        self.update_chat_display(user_text, "You")
        self.chat_history.append(HumanMessage(content=user_text))
        
        # Limit chat history to last 10 messages to reduce API cost
        MAX_HISTORY = 10
        if len(self.chat_history) > MAX_HISTORY:
            self.chat_history = self.chat_history[-MAX_HISTORY:]
            
        if not self.app_workflow:
            try:
                self.app_workflow = create_workflow(self.selected_llm.get(), self.ollama_model_name)
            except Exception as e:
                self.update_chat_display(f"Initialization Error: {e}", "System")
                return

        try:
            # Show thinking indicator while LLM processes
            self.set_avatar_image("luna_thinking.png")
            if self.voice_mode_active:
                self.update_chat_display("thinking...", "Luna")
            
            response = self.app_workflow.invoke({"messages": self.chat_history})
            self.chat_history = response["messages"]
            final_message_obj = self.chat_history[-1]
            
            if hasattr(final_message_obj, "content") and final_message_obj.content:
                content = final_message_obj.content
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            text_parts.append(item["text"])
                        elif isinstance(item, str):
                            text_parts.append(item)
                    final_text = "".join(text_parts) if text_parts else str(content)
                else:
                    final_text = str(content)
            else:
                final_text = "[Action completed]"
            
            if self.voice_mode_active and self.tts:
                # Speak first, then replace "thinking..." with real text
                self.tts.speak(final_text)
                self._replace_thinking_with(final_text)
            else:
                self.update_chat_display(final_text, "Luna")
                
            self.set_avatar_image("luna_avatar.jpg")
                
        except Exception as e:
            self.set_avatar_image("luna_avatar.jpg")
            
            err_str = str(e).lower()
            if "429" in err_str or "rate limit" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                short_err = "API Error: Rate limit or Quota exceeded."
            elif "401" in err_str or "unauthorized" in err_str or "api key" in err_str:
                short_err = "API Error: Invalid or missing API key."
            else:
                raw_err = str(e)
                short_err = f"API Error: {raw_err[:60]}..." if len(raw_err) > 60 else f"API Error: {raw_err}"
                
            if self.voice_mode_active:
                self._replace_thinking_with(short_err)
            else:
                self.update_chat_display(short_err, "System")

    def _replace_thinking_with(self, final_text):
        """Replace the last 'Luna: thinking...' line with the actual response."""
        def _do_replace():
            self.chat_display.config(state=tk.NORMAL)
            # Search backwards for "Luna: thinking..."
            pos = self.chat_display.search("Luna: thinking...", "end", backwards=True, exact=True)
            if pos:
                # Delete from that position to the end of "thinking...\n\n"
                line = int(pos.split(".")[0])
                self.chat_display.delete(f"{line}.0", f"{line + 1}.end")
                self.chat_display.insert(f"{line}.0", f"Luna: {final_text}\n")
            else:
                # Fallback: just append
                self.chat_display.insert(tk.END, f"Luna: {final_text}\n\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        self.after(0, _do_replace)

    def send_text_message(self):
        """Called from main thread — grabs text, then offloads LLM work."""
        text = self.ask_entry.get().strip()
        if text and text != "Ask anything...":
            self.ask_entry.delete(0, tk.END)
            self.ask_entry.config(fg=self.fg_color)
            threading.Thread(target=self.process_llm_response, args=(text,), daemon=True).start()

    def on_voice_press(self, event):
        """Push-to-talk: start recording on button press."""
        if not self.listener:
            self.update_chat_display("Audio models are still loading. Please wait...", "System")
            return
        self.voice_input_btn.config(bg="#DC2626", text="🎤 RECORDING...")  # Red when recording
        self.listener.start_recording()

    def on_voice_release(self, event):
        """Push-to-talk: stop recording on button release, transcribe & send."""
        self.voice_input_btn.config(bg=self.input_bg, text="VOICE INPUT")
        if self.listener and self.listener.is_recording:
            def process_voice():
                text = self.listener.stop_recording()
                if text:
                    self.process_llm_response(text)
                else:
                    self.update_chat_display("Could not understand audio. Try again.", "System")
            threading.Thread(target=process_voice, daemon=True).start()

    def show_chat(self):
        self.settings_frame.pack_forget()
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        # Update tab visuals
        self.btn_chat.config(bg=self.teal, fg=self.fg_color)
        self.btn_settings.config(bg=self.panel_bg, fg="#94A3B8")
        
    def show_settings(self):
        self.chat_frame.pack_forget()
        self.settings_frame.pack(fill=tk.BOTH, expand=True)
        # Update tab visuals
        self.btn_settings.config(bg=self.teal, fg=self.fg_color)
        self.btn_chat.config(bg=self.panel_bg, fg="#94A3B8")

    def on_llm_change(self):
        selected = self.selected_llm.get()
        config_data = load_config()
        config_data["llm_provider"] = selected
        save_config(config_data)
        
        self.app_workflow = None # Will load lazily on next message
            
        # Visually highlight the selected option text in Teal, turn others generic white
        try:
            self.rb_gemini.config(fg=self.teal if selected == "gemini" else self.fg_color)
            self.rb_grok.config(fg=self.teal if selected == "grok" else self.fg_color)
            self.rb_ollama.config(fg=self.teal if selected == "ollama" else self.fg_color)
        except AttributeError:
            pass # Fails cleanly during initial setup before rb elements exist
            
        if selected == "ollama":
            self.right_col.grid()
        else:
            self.right_col.grid_remove()

    def on_ollama_model_change(self):
        new_model = self.ollama_entry.get().strip()
        if new_model:
            self.ollama_model_name = new_model
            config_data = load_config()
            config_data["ollama_model"] = self.ollama_model_name
            save_config(config_data)
            self._show_toast(f"Saved Ollama model: {self.ollama_model_name}")
            if self.selected_llm.get() == "ollama":
                self.app_workflow = None

    def on_entry_click(self, event):
        if self.ask_entry.get().strip() == "Ask anything...":
            self.ask_entry.delete(0, "end")
            self.ask_entry.config(fg=self.fg_color)
            
    def on_focusout(self, event):
        if self.ask_entry.get().strip() == "":
            self.ask_entry.insert(0, "  Ask anything...")
            self.ask_entry.config(fg="#94A3B8")

    def toggle_voice_mode(self):
        if not HAS_CV2:
            self.video_label.config(text="(OpenCV missing. Run: pip install opencv-python)", fg="#94A3B8")
            return
            
        self.voice_mode_active = not self.voice_mode_active
        if self.voice_mode_active:
            self.voice_mode_btn.config(text="VOICE MODE OFF", bg="#DC2626", activebackground="#EF4444")
            video_path = os.path.join(os.path.dirname(__file__), "voice_effect.mp4")
            self.cap = cv2.VideoCapture(video_path)
            self.play_video_frame()
        else:
            self.voice_mode_btn.config(text="VOICE MODE ON", bg=self.teal, activebackground="#0891B2")
            if hasattr(self, 'cap'):
                self.cap.release()
            self.video_label.config(image='')
            
    def play_video_frame(self):
        if hasattr(self, 'voice_mode_active') and self.voice_mode_active and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image)
                # scale to fit underneath avatar nicely
                img.thumbnail((280, 80), Image.Resampling.LANCZOS)
                
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                self.after(33, self.play_video_frame)
            else:
                # loop back to beginning
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.after(33, self.play_video_frame)

if __name__ == "__main__":
    app = LunaAIGUI()
    app.mainloop()
