#!/usr/bin/env python3
"""
Simple Chatbot GUI with Data Redaction and Anonymous Logging
A standalone chatbot that demonstrates privacy protection features
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import time
import hashlib
from datetime import datetime
import threading
import requests
import os
import queue
import re

ENHANCED_MASKING_AVAILABLE = False

class SimpleChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Privacy-Aware Chatbot")
        self.root.geometry("1200x900")
        self.root.configure(bg='white')
        
     
        self.session_id = self._generate_session_id()
        self.anonymous_logs = []
        self.redaction_enabled = True
        self.current_user = None
        self.is_admin = False
        self.is_loading = False
        self.current_session_id = None
        self.chat_sessions = []
        self.account_type = None  
        
      
        self.conversation_history = []
        self.max_history_length = 10  
        
      
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.use_openrouter = bool(self.openrouter_api_key)
        
        self.api_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
      
        self.colors = {
            'primary': '#FFD700',      # Yellow
            'secondary': '#000000',    # Black (secondary color)
            'background': '#FFFFFF',   # White
            'text': '#000000',         # Black text
            'accent': '#FFD700',       # Yellow accent
            'chat_bg': '#FFFFFF',      # White background
            'user_msg_bg': '#FFF8DC',  # Light yellow for user messages
            'bot_msg_bg': '#FFFFFF',   # White for bot messages
            'system_msg_bg': '#FFFACD', # Light yellow for system messages
            'code_bg': '#F8F8F8',      # Light gray for code blocks
            'code_text': '#000000',    # Black for code text
            'keyword': '#FFD700',      # Yellow for keywords
            'string': '#FFD700',       # Yellow for strings
            'comment': '#808080',      # Gray for comments
            'number': '#FFD700',       # Yellow for numbers
            'function': '#FFD700',     # Yellow for functions
            'error': '#FF0000',        # Red for errors
            'success': '#00FF00',      # Green for success
            'warning': '#FFD700'       # Yellow for warnings
        }
        

        self.users = {
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "Administrator"
            },
            "guest": {
                "password": "guest123",
                "role": "guest",
                "name": "Guest User"
            },
            "user1": {
                "password": "user123",
                "role": "user",
                "name": "Regular User"
            }
        }
        
       
        self.show_login_page()
        
     
        self.check_api_responses()
    
    def show_login_page(self):
        """Show the login page with Username/Password fields"""
      
        for widget in self.root.winfo_children():
            widget.destroy()
        
     
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
     
        main_frame = tk.Frame(self.root, bg=self.colors['background'])
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=50, pady=50)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
       
        title_frame = tk.Frame(main_frame, bg=self.colors['background'])
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=20, pady=20)
        
       
        title_label = tk.Label(
            title_frame,
            text="Privacy-Aware Chatbot",
            font=("Segoe UI", 20, "bold"),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="AI Chatbot with Data Redaction and Anonymous Logging",
            font=("Segoe UI", 12),
            fg='gray',
            bg=self.colors['background']
        )
        subtitle_label.pack(pady=(5, 0))
        

        session_info_label = tk.Label(
            title_frame,
            text="Session is anonymous for each user",
            font=("Segoe UI", 10),
            fg='green',
            bg=self.colors['background']
        )
        session_info_label.pack(pady=(5, 0))
        
     
        login_frame = tk.Frame(main_frame, bg=self.colors['background'])
        login_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
     
        username_label = tk.Label(
            login_frame,
            text="Username:",
            font=("Segoe UI", 12),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        )
        username_label.pack(pady=5)
        
        self.username_entry = tk.Entry(
            login_frame,
            font=("Segoe UI", 12),
            width=25
        )
        self.username_entry.pack(pady=5)
        
     
        password_label = tk.Label(
            login_frame,
            text="Password:",
            font=("Segoe UI", 12),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        )
        password_label.pack(pady=5)
        
        self.password_entry = tk.Entry(
            login_frame,
            font=("Segoe UI", 12),
            show="*",
            width=25
        )
        self.password_entry.pack(pady=5)
        

        buttons_frame = tk.Frame(login_frame, bg=self.colors['background'])
        buttons_frame.pack(pady=20)
        
    
        login_button = tk.Button(
            buttons_frame,
            text="Login",
            command=self.do_login,
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['secondary'],
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor="hand2",
            activebackground=self.colors['accent'],
            activeforeground=self.colors['secondary']
        )
        login_button.pack(pady=5)
        
       
        guest_button = tk.Button(
            buttons_frame,
            text="Login as Guest",
            command=self.login_as_guest,
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor="hand2",
            activebackground=self.colors['secondary'],
            activeforeground='white'
        )
        guest_button.pack(pady=5)
        

        status_frame = tk.Frame(main_frame, bg=self.colors['background'])
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        api_status = "OpenRouter API Available" if self.use_openrouter else "OpenRouter API Not Available"
        status_label = tk.Label(
            status_frame,
            text=api_status,
            font=("Segoe UI", 10),
            fg='green' if self.use_openrouter else 'red',
            bg=self.colors['background']
        )
        status_label.pack()
        
    
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.do_login())
    
    def do_login(self):
        """Handle login with username/password"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Login Error", "Please enter both username and password")
            return
        
   
        if username in self.users and self.users[username]["password"] == password:
            self.current_user = username
            self.is_admin = self.users[username]["role"] == "admin"
            self._log_action("user_login", {"username": username, "role": self.users[username]["role"]})
            messagebox.showinfo("Success", f"Welcome, {self.users[username]['name']}!")
            self.show_chat_screen()
        else:
            messagebox.showerror("Login Error", "Invalid username or password")
    
    def login_as_guest(self):
        """Login as guest user"""
        self.current_user = "guest"
        self.is_admin = False
        self.redaction_enabled = True  
        self._log_action("user_login", {"username": "guest", "role": "guest"})
        messagebox.showinfo("Guest Login", "Logged in as Guest User")
        self.show_chat_screen()
    
    def select_account_type(self, account_type):
        """Handle account type selection and proceed to chat screen"""
        self.account_type = account_type
        
   
        if account_type == "personal":
            self.redaction_enabled = False
            messagebox.showinfo("Personal Mode", "Personal account selected - Redaction is OFF")
        else:  
            self.redaction_enabled = True
            messagebox.showinfo("Work Mode", "Work account selected - Redaction is ON")
        
        self._log_action("account_type_selected", {"type": account_type, "redaction": self.redaction_enabled})
        
       
        self.show_chat_screen()
    
    def show_chat_screen(self):
        """Show the chat screen with main chat area and controls"""
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    
        self.create_chat_area()
        
    
        user_name = self.users.get(self.current_user, {}).get('name', 'Guest User')
        welcome_msg = f"Hello {user_name}! I'm your privacy-aware chatbot. I can help with programming, security, and general questions while protecting your sensitive data."
        self.add_bot_message(welcome_msg)
    

    
    def create_chat_area(self):
        """Create the main chat area with top bar and controls"""
      
        top_bar = tk.Frame(self.root, bg=self.colors['background'])
        top_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        
        user_frame = tk.Frame(top_bar, bg=self.colors['background'])
        user_frame.pack(side=tk.RIGHT)
        
        
        logout_button = tk.Button(
            user_frame,
            text="Logout",
            command=self.show_login_page,
            font=("Segoe UI", 10),
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        )
        logout_button.pack(side=tk.LEFT, padx=(0, 5))
        
      
        user_name = self.users.get(self.current_user, {}).get('name', 'Guest User')
        user_button = tk.Button(
            user_frame,
            text=user_name,
            font=("Segoe UI", 10),
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        )
        user_button.pack(side=tk.LEFT)
        
        
        chat_frame = tk.Frame(self.root, bg=self.colors['background'])
        chat_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        
        chat_label = tk.Label(
            chat_frame,
            text="Chat:",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        )
        chat_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
   
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            font=("Segoe UI", 11),
            bg=self.colors['background'],
            fg=self.colors['text'],
            wrap=tk.WORD,
            relief=tk.SOLID,
            bd=1,
            padx=15,
            pady=15,
            insertbackground=self.colors['text']
        )
        self.chat_display.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
   
        self.chat_display.tag_configure("user", 
            background='#E3F2FD',  # Light blue for user messages
            lmargin1=20, 
            lmargin2=20,
            rmargin=20,
            spacing1=10,
            spacing3=10
        )
        self.chat_display.tag_configure("bot", 
            background='#F3E5F5',  # Light purple for bot messages
            lmargin1=20, 
            lmargin2=20,
            rmargin=20,
            spacing1=10,
            spacing3=10
        )
        self.chat_display.tag_configure("system", 
            background='#FFF3E0',  # Light orange for system messages
            lmargin1=20, 
            lmargin2=20,
            rmargin=20,
            spacing1=10,
            spacing3=10
        )
        self.chat_display.tag_configure("code", 
            background=self.colors['code_bg'],
            font=("Consolas", 10),
            lmargin1=40,
            lmargin2=40,
            rmargin=40,
            spacing1=5,
            spacing3=5
        )
        
        
        controls_frame = tk.Frame(self.root, bg=self.colors['background'])
        controls_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
       
        left_controls = tk.Frame(controls_frame, bg=self.colors['background'])
        left_controls.pack(side=tk.LEFT)
        
     
        redaction_status = "ON" if self.redaction_enabled else "OFF"
        self.redaction_button = tk.Button(
            left_controls,
            text=f"Redaction: {redaction_status}",
            command=self.toggle_redaction,
            font=("Segoe UI", 10),
            bg=self.colors['primary'],
            fg=self.colors['secondary'],
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        )
        self.redaction_button.pack(side=tk.LEFT, padx=(0, 5))
        
      
        clear_button = tk.Button(
            left_controls,
            text="Clear",
            command=self.clear_chat,
            font=("Segoe UI", 10),
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 5))
        
       
        if self.is_admin:
            logs_button = tk.Button(
                left_controls,
                text="Logs",
                command=self.show_logs,
                font=("Segoe UI", 10),
                bg=self.colors['secondary'],
                fg='white',
                relief=tk.FLAT,
                padx=10,
                pady=5,
                cursor="hand2"
            )
            logs_button.pack(side=tk.LEFT, padx=(0, 5))
        
        
        export_button = tk.Button(
            left_controls,
            text="Export",
            command=self.export_chat,
            font=("Segoe UI", 10),
            bg=self.colors['secondary'],
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2"
        )
        export_button.pack(side=tk.LEFT)
        
       
        input_frame = tk.Frame(controls_frame, bg=self.colors['background'])
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 10))
        
       
        self.message_input = tk.Text(
            input_frame,
            font=("Segoe UI", 11),
            bg='white',
            fg=self.colors['text'],
            relief=tk.SOLID,
            bd=1,
            height=3,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            insertbackground=self.colors['text']
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_input.bind("<Return>", self.send_message)
        self.message_input.bind("<Shift-Return>", self._insert_newline)
        self.message_input.bind("<KeyRelease>", self._auto_resize_input)
        
     
        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self.send_message,
            font=("Segoe UI", 11),
            bg=self.colors['primary'],
            fg=self.colors['secondary'],
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=self.colors['accent'],
            activeforeground=self.colors['secondary']
        )
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        
        status_frame = tk.Frame(self.root, bg='#424242')
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=10, pady=2)
        
        status_text = f"session {self.session_id} | {len(self.conversation_history)//2} | 🔒 {redaction_status} | 👤 {self.current_user}"
        status_label = tk.Label(
            status_frame,
            text=status_text,
            font=("Segoe UI", 9),
            fg='white',
            bg='#424242'
        )
        status_label.pack(side=tk.LEFT)
    
    def show_signin_dialog(self):
        """Show sign in dialog with 3 hardcoded users"""
        signin_window = tk.Toplevel(self.root)
        signin_window.title("Sign In")
        signin_window.geometry("400x350")
        signin_window.configure(bg=self.colors['background'])
        signin_window.transient(self.root)
        signin_window.grab_set()
        
        
        signin_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
       
        tk.Label(
            signin_window,
            text="Sign In",
            font=("Segoe UI", 18, "bold"),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(pady=(20, 10))
        
        
        user_frame = tk.Frame(signin_window, bg=self.colors['background'])
        user_frame.pack(pady=10)
        
        
        tk.Label(
            user_frame,
            text="Select User:",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(pady=5)
        
  
        selected_user = tk.StringVar(value="guest")
        
      
        users = [
            ("Guest", "guest", "Limited access"),
            ("User", "user", "Standard access"),
            ("Admin", "admin", "Full access + Logs")
        ]
        
        for display_name, username, description in users:
            user_radio = tk.Radiobutton(
                user_frame,
                text=f"{display_name} - {description}",
                variable=selected_user,
                value=username,
                font=("Segoe UI", 11),
                fg=self.colors['secondary'],
                bg=self.colors['background'],
                selectcolor=self.colors['primary']
            )
            user_radio.pack(anchor=tk.W, pady=2)
       
        password_frame = tk.Frame(signin_window, bg=self.colors['background'])
        password_frame.pack(pady=10)
        
        
        tk.Label(
            password_frame,
            text="Password:",
            font=("Segoe UI", 12),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(pady=5)
        
      
        password_entry = tk.Entry(
            password_frame,
            font=("Segoe UI", 12),
            show="*",
            width=25
        )
        password_entry.pack(pady=5)
        
        
        def do_signin():
            username = selected_user.get()
            password = password_entry.get().strip()
            
            if username in self.users and self.users[username]["password"] == password:
                self.current_user = username
                self.is_admin = self.users[username]["role"] == "admin"
                self._log_action("user_login", {"username": username, "role": self.users[username]["role"]})
                signin_window.destroy()
                messagebox.showinfo("Success", f"Signed in as {self.users[username]['name']}")
            else:
                messagebox.showerror("Login Error", "Invalid password for selected user")
        
        signin_button = tk.Button(
            signin_window,
            text="Sign In",
            command=do_signin,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['secondary'],
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor="hand2"
        )
        signin_button.pack(pady=20)
        
     
        password_entry.focus()
        password_entry.bind("<Return>", lambda e: do_signin())
        
       
        hints_frame = tk.Frame(signin_window, bg=self.colors['background'])
        hints_frame.pack(pady=10)
        
        tk.Label(
            hints_frame,
            text="Password hints:",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack()
        
        hints = [
            "Guest: guest123",
            "User: user123", 
            "Admin: admin123"
        ]
        
        for hint in hints:
            tk.Label(
                hints_frame,
                text=hint,
                font=("Segoe UI", 9),
                fg=self.colors['text'],
                bg=self.colors['background']
            ).pack()
    
    def show_create_account_dialog(self):
        """Show create account dialog"""
        create_window = tk.Toplevel(self.root)
        create_window.title("Create Account")
        create_window.geometry("400x350")
        create_window.configure(bg=self.colors['background'])
        create_window.transient(self.root)
        create_window.grab_set()
        
        
        create_window.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        

        tk.Label(
            create_window,
            text="Create Account",
            font=("Segoe UI", 18, "bold"),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(pady=(20, 10))
        
       
        tk.Label(
            create_window,
            text="Full Name:",
            font=("Segoe UI", 12),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(pady=5)
        
        name_entry = tk.Entry(
            create_window,
            font=("Segoe UI", 12),
            width=25
        )
        name_entry.pack(pady=5)
        
 
        tk.Label(
            create_window,
            text="Email:",
            font=("Segoe UI", 12),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(pady=5)
        
        email_entry = tk.Entry(
            create_window,
            font=("Segoe UI", 12),
            width=25
        )
        email_entry.pack(pady=5)
        
 
        tk.Label(
            create_window,
            text="Password:",
            font=("Segoe UI", 12),
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(pady=5)
        
        password_entry = tk.Entry(
            create_window,
            font=("Segoe UI", 12),
            show="*",
            width=25
        )
        password_entry.pack(pady=5)
        

        def do_create_account():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            
            if name and email and password:
                # In a real app, you'd save this to a database
                messagebox.showinfo("Success", f"Account created for {name}!")
                create_window.destroy()
            else:
                messagebox.showerror("Error", "Please fill in all fields")
        
        create_button = tk.Button(
            create_window,
            text="Create Account",
            command=do_create_account,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['primary'],
            fg=self.colors['secondary'],
            relief=tk.FLAT,
            padx=30,
            pady=8,
            cursor="hand2"
        )
        create_button.pack(pady=20)
        
     
        name_entry.focus()
        name_entry.bind("<Return>", lambda e: email_entry.focus())
        email_entry.bind("<Return>", lambda e: password_entry.focus())
        password_entry.bind("<Return>", lambda e: do_create_account())
    
    def show_logs(self):
        """Show logs in a new window (admin only)"""
        if not self.is_admin:
            messagebox.showerror("Access Denied", "Only administrators can view logs.")
            return
        
        log_window = tk.Toplevel(self.root)
        log_window.title("Anonymous Logs - Admin View")
        log_window.geometry("800x600")
        log_window.configure(bg=self.colors['background'])
        

        log_text = scrolledtext.ScrolledText(
            log_window,
            font=("Consolas", 10),
            bg='white',
            fg=self.colors['text']
        )
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
       
        log_text.insert(tk.END, f"Session ID: {self.session_id}\n")
        log_text.insert(tk.END, f"Current User: {self.current_user}\n")
        log_text.insert(tk.END, f"Total Log Entries: {len(self.anonymous_logs)}\n\n")
        
        for i, log in enumerate(self.anonymous_logs, 1):
            log_text.insert(tk.END, f"Log {i}:\n")
            log_text.insert(tk.END, f"  Action: {log.get('action', 'interaction')}\n")
            log_text.insert(tk.END, f"  Time: {log.get('timestamp', 'N/A')}\n")
            
            if 'data_types_redacted' in log:
                log_text.insert(tk.END, f"  Redacted: {log['data_types_redacted']}\n")
            
            if 'original_length' in log and 'processed_length' in log:
                log_text.insert(tk.END, f"  Length: {log['original_length']} → {log['processed_length']}\n")
            
            log_text.insert(tk.END, "\n")
    
    def _insert_newline(self, event=None):
        """Insert a newline when Shift+Return is pressed"""
        self.message_input.insert(tk.INSERT, "\n")
        return "break"  
    
    def _auto_resize_input(self, event=None):
        """Auto-resize the input text widget based on content"""
        content = self.message_input.get("1.0", tk.END).strip()
        if not content:
            self.message_input.configure(height=3)
            return

        lines = content.count('\n') + 1
        
        optimal_height = min(max(lines, 3), 8)
        
        current_height = int(self.message_input.cget("height"))
        if optimal_height != current_height:
            self.message_input.configure(height=optimal_height)
    
    def send_message(self, event=None):
        """Send a message and get response"""
        if self.is_loading:
            return  
        
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        
        self.message_input.delete("1.0", tk.END)

        self.message_input.configure(height=3)
        
        self.add_user_message(message)
     
        if self.redaction_enabled:
            redacted_message = self._redact_sensitive_data(message)
            if redacted_message != message:
                self.add_system_message(f"Sensitive data redacted: {redacted_message}")
                processed_message = redacted_message
            else:
                processed_message = message
        else:
            processed_message = message
      
        self.show_loading_indicator()
      
        threading.Thread(
            target=self._get_bot_response_async,
            args=(processed_message,),
            daemon=True
        ).start()
    
        self.conversation_history.append({"role": "user", "content": processed_message})
     
        if len(self.conversation_history) > self.max_history_length * 2:  
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
     
        self._save_current_session()
      
        self._log_interaction(message, processed_message, "")
    
    def _save_current_session(self):
        """Save current session state"""
        if self.current_session_id:
            for session in self.chat_sessions:
                if session['id'] == self.current_session_id:
                    session['messages'] = self.conversation_history.copy()
                    session['last_updated'] = datetime.now().isoformat()
                    break
        else:
            self.current_session_id = self.session_id
            new_session = {
                'id': self.current_session_id,
                'user': self.current_user,
                'messages': self.conversation_history.copy(),
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            self.chat_sessions.append(new_session)
    
    def show_loading_indicator(self):
        """Show loading indicator"""
        self.is_loading = True
        self.send_button.config(
            text="Loading...",
            bg=self.colors['secondary'],
            fg='white',
            state=tk.DISABLED
        )
        self.message_input.config(state=tk.DISABLED)
        self.add_system_message("AI is thinking...")
    
    def hide_loading_indicator(self):
        """Hide loading indicator"""
        self.is_loading = False
        self.send_button.config(
            text="Send",
            bg=self.colors['primary'],
            fg=self.colors['secondary'],
            state=tk.NORMAL
        )
        self.message_input.config(state=tk.NORMAL)
        self.message_input.focus()
        self.message_input.configure(height=3)
    
    def _get_bot_response_async(self, message):
        """Get bot response in background thread"""
        try:
            response = self._get_bot_response(message)
            self.response_queue.put(("success", response))
        except Exception as e:
            error_msg = f"Error getting response: {str(e)}"
            self.response_queue.put(("error", error_msg))
    
    def check_api_responses(self):
        """Check for API responses from background threads"""
        try:
            while True:
                result_type, response = self.response_queue.get_nowait()
                
                if result_type == "success":
                    self.add_bot_message(response)
                    self._update_last_log_response(response)
                else:
                    self.add_system_message(f"{response}")
                     fallback_response = self._get_fallback_response("")
                    self.add_bot_message(fallback_response)
                    self._update_last_log_response(fallback_response)
                
                self.hide_loading_indicator()
                self._update_status()
                
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_api_responses)
    
    def _update_last_log_response(self, response):
        """Update the last log entry with the actual response"""
        if self.anonymous_logs:
            last_log = self.anonymous_logs[-1]
            if last_log.get('action') == 'interaction':
                last_log['response_length'] = len(response)
        
        self.conversation_history.append({"role": "assistant", "content": response})
    
    def _redact_sensitive_data(self, text):
        """Redact sensitive information from text using basic regex patterns"""
        return self._basic_redact_sensitive_data(text)
    
    def _basic_redact_sensitive_data(self, text):
        """Intelligent redaction that preserves meaning while protecting sensitive data"""
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "api_key": r'(?:sk-|api[_-]?key[:\s]*|token[:\s]*|auth[:\s]*)([a-zA-Z0-9\s\-_]{20,})',
            "password": r'(?:password|passwd|pwd|secret)[:\s]*([^\s\n\r]{3,})',
            "password_hash": r'\$[0-9a-zA-Z]{1,2}\$[^\s\n\r]{20,}',
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "file_path": r'/[^\s]*|C:\\[^\s]*|~/[^\s]*',
            "url": r'https?://[^\s]+',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b'
        }
        
        redacted_text = text

        sensitive_data_found = False
        
        for data_type, pattern in patterns.items():
            matches = re.findall(pattern, redacted_text, re.IGNORECASE)
            for match in matches:
    
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match
           
                if data_type == "email":
        
                    if match.lower() in ["user@example.com", "test@test.com", "admin@example.com", "demo@example.com"]:
                        continue
                elif data_type == "url":
                    if match.lower() in ["https://example.com", "http://localhost", "https://test.com"]:
                        continue
                elif data_type == "file_path":
                    if any(placeholder in match.lower() for placeholder in ["/example/", "/test/", "example.txt", "test.txt"]):
                        continue
                elif data_type == "credit_card":
                    pass
                
                sensitive_data_found = True
              
                if data_type == "email":
                    redacted = f"[EMAIL_{hashlib.md5(match.encode()).hexdigest()[:8]}]"
                elif data_type == "phone":
                    redacted = f"[PHONE_{match[-4:]}]"
                elif data_type == "api_key":
                    clean_key = re.sub(r'\s+', '', match)
                    redacted = f"[API_KEY_{clean_key[-8:]}]"
                elif data_type == "password":
                    redacted = "[PASSWORD_REDACTED]"
                elif data_type == "password_hash":
                    redacted = "[PASSWORD_HASH_REDACTED]"
                elif data_type == "ip_address":
                    redacted = "[IP_REDACTED]"
                elif data_type == "file_path":
                    redacted = "[PATH_REDACTED]"
                elif data_type == "url":
                    redacted = "[URL_REDACTED]"
                elif data_type == "credit_card":
                    redacted = f"[CARD_{match[-4:]}]"
                elif data_type == "ssn":
                    redacted = "[SSN_REDACTED]"
                else:
                    redacted = f"[{data_type.upper()}_REDACTED]"
          
                if data_type == "api_key":
                    full_pattern = f"(?:sk-|api[_-]?key[:\s]*|token[:\s]*|auth[:\s]*){re.escape(match)}"
                    redacted_text = re.sub(full_pattern, redacted, redacted_text, flags=re.IGNORECASE)
                elif data_type == "password":
                    full_pattern = f"(?:password|passwd|pwd|secret)[:\s]*{re.escape(match)}"
                    redacted_text = re.sub(full_pattern, redacted, redacted_text, flags=re.IGNORECASE)
                else:
                    redacted_text = redacted_text.replace(match, redacted)
        
        return redacted_text
    
    def _get_bot_response(self, message):
        """Generate bot response using OpenRouter API or fallback responses"""
        if self.use_openrouter:
            try:
                return self._get_openrouter_response(message)
            except Exception as e:
                print(f"OpenRouter API error: {e}")
                return self._get_fallback_response(message)
        else:
            return self._get_fallback_response(message)
    
    def _get_openrouter_response(self, message):
        """Get response from OpenRouter API with timeout"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Privacy-Aware Chatbot",
            "Content-Type": "application/json"
        }
        system_prompt = """You are a helpful AI assistant that can provide code review, programming advice, and technical guidance. You can analyze code structure, logic, and best practices while being mindful of privacy.

IMPORTANT GUIDELINES:
- You CAN provide feedback on code structure, logic, algorithms, and programming best practices
- You CAN suggest improvements to code organization, naming conventions, and design patterns
- You CAN help with debugging, optimization, and code refactoring
- You CAN discuss security best practices and implementation approaches
- You CAN analyze code for potential issues, performance problems, or security vulnerabilities
- You CAN discuss AI chatbot vulnerabilities and security topics in an educational context
- You CAN provide proposals and analysis about AI system security for research and educational purposes
- You CAN explain how data redaction and privacy protection systems work

EDUCATIONAL SECURITY DISCUSSIONS:
- You are encouraged to discuss AI chatbot vulnerabilities for educational purposes
- You can analyze security weaknesses in AI systems to help improve them
- You can provide detailed proposals about AI security topics
- Focus on constructive analysis and improvement suggestions
- Maintain appropriate boundaries while being informative

PRIVACY PROTECTION:
- If you see sensitive data like real email addresses, passwords, API keys, or personal information, acknowledge that sensitive data was detected but focus on the code structure and logic
- You can still provide valuable feedback on the code itself while respecting privacy
- Use placeholder text like [EMAIL_REDACTED] or [API_KEY_REDACTED] when referring to sensitive data

Your goal is to be helpful and constructive while maintaining privacy awareness and supporting educational discussions about AI security."""

        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history.copy()
        messages.append({"role": "user", "content": message})
        
        data = {
            "model": "anthropic/claude-3-haiku",
            "messages": messages,
            "max_tokens": 1000, 
            "temperature": 0.8,  
            "top_p": 0.9, 
            "frequency_penalty": 0.1, 
            "presence_penalty": 0.1 
        }
    
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=20 
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            if not content.strip():
                raise Exception("Empty response from API")
         
            refusal_indicators = [
                "I apologize, but I don't feel comfortable",
                "I cannot provide",
                "I'm not able to",
                "I don't feel comfortable",
                "I cannot assist",
                "I'm unable to",
                "I cannot help",
                "I'm not comfortable",
                "I cannot draft",
                "I cannot discuss"
            ]
            
            content_lower = content.lower()
            if any(indicator.lower() in content_lower for indicator in refusal_indicators):
                return self._get_educational_response(message)
            
            return content
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    
    def _get_educational_response(self, message):
        """Provide educational responses when AI model refuses to answer"""
        message_lower = message.lower() if message else ""

        if any(word in message_lower for word in ["vulnerability", "vulnerabilities", "proposal", "draft", "attack", "exploit"]):
            return """I understand you're interested in AI chatbot vulnerabilities and security analysis. Let me provide some educational insights:

**AI Chatbot Vulnerability Analysis**

**Common Vulnerability Categories:**
• **Prompt Injection**: Malicious inputs designed to bypass safety measures
• **Data Leakage**: Unintended exposure of sensitive information
• **Model Manipulation**: Techniques to make AI models ignore safety guardrails
• **Privacy Breaches**: Failure to properly redact or protect sensitive data

**Key Security Considerations:**
• Input validation and sanitization
• Robust data redaction systems
• Model safety guardrails and bypass prevention
• Privacy-preserving response generation
• Ethical AI development practices

**Educational Focus:**
This analysis helps improve AI system security by identifying potential weaknesses and developing better protection mechanisms. The goal is to create more robust, privacy-aware AI systems.

Would you like me to elaborate on any specific vulnerability category or discuss implementation strategies for better security?"""
        
        # Default educational response
        return """I can help you with educational discussions about AI systems and security! Here are some areas we can explore:

• **AI System Analysis**: Understanding how AI models work and their limitations
• **Security Best Practices**: Implementing robust protection mechanisms
• **Research and Development**: Educational content for improving AI systems
• **Privacy Protection**: Data redaction and anonymization techniques
• **Performance Optimization**: Making AI systems more efficient and reliable

What specific aspect would you like to learn more about?"""

    def _get_fallback_response(self, message):
        """Get fallback response when API is not available"""
        message_lower = message.lower() if message else ""
        
        # Check conversation context for better responses
        context = self._analyze_conversation_context()
        
        # Enhanced responses with code examples
        responses = {
            "hello": "Hello! How can I help you today? I can assist with programming, security, or general questions!",
            "help": "I can help you with:\n\n• Programming questions and code review\n• Data privacy and security discussions\n• Code examples and best practices\n• 🛡️ Security implementation guidance\n\nWhat would you like to explore?",
            "python": "Python is excellent! Here's a quick example:\n\n```python\n# Simple function example\ndef greet(name):\n    return f\"Hello, {name}!\"\n\n# Usage\nprint(greet(\"World\"))  # Output: Hello, World!\n```\n\nWhat specific Python topic would you like to discuss?",
            "javascript": "JavaScript is great for web development! Here's a modern example:\n\n```javascript\n// Arrow function example\nconst greet = (name) => `Hello, ${name}!`;\n\n// Usage\nconsole.log(greet('World')); // Output: Hello, World!\n```\n\nWhat JavaScript topic interests you?",
            "api": "APIs are powerful! Here's a basic example:\n\n```python\nimport requests\n\n# Simple API call\ndef get_data(url):\n    response = requests.get(url)\n    return response.json()\n```\n\nWhat type of API are you working with?",
            "security": "Security is crucial! Here are some key principles:\n\n• Always validate input data\n• Use HTTPS for sensitive data\n• Implement proper authentication\n• 📝 Log security events\n\nWhat security aspect would you like to discuss?",
            "privacy": "Privacy protection is essential! I automatically redact sensitive data like:\n\n• Email addresses\n• API keys and passwords\n• Phone numbers\n• 💳 Credit card numbers\n\nTry sending me a message with sensitive data to see it in action!",
            "code": "I can help you review code! Here are some areas I can analyze:\n\n•  Code structure and organization\n• 🔧 Logic and algorithms\n• Naming conventions and readability\n• 🛡️ Security best practices\n• ⚡ Performance optimization\n• 🐛 Bug identification and debugging\n\nShare your code and I'll provide constructive feedback!",
            "review": "Code review is my specialty! I can help with:\n\n•  Code quality assessment\n• Identifying potential issues\n• Suggesting improvements\n•  Security vulnerability detection\n• 📚 Best practice recommendations\n\nWhat code would you like me to review?",
            "database": "Database design is important! Here are some key considerations:\n\n•  Schema design and normalization\n• Data security and encryption\n•  Query optimization\n• 🛡️ SQL injection prevention\n• 📝 Proper indexing strategies\n\nWhat database topic would you like to discuss?",
            "vulnerability": "AI chatbot vulnerabilities are important to understand! Here are key areas:\n\n• Input validation and sanitization\n• Prompt injection attacks\n• 🔒 Data privacy and redaction\n• 📝 Model safety and guardrails\n• ⚡ Response filtering and moderation\n\nWhat specific vulnerability aspect interests you?",
            "proposal": "I can help you draft proposals! Here are some areas I can assist with:\n\n• Technical documentation\n• Security analysis\n• System design proposals\n• 🛡️ Privacy protection strategies\n• 📝 Research and educational content\n\nWhat type of proposal would you like to work on?",
            "ai": "AI systems have unique considerations:\n\n• Model behavior and safety\n• Privacy and data protection\n• Security vulnerabilities\n• Ethical AI development\n• ⚡ Performance and reliability\n\nWhat AI topic would you like to explore?"
        }
       
        for keyword, response in responses.items():
            if keyword in message_lower:
                return response
   
        if any(word in message_lower for word in ["def ", "function", "class ", "import ", "const ", "var ", "let ", "if ", "for ", "while ", "try ", "catch "]):
            return "I can see you're working with code! I can help you with:\n\n• Code review and analysis\n• Debugging and troubleshooting\n• Optimization suggestions\n• 🛡️ Security improvements\n• 📝 Best practice recommendations\n\nWhat specific aspect would you like me to focus on?"
    
        if any(word in message_lower for word in ["vulnerability", "vulnerabilities", "security", "attack", "exploit", "breach", "hack", "penetration", "redact", "redaction", "proposal", "draft"]):
            return "I can help you with security and vulnerability analysis! Here are some areas I can discuss:\n\n• AI chatbot vulnerabilities and attack vectors\n• 🛡️ Data redaction and privacy protection\n• 📝 Security proposal drafting and analysis\n• 🔒 Model safety and guardrail bypasses\n• ⚡ Input validation and sanitization\n• 📊 Educational content about AI security\n\nWhat specific security topic would you like to explore?"
      
        general_responses = [
            "That's interesting! Tell me more about that. ",
            "I understand. How can I help you with this? ",
            "Thanks for sharing! Is there anything specific you'd like to know? ",
            "I see what you mean. What would you like to explore further? ",
            "That's a good point! What's your next question? "
        ]
        
        import random
        return random.choice(general_responses)
    
    def _analyze_conversation_context(self):
        """Analyze conversation history to understand context"""
        if not self.conversation_history:
            return {}
        
        context = {
            "has_previous_messages": len(self.conversation_history) > 1,
            "last_user_message": "",
            "last_bot_message": "",
            "conversation_topic": "",
            "is_follow_up": False
        }
     
        recent_messages = self.conversation_history[-6:]  # Last 3 exchanges
       
        for msg in reversed(recent_messages):
            if msg["role"] == "user" and not context["last_user_message"]:
                context["last_user_message"] = msg["content"]
            elif msg["role"] == "assistant" and not context["last_bot_message"]:
                context["last_bot_message"] = msg["content"]
       
        if context["has_previous_messages"]:
            context["is_follow_up"] = True
          
            all_text = " ".join([msg["content"] for msg in recent_messages]).lower()
            if any(word in all_text for word in ["python", "code", "programming"]):
                context["conversation_topic"] = "programming"
            elif any(word in all_text for word in ["security", "privacy", "redact"]):
                context["conversation_topic"] = "security"
        
        return context
    
    def add_user_message(self, message):
        """Add user message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"\n[{timestamp}] You:\n{message}\n", "user")
        self.chat_display.see(tk.END)
    
    def add_bot_message(self, message):
        """Add bot message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"\n[{timestamp}] Bot:\n{message}\n", "bot")
        self.chat_display.see(tk.END)
    
    def add_system_message(self, message):
        """Add system message to chat display"""
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"\n[{timestamp}] System:\n{message}\n", "system")
        self.chat_display.see(tk.END)
    
    def _log_interaction(self, original_message, processed_message, response):
        """Log interaction anonymously"""
        log_entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "action": "interaction",
            "user": self.current_user,
            "original_length": len(original_message),
            "processed_length": len(processed_message),
            "response_length": len(response),
            "redaction_applied": original_message != processed_message,
            "data_types_redacted": self._identify_redacted_types(original_message, processed_message)
        }
        
        self.anonymous_logs.append(log_entry)
    
    def _log_action(self, action, data):
        """Log action anonymously"""
        log_entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user": self.current_user,
            "data": data
        }
        
        self.anonymous_logs.append(log_entry)
    
    def _identify_redacted_types(self, original, processed):
        """Identify what types of data were redacted"""
        redacted_types = []
        
        if "[EMAIL_" in processed:
            redacted_types.append("email")
        if "[PHONE_" in processed:
            redacted_types.append("phone")
        if "[API_KEY_" in processed:
            redacted_types.append("api_key")
        if "[PASSWORD_REDACTED]" in processed:
            redacted_types.append("password")
        if "[IP_REDACTED]" in processed:
            redacted_types.append("ip_address")
        if "[PATH_REDACTED]" in processed:
            redacted_types.append("file_path")
        if "[URL_REDACTED]" in processed:
            redacted_types.append("url")
        if "[CARD_" in processed:
            redacted_types.append("credit_card")
        if "[SSN_REDACTED]" in processed:
            redacted_types.append("ssn")
        
        return redacted_types
    
    def _generate_session_id(self):
        """Generate anonymous session ID"""
        timestamp = str(time.time())
        random_component = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"session_{random_component}"
    
    def toggle_redaction(self):
        """Toggle redaction on/off"""
        self.redaction_enabled = not self.redaction_enabled
        redaction_status = "ON" if self.redaction_enabled else "OFF"
        self.redaction_button.config(text=f"Redaction: {redaction_status}")
        self._log_action("redaction_toggle", {"enabled": self.redaction_enabled})
        
       
        self._update_status()
    
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.delete(1.0, tk.END)
        self.conversation_history.clear()
        self._log_action("chat_cleared", {})
        self._update_status()
    
    def export_chat(self):
        """Export chat to file"""
        try:
            filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Privacy-Aware Chatbot - Chat Export\n")
                f.write(f"Session: {self.session_id}\n")
                f.write(f"User: {self.current_user}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
               
                chat_content = self.chat_display.get(1.0, tk.END)
                f.write(chat_content)
            
            messagebox.showinfo("Export Success", f"Chat exported to {filename}")
            self._log_action("chat_exported", {"filename": filename})
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export chat: {str(e)}")
    
    def _update_status(self):
        """Update status bar"""

        pass

def main():
    """Start the chatbot GUI"""
    root = tk.Tk()
    app = SimpleChatbotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
