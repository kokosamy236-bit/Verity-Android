# -*- coding: utf-8 -*-
import os, json, math, time, threading, subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from groq import Groq

# ===================== الإعدادات والملفات =====================
CONFIG_FILE = "config.json"
TRANSPARENT_COLOR = "#ff00fe"
PET_W, PET_H = 700, 520
BLACK, WHITE = "#0a0a0a", "#ffffff"
SMILEY_YELLOW = "#ffcc00"
BLACK2 = "#15151a"

def load_api_key():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("api_key", "").strip()
        except:
            return ""
    return ""

def save_api_key(key):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"api_key": key.strip()}, f, indent=4)

# ===================== المحرك الصوتي =====================
class TTS:
    def speak(self, text):
        def _run():
            clean_text = text.replace("'", "''")
            script = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate = -1; $s.Volume = 100; $s.Speak('{clean_text}')"
            subprocess.run(["powershell", "-NoProfile", "-Command", script], creationflags=subprocess.CREATE_NO_WINDOW)
        threading.Thread(target=_run, daemon=True).start()

# ===================== العقل المدبر =====================
class AIBrain:
    def __init__(self, api_key=""):
        self.api_key = api_key
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def set_key(self, api_key):
        self.api_key = api_key
        self.client = Groq(api_key=self.api_key)

    def process(self, text):
        if not self.client or not self.api_key:
            return "يرجى إدخال مفتاح API الخاص بك من زر الإعدادات (⚙️) للبدء."
        try:
            res = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": "أنت فيرتي (Verity)، مساعد ذكي ولطيف ومرح. أجب بالعربية بأسلوب ودود ومساعد."}, {"role": "user", "content": text}],
                temperature=0.7, max_tokens=500
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            return "حدث خطأ أثناء الاتصال. تأكد من صحة مفتاح API والاتصال بالإنترنت."

# ===================== التطبيق =====================
class PetApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.root.configure(bg=TRANSPARENT_COLOR)

        self.canvas = tk.Canvas(self.root, width=PET_W, height=PET_H, bg=TRANSPARENT_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        self.saved_key = load_api_key()
        self.brain = AIBrain(self.saved_key)
        self.tts = TTS()
        self.is_processing = False
        
        self._create_ui()
        self.bubble_frame = None
        
        if not self.saved_key:
            self.show_bubble("أهلاً بك! يرجى إضافة مفتاح Groq API الخاص بك من زر الإعدادات ⚙️")
        else:
            self.show_bubble("أهلاً بك! أنا فيرتي، كيف يمكنني مساعدتك اليوم؟")
        
        self.root.after(100, self._animate)
        self.root.mainloop()

    def _create_ui(self):
        self.input_frame = tk.Frame(self.root, bg=BLACK2, bd=2, relief="solid")
        
        # زر الإعدادات لتغيير المفتاح
        tk.Button(self.input_frame, text="⚙️", command=self._prompt_api_key, bg=BLACK2, fg=WHITE, font=("Arial", 11), bd=0).pack(side="left", padx=5)
        
        self.entry = tk.Entry(self.input_frame, bg=BLACK, fg=WHITE, font=("Segoe UI", 14), insertbackground=WHITE, bd=0)
        self.entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.entry.bind("<Return>", lambda e: self._on_send())
        
        tk.Button(self.input_frame, text="😊", command=self._on_send, bg=SMILEY_YELLOW, fg=BLACK, font=("Arial", 12, "bold")).pack(side="right", padx=5)
        self.canvas.create_window(PET_W // 2, PET_H - 40, window=self.input_frame, width=550, height=50)

    def _prompt_api_key(self):
        new_key = simpledialog.askstring("إعدادات API Key", "أدخل مفتاح Groq API الخاص بك:", parent=self.root)
        if new_key:
            save_api_key(new_key)
            self.brain.set_key(new_key)
            messagebox.showinfo("تم بنجاح", "تم حفظ مفتاح API بنجاح!")
            self.show_bubble("تم تحديث مفتاح API! أنا جاهز للإجابة على أسئلتك.")

    def _on_send(self):
        text = self.entry.get().strip()
        if text and not self.is_processing:
            if not self.brain.api_key:
                self._prompt_api_key()
                return
            self.entry.delete(0, "end")
            threading.Thread(target=self._ask_ai, args=(text,), daemon=True).start()

    def _ask_ai(self, text):
        self.is_processing = True
        self.show_bubble("جاري التفكير...")
        res = self.brain.process(text)
        self.tts.speak(res)
        self.show_bubble(res)
        self.is_processing = False

    def show_bubble(self, text):
        if self.bubble_frame: self.bubble_frame.destroy()
        
        self.bubble_frame = tk.Frame(self.root, bg=BLACK2, highlightbackground=SMILEY_YELLOW, highlightthickness=2)
        
        txt = tk.Text(self.bubble_frame, bg=BLACK2, fg=WHITE, font=("Segoe UI", 15, "bold"), width=36, height=11, bd=0, wrap="word")
        txt.insert("1.0", text)
        txt.config(state="disabled")
        
        scrl = ttk.Scrollbar(self.bubble_frame, orient="vertical", command=txt.yview)
        txt.config(yscrollcommand=scrl.set)
        
        scrl.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        def _on_mousewheel(event):
            txt.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
        txt.bind("<MouseWheel>", _on_mousewheel)
        
        self.canvas.create_window(230, 180, window=self.bubble_frame, width=440, height=320)

    def _animate(self):
        self.canvas.delete("verity_element")
        cx, cy = 580, 250
        
        self.canvas.create_oval(cx-45, cy-45, cx+45, cy+45, fill=SMILEY_YELLOW, outline="black", width=2, tags="verity_element")
        self.canvas.create_oval(cx-18, cy-18, cx-8, cy-2, fill="black", tags="verity_element")
        self.canvas.create_oval(cx+8, cy-18, cx+18, cy-2, fill="black", tags="verity_element")
        self.canvas.create_arc(cx-25, cy-25, cx+25, cy+25, start=200, extent=140, style="arc", outline="black", width=3, tags="verity_element")

        self.root.after(40, self._animate)

if __name__ == "__main__":
    PetApp()