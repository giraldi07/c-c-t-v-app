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
        # Main frame
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Application info
        ttk.Label(main_frame, text="CCTV Kota Bandung Viewer", 
                 font=('Helvetica', 14, 'bold')).pack(pady=(0, 10))
        
        ttk.Label(main_frame, text="Versi 1.0").pack(pady=(0, 20))
        
        # Logo/icon placeholder
        logo_frame = ttk.Frame(main_frame)
        logo_frame.pack(pady=(0, 20))
        
        # Copyright info
        ttk.Label(main_frame, text="Hak Cipta © 2023", 
                 font=('Helvetica', 10)).pack(pady=(0, 5))
        
        ttk.Label(main_frame, text="Giraldi P.Y", 
                 font=('Helvetica', 10, 'bold')).pack(pady=(0, 5))
        
        # Developer info
        ttk.Label(main_frame, text="Dikembangkan oleh:", 
                 font=('Helvetica', 9)).pack(pady=(10, 0))
        
        ttk.Label(main_frame, text="Tim BlossomBiz", 
                 font=('Helvetica', 9)).pack()
        
        # Close button
        ttk.Button(main_frame, text="Tutup", 
                  command=self.window.destroy).pack(pady=(20, 0))
        
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
        self.master.geometry("1200x700")
        self.master.minsize(1000, 600)
        
        # Style dan tema
        self.style = Style("flatly")
        self.style.configure("TFrame", background=self.style.colors.light)
        self.style.configure("TLabel", background=self.style.colors.light)
        
        self.data = self.load_data(json_file)
        self.filtered_data = self.data.copy()
        self.current_process = None
        self.cap = None
        self.video_thread = None
        self.running = False
        
        self.create_widgets()
        self.create_menu()  # Panggil create_menu di sini
        self.populate_list()
        
        # Bind resize event
        self.master.bind("<Configure>", self.on_window_resize)
        
    def load_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel (list of CCTV)
        self.left_panel = ttk.Frame(self.main_frame, width=400)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))
        self.left_panel.pack_propagate(False)
        
        # Search box
        self.search_frame = ttk.Frame(self.left_panel)
        self.search_frame.pack(fill="x", pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_list)
        
        ttk.Label(self.search_frame, text="Cari CCTV:").pack(side="left")
        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # List container with scrollbar
        self.list_container = ttk.Frame(self.left_panel)
        self.list_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.list_container)
        self.scrollbar = ttk.Scrollbar(self.list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Right panel (video display)
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # Video frame
        self.video_frame = ttk.Frame(self.right_panel)
        self.video_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.video_label = ttk.Label(self.video_frame, text="Pilih CCTV untuk menampilkan video", 
                                   anchor="center", justify="center")
        self.video_label.pack(fill="both", expand=True)
        
        # Canvas untuk menampilkan video
        self.video_canvas = tk.Canvas(self.video_frame, bg='black')
        self.video_canvas.pack(fill="both", expand=True)
        
        # Control buttons
        self.control_frame = ttk.Frame(self.right_panel)
        self.control_frame.pack(fill="x", pady=(0, 10))
        
        self.stop_button = ttk.Button(self.control_frame, text="Stop", 
                                    command=self.stop_stream)
        self.stop_button.pack(side="left", padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Siap")
        
        self.status_bar = ttk.Label(self.right_panel, textvariable=self.status_var, 
                                   relief="sunken", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")

    def create_menu(self):
        # Create menu bar
        menubar = tk.Menu(self.master)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Keluar", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Tentang", command=self.show_about)
        menubar.add_cascade(label="Bantuan", menu=help_menu)
        
        self.master.config(menu=menubar)

    def show_about(self):
        AboutWindow(self.master)

    def populate_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_data:
            empty_label = ttk.Label(self.scrollable_frame, text="Tidak ada CCTV yang ditemukan")
            empty_label.pack(pady=10)
            return
            
        for item in self.filtered_data:
            frame = ttk.Frame(self.scrollable_frame)
            frame.pack(fill="x", pady=2, padx=5)
            
            label = ttk.Label(frame, text=item["lokasi"], width=40, anchor="w")
            label.pack(side="left", fill="x", expand=True)
            
            btn = ttk.Button(frame, text="Lihat", 
                           command=lambda link=item["link"], lokasi=item["lokasi"]: 
                           self.play_stream(link, lokasi))
            btn.pack(side="right")

    def filter_list(self, *args):
        search = self.search_var.get().lower()
        self.filtered_data = [item for item in self.data if search in item["lokasi"].lower()]
        self.populate_list()

    def play_stream(self, url, lokasi):
        self.stop_stream()  # Stop stream sebelumnya jika ada
        
        self.status_var.set(f"Memuat CCTV: {lokasi}")
        self.master.update()
        
        self.running = True
        self.video_thread = threading.Thread(target=self._video_stream_thread, args=(url, lokasi), daemon=True)
        self.video_thread.start()

    def _video_stream_thread(self, url, lokasi):
        try:
            # Gunakan OpenCV untuk menangkap stream
            self.cap = cv2.VideoCapture(url)
            
            if not self.cap.isOpened():
                self.status_var.set(f"Gagal membuka stream: {lokasi}")
                return
                
            self.status_var.set(f"Sedang menampilkan: {lokasi}")
            
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
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update gambar di canvas
                self.video_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.video_canvas.image = imgtk
                
                # Delay untuk mengurangi beban CPU
                cv2.waitKey(30)
                
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Gagal memutar stream:\n{str(e)}")
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
        
        # Clear video canvas
        self.video_canvas.delete("all")
        self.video_canvas.create_text(
            self.video_canvas.winfo_width()//2, 
            self.video_canvas.winfo_height()//2,
            text="Pilih CCTV untuk menampilkan video",
            fill="white",
            font=('Helvetica', 12)
        )
        self.status_var.set("Siap")

    def on_window_resize(self, event):
        # Adjust layout on window resize
        if event.widget == self.master:
            new_width = self.master.winfo_width()
            if new_width < 1000:
                self.left_panel.config(width=300)
            else:
                self.left_panel.config(width=400)

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