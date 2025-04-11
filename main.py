import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Untuk scaling DPI yang baik
import json
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from ttkbootstrap import Style
import threading
import cv2
from PIL import Image, ImageTk
from functools import partial

class AboutWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Tentang Aplikasi")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        # Style
        self.style = Style(theme="flatly")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self.window, padding=(20, 20, 20, 10))
        main_frame.pack(fill="both", expand=True)
        
        # Application info with better spacing
        ttk.Label(main_frame, text="CCTV Kota Bandung Viewer", 
                 font=('Helvetica', 14, 'bold')).pack(pady=(0, 15))
        
        ttk.Label(main_frame, text="Versi 1.0", 
                 font=('Helvetica', 11)).pack(pady=(0, 20))
        
        # Info container with subtle border
        info_frame = ttk.Frame(main_frame, borderwidth=1, relief="solid", padding=10)
        info_frame.pack(fill="x", pady=(0, 20))
        
        # Copyright info with icon (using emoji as placeholder)
        ttk.Label(info_frame, text="© 2023 Hak Cipta", 
                 font=('Helvetica', 10)).pack(anchor="w")
        ttk.Label(info_frame, text="Giraldi P.Y", 
                 font=('Helvetica', 10, 'bold')).pack(anchor="w", pady=(0, 10))
        
        # Developer info
        ttk.Label(info_frame, text="Dikembangkan oleh:", 
                 font=('Helvetica', 9)).pack(anchor="w")
        ttk.Label(info_frame, text="Tim BlossomBiz", 
                 font=('Helvetica', 9, 'bold')).pack(anchor="w")
        
        # Close button with better styling
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Tutup", 
                  command=self.window.destroy,
                  style='primary.TButton').pack(side="right", ipadx=10)
        
        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'+{x}+{y}')

class CCTVViewer:
    def __init__(self, master, json_file):
        self.master = master
        self.master.title("CCTV Kota Bandung Viewer")
        
        # Set initial size based on screen dimensions
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.master.geometry(f"{int(screen_width*0.8)}x{int(screen_height*0.8)}")
        self.master.minsize(800, 600)
        
        # Style dan tema
        self.style = Style("flatly")
        self.style.configure("TFrame", background=self.style.colors.light)
        self.style.configure("TLabel", background=self.style.colors.light)
        self.style.configure("TButton", padding=6)
        self.style.configure("Title.TLabel", font=('Helvetica', 12, 'bold'))
        self.style.configure("CCTV.TLabel", font=('Helvetica', 10), padding=5)
        
        self.data = self.load_data(json_file)
        self.filtered_data = self.data.copy()
        self.current_process = None
        self.cap = None
        self.video_thread = None
        self.running = False
        self.current_imgtk = None  # To prevent garbage collection
        
        self.create_widgets()
        self.create_menu()
        self.populate_list()
        
        # Bind resize event
        self.master.bind("<Configure>", self.on_window_resize)
        
    def load_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_widgets(self):
        # Main container with padding
        self.main_frame = ttk.Frame(self.master, padding=10)
        self.main_frame.pack(fill="both", expand=True)
        
        # Left panel (list of CCTV) with minimum width
        self.left_panel = ttk.Frame(self.main_frame, width=350)
        self.left_panel.pack(side="left", fill="both", padx=(0, 10))
        self.left_panel.pack_propagate(False)
        
        # Title for CCTV list
        ttk.Label(self.left_panel, text="Daftar CCTV", 
                 style="Title.TLabel").pack(fill="x", pady=(0, 10))
        
        # Search box with better styling
        self.search_frame = ttk.Frame(self.left_panel)
        self.search_frame.pack(fill="x", pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_list)
        
        ttk.Label(self.search_frame, text="🔍 Cari:", 
                 style="TLabel").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(self.search_frame, 
                                    textvariable=self.search_var,
                                    font=('Helvetica', 10))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # List container with scrollbar
        self.list_container = ttk.Frame(self.left_panel)
        self.list_container.pack(fill="both", expand=True)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self.list_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.list_container, 
                                      orient="vertical", 
                                      command=self.canvas.yview)
        
        # Create a frame inside the canvas for the list items
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure the canvas scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"),
                width=e.width  # Set canvas width to match frame width
            )
        )
        
        # Create window in canvas for the scrollable frame
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel for scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Right panel (video display)
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # Video frame with title
        self.video_frame = ttk.Frame(self.right_panel)
        self.video_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ttk.Label(self.video_frame, text="Pemutar CCTV", 
                 style="Title.TLabel").pack(fill="x", pady=(0, 5))
        
        # Canvas untuk menampilkan video with border
        self.video_canvas = tk.Canvas(self.video_frame, bg='black', 
                                     highlightthickness=1, 
                                     highlightbackground="#cccccc")
        self.video_canvas.pack(fill="both", expand=True)
        
        # Initial placeholder text
        self.video_canvas.create_text(
            self.video_canvas.winfo_width()//2, 
            self.video_canvas.winfo_height()//2,
            text="Pilih CCTV dari daftar untuk memulai",
            fill="white",
            font=('Helvetica', 12),
            tags="placeholder"
        )
        
        # Control buttons with better layout
        self.control_frame = ttk.Frame(self.right_panel)
        self.control_frame.pack(fill="x", pady=(10, 0))
        
        self.stop_button = ttk.Button(self.control_frame, 
                                    text="⏹ Stop", 
                                    command=self.stop_stream,
                                    state="disabled",
                                    style='danger.TButton')
        self.stop_button.pack(side="left", padx=5)
        
        # Status bar with better styling
        self.status_frame = ttk.Frame(self.right_panel, height=24)
        self.status_frame.pack(fill="x", side="bottom")
        
        self.status_var = tk.StringVar()
        self.status_var.set("Siap")
        
        self.status_bar = ttk.Label(self.status_frame, 
                                  textvariable=self.status_var, 
                                  relief="sunken", 
                                  anchor="w",
                                  padding=(5, 0),
                                  font=('Helvetica', 9))
        self.status_bar.pack(fill="x")

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling for the canvas"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_menu(self):
        # Create menu bar with better organization
        menubar = tk.Menu(self.master)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Keluar", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Tentang Aplikasi...", command=self.show_about)
        menubar.add_cascade(label="Bantuan", menu=help_menu)
        
        self.master.config(menu=menubar)

    def show_about(self):
        AboutWindow(self.master)

    def populate_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_data:
            empty_label = ttk.Label(self.scrollable_frame, 
                                  text="Tidak ada CCTV yang ditemukan",
                                  style="TLabel")
            empty_label.pack(pady=10)
            return
            
        for item in self.filtered_data:
            # Create a clickable label for each CCTV
            label = ttk.Label(
                self.scrollable_frame, 
                text=item["lokasi"], 
                style="CCTV.TLabel",
                cursor="hand2"
            )
            label.pack(fill="x", pady=2, padx=5)
            
            # Bind click event to the entire label
            label.bind("<Button-1>", lambda e, url=item["link"], loc=item["lokasi"]: self.play_stream(url, loc))
            
            # Change appearance on hover
            label.bind("<Enter>", lambda e: e.widget.configure(style='primary.TLabel'))
            label.bind("<Leave>", lambda e: e.widget.configure(style='CCTV.TLabel'))

    def filter_list(self, *args):
        search = self.search_var.get().lower()
        self.filtered_data = [item for item in self.data if search in item["lokasi"].lower()]
        self.populate_list()

    def play_stream(self, url, lokasi):
        self.stop_stream()  # Stop stream sebelumnya jika ada
        
        self.status_var.set(f"Memuat CCTV: {lokasi}")
        self.master.update()
        self.stop_button.config(state="enabled")
        
        # Clear placeholder text
        self.video_canvas.delete("placeholder")
        
        self.running = True
        self.video_thread = threading.Thread(target=self._video_stream_thread, args=(url, lokasi), daemon=True)
        self.video_thread.start()

    def _video_stream_thread(self, url, lokasi):
        try:
            # Gunakan OpenCV untuk menangkap stream
            self.cap = cv2.VideoCapture(url)
            
            if not self.cap.isOpened():
                self.status_var.set(f"Gagal membuka stream: {lokasi}")
                self.video_canvas.create_text(
                    self.video_canvas.winfo_width()//2, 
                    self.video_canvas.winfo_height()//2,
                    text=f"Gagal memuat CCTV: {lokasi}",
                    fill="white",
                    font=('Helvetica', 12),
                    tags="error"
                )
                return
                
            self.status_var.set(f"Sedang menampilkan: {lokasi}")
            
            # Get frame rate to control display speed
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # Default if cannot get fps
            delay = int(1000 / fps)
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Konversi frame dari BGR ke RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize frame sesuai dengan ukuran canvas
                canvas_width = self.video_canvas.winfo_width()
                canvas_height = self.video_canvas.winfo_height()
                
                if canvas_width > 0 and canvas_height > 0:
                    frame = cv2.resize(frame, (canvas_width, canvas_height))
                
                # Konversi ke format yang bisa ditampilkan di Tkinter
                img = Image.fromarray(frame)
                self.current_imgtk = ImageTk.PhotoImage(image=img)  # Keep reference
                
                # Update gambar di canvas
                self.video_canvas.delete("all")
                self.video_canvas.create_image(0, 0, anchor=tk.NW, image=self.current_imgtk)
                
                # Update the window
                self.master.update_idletasks()
                
                # Delay untuk mengurangi beban CPU dan sinkronisasi frame rate
                cv2.waitKey(delay)
                
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.video_canvas.create_text(
                self.video_canvas.winfo_width()//2, 
                self.video_canvas.winfo_height()//2,
                text=f"Terjadi error: {str(e)}",
                fill="white",
                font=('Helvetica', 12),
                tags="error"
            )
        finally:
            if self.cap:
                self.cap.release()

    def stop_stream(self):
        self.running = False
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear video canvas and show placeholder
        self.video_canvas.delete("all")
        self.video_canvas.create_text(
            self.video_canvas.winfo_width()//2, 
            self.video_canvas.winfo_height()//2,
            text="Pilih CCTV dari daftar untuk memulai",
            fill="white",
            font=('Helvetica', 12),
            tags="placeholder"
        )
        self.status_var.set("Siap")
        self.stop_button.config(state="disabled")

    def on_window_resize(self, event):
        # Adjust layout on window resize
        if event.widget == self.master:
            new_width = self.master.winfo_width()
            
            # Responsive panel widths
            if new_width < 1000:
                self.left_panel.config(width=300)
            elif new_width < 1200:
                self.left_panel.config(width=350)
            else:
                self.left_panel.config(width=400)
            
            # Redraw video if playing
            if self.running and self.cap:
                self.video_canvas.delete("all")

    def cleanup(self):
        self.stop_stream()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        style = Style("flatly")
        app = CCTVViewer(root, "cctv_data.json")
        
        # Handle window close
        root.protocol("WM_DELETE_WINDOW", lambda: [app.cleanup(), root.destroy()])
        
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"Aplikasi error: {str(e)}")