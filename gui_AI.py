import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font
import sys
import os
import math

# --- 全局配色 ---
THEME = {
    "bg_window": "#23272e",       
    "bg_panel":  "#282c34",       
    "bg_header": "#21252b",       
    
    "input_bg":    "#434c5e",     
    "input_fg":    "#ffffff",     # 默认文字颜色
    "input_err":   "#ff5555",     # 错误颜色
    
    "title_fg":    "#e5c07b",     
    "text_main":   "#abb2bf",     
    "text_dim":    "#5c6370",     
    
    "pill_off_bg": "#000000",     
    "pill_on_bg":  "#28a745",     
    "pill_text":   "#ffffff",     
    
    "border":      "#181a1f",
    
    "diff_bg":     "#8b2a2a"      # 差异高亮背景色 (红底)
}

# --- 图标设置逻辑 ---
ICON_FILE = 'svg_code_to_png.ico'

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)

def set_window_icon(window):
    try:
        icon_path = resource_path(ICON_FILE)
        window.iconbitmap(icon_path)
    except Exception:
        pass 

# --- 精确几何绘制圆角矩形 ---
def draw_rounded_rect(canvas, x, y, w, h, r, **kwargs):
    # 限制半径
    r = min(r, h/2, w/2)
    
    points = []
    # 1. 左上角 (180->270)
    for i in range(180, 270+1, 5):
        a = math.radians(i)
        points.extend([x + r + r*math.cos(a), y + r + r*math.sin(a)])
    # 2. 右上角 (270->360)
    for i in range(270, 360+1, 5):
        a = math.radians(i)
        points.extend([x + w - r + r*math.cos(a), y + r + r*math.sin(a)])
    # 3. 右下角 (0->90)
    for i in range(0, 90+1, 5):
        a = math.radians(i)
        points.extend([x + w - r + r*math.cos(a), y + h - r + r*math.sin(a)])
    # 4. 左下角 (90->180)
    for i in range(90, 180+1, 5):
        a = math.radians(i)
        points.extend([x + r + r*math.cos(a), y + h - r + r*math.sin(a)])
        
    return canvas.create_polygon(points, smooth=False, **kwargs)

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=100, height=30, corner_radius=10, bg_normal='#EBCB8B', bg_hover='#D0B075', fg_color='#2E3440', outer_bg=THEME["bg_header"], font_size=9, **kwargs):
        super().__init__(parent, width=width, height=height, bg=outer_bg, bd=0, highlightthickness=0, cursor='hand2', **kwargs)
        self.command = command
        self.bg_normal = bg_normal
        self.bg_hover = bg_hover
        self.rect_id = draw_rounded_rect(self, 2, 2, width-2, height-2, corner_radius, fill=bg_normal, outline="")
        self.text_id = self.create_text(width/2, height/2, text=text, fill=fg_color, font=('Microsoft YaHei UI', font_size, 'bold'))
        self.bind('<Enter>', lambda e: self.itemconfig(self.rect_id, fill=self.bg_hover))
        self.bind('<Leave>', lambda e: self.itemconfig(self.rect_id, fill=self.bg_normal))
        self.bind('<Button-1>', lambda e: self.command() if self.command else None)

class RoundedEntry(tk.Canvas):
    def __init__(self, parent, textvariable, width=100, height=26, bg_color=THEME["input_bg"], fg_color=THEME["input_fg"]):
        super().__init__(parent, width=width, height=height, bg=THEME["bg_header"], highlightthickness=0)
        r = height / 2
        pad = 1
        self.shape = draw_rounded_rect(self, pad, pad, width-pad, height-pad, r, fill=bg_color, outline="")
        self.entry = tk.Entry(self, textvariable=textvariable, 
                              font=("Consolas", 11, "bold"),
                              bg=bg_color, fg=fg_color,
                              bd=0, justify="center",
                              insertbackground="white")
        self.create_window(width/2, height/2, window=self.entry, width=width-20, height=height-6)

class RoundedPill(tk.Canvas):
    def __init__(self, parent, width=40, height=20):
        super().__init__(parent, width=width, height=height, bg=THEME["bg_panel"], highlightthickness=0)
        self.current_val = -1
        self.bg_parent = THEME["bg_panel"]
        r = height / 2
        self.bg_shape = draw_rounded_rect(self, 0, 0, width, height, r, fill=THEME["pill_off_bg"], outline="")
        self.text = self.create_text(width/2, height/2, text="0", fill=THEME["pill_text"], font=("Arial", 9, "bold"))

    def set_state(self, val):
        if val == self.current_val: return
        self.current_val = val
        self.itemconfig(self.text, text=str(val))
        if val > 0:
            self.itemconfig(self.bg_shape, fill=THEME["pill_on_bg"])
        else:
            self.itemconfig(self.bg_shape, fill=THEME["pill_off_bg"])

class BitRow(tk.Frame):
    def __init__(self, parent, index_label, text, bg_color, on_click=None):
        super().__init__(parent, bg=bg_color, height=28)
        self.pack_propagate(False)
        self.default_bg = bg_color
        self.shift = 0 
        self.mask = 1  
        self.on_click = on_click

        lbl_idx = tk.Label(self, text=index_label, font=("Consolas", 9), width=6, anchor="w", fg=THEME["text_dim"], bg=bg_color)
        lbl_idx.pack(side="left", padx=(12, 0))
        
        self.lbl_text = tk.Label(self, text=text, font=("Microsoft YaHei UI", 9), fg=THEME["text_main"], bg=bg_color, anchor="w")
        self.lbl_text.pack(side="left", fill="both", expand=True)
        
        self.pill = RoundedPill(self)
        self.pill.configure(bg=bg_color)
        self.pill.pack(side="right", padx=12)

        if self.on_click:
            self.bind("<Button-1>", self.handle_click)
            lbl_idx.bind("<Button-1>", self.handle_click)
            self.lbl_text.bind("<Button-1>", self.handle_click)
            self.pill.bind("<Button-1>", self.handle_click)

    def handle_click(self, event):
        if self.on_click:
            self.on_click(self.shift, self.mask)

    def set_state(self, val):
        self.pill.set_state(val)
        self.lbl_text.config(fg="white" if val > 0 else THEME["text_main"])

    def set_highlight(self, is_highlight):
        color = THEME["diff_bg"] if is_highlight else self.default_bg
        self.configure(bg=color)
        self.lbl_text.configure(bg=color)
        self.pill.configure(bg=color)
        for child in self.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=color)

class PanelColumn(tk.Frame):
    def __init__(self, parent, title, var, texts, icon="⚡", show_compare_btn=True, entry_width=70):
        super().__init__(parent, bg=THEME["bg_panel"], highlightbackground=THEME["border"], highlightthickness=1)
        self.var = var
        self.texts = texts 
        self.title_text = title
        self.icon_symbol = icon
        
        header = tk.Frame(self, bg=THEME["bg_header"], height=42)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        h_container = tk.Frame(header, bg=THEME["bg_header"])
        h_container.pack(fill="both", expand=True, padx=10)
        
        left_box = tk.Frame(h_container, bg=THEME["bg_header"])
        left_box.pack(side="left", fill="y")
        tk.Label(left_box, text=icon, font=("Segoe UI", 11), fg=THEME["title_fg"], bg=THEME["bg_header"]).pack(side="left", padx=(0, 6))
        tk.Label(left_box, text=title, font=("Microsoft YaHei UI", 10, "bold"), fg=THEME["title_fg"], bg=THEME["bg_header"]).pack(side="left")
        
        if show_compare_btn:
            btn_wrapper = tk.Frame(h_container, bg=THEME["bg_header"])
            btn_wrapper.pack(side="right", pady=7)
            self.btn_compare = RoundedButton(btn_wrapper, text="+", command=self.open_compare_window, 
                                             width=26, height=26, corner_radius=13, font_size=12,
                                             bg_normal='#EBCB8B', bg_hover='#D0B075', outer_bg=THEME["bg_header"])
            self.btn_compare.pack()

        input_wrapper = tk.Frame(h_container, bg=THEME["bg_header"])
        input_wrapper.pack(side="left", padx=(15, 0), pady=7)
        self.rounded_entry = RoundedEntry(input_wrapper, textvariable=var, width=entry_width, height=26)
        self.rounded_entry.pack(side="left")
        
        tk.Frame(self, bg=THEME["border"], height=1).pack(fill="x")
        
        list_frame = tk.Frame(self, bg=THEME["bg_panel"])
        list_frame.pack(fill="both", expand=True)
        
        self.rows = []
        
        bit_idx = 0
        row_display_idx = 0
        
        while bit_idx < len(texts):
            content = texts[bit_idx]
            
            if content is None:
                bit_idx += 1
                continue
            
            row_bg = THEME["bg_panel"] if row_display_idx % 2 == 0 else "#2c313c"
            
            if isinstance(content, tuple):
                text_label, width = content
                index_label = f".{bit_idx}-{bit_idx+width-1}" 
                row = BitRow(list_frame, index_label, text_label, row_bg, on_click=self.on_row_click)
                row.shift = bit_idx
                row.mask = (1 << width) - 1 
                self.rows.append(row)
                row.pack(fill="x", pady=0)
                bit_idx += width 
            else:
                index_label = f".{bit_idx:<4}"
                row = BitRow(list_frame, index_label, content, row_bg, on_click=self.on_row_click)
                row.shift = bit_idx
                row.mask = 1
                self.rows.append(row)
                row.pack(fill="x", pady=0)
                bit_idx += 1
            
            row_display_idx += 1

        self._trace_id = self.var.trace_add("write", self.on_typing)
        self.bind("<Destroy>", self.on_destroy)
        self.rounded_entry.entry.bind("<FocusOut>", self.on_focus_out)
        self.on_typing()

    def on_destroy(self, event):
        if event.widget == self:
            try:
                self.var.trace_remove("write", self._trace_id)
            except Exception:
                pass

    def on_row_click(self, shift, mask):
        current_text = self.var.get().strip()
        current_val = self.parse_value(current_text)
        if current_val is None: 
            current_val = 0
        
        current_part_val = (current_val >> shift) & mask
        
        if mask == 1:
            new_part_val = 1 - current_part_val
        else:
            new_part_val = (current_part_val + 1) & mask
            
        new_total_val = current_val & ~(mask << shift)
        new_total_val |= (new_part_val << shift)
        
        if current_text.startswith("16#"):
            new_text = f"16#{new_total_val:X}"
        elif current_text.lower().startswith("0x"):
            new_text = f"0x{new_total_val:X}"
        else:
            new_text = str(new_total_val)
            
        self.var.set(new_text)

    def open_compare_window(self):
        CompareWindow(self, self.title_text, self.texts, self.icon_symbol)

    def parse_value(self, text):
        raw = text.strip().replace(" ", "")
        if not raw: return 0 
        try:
            if raw.startswith("16#"): return int(raw[3:], 16)
            if raw.lower().startswith("0x"): return int(raw, 16)
            return int(raw, 10)
        except ValueError:
            return None 

    def on_typing(self, *args):
        try:
            if not self.winfo_exists(): return
        except Exception: return

        text = self.var.get()
        val = self.parse_value(text)
        if val is not None:
            self.rounded_entry.entry.config(fg=THEME["input_fg"]) 
            self.update_bits(val)
        else:
            self.rounded_entry.entry.config(fg=THEME["input_err"])
            self.update_bits(0)

    def on_focus_out(self, event):
        text = self.var.get()
        val = self.parse_value(text)
        if val is None: self.var.set("0")

    def update_bits(self, val):
        for row in self.rows:
            bit_val = (val >> row.shift) & row.mask
            row.set_state(bit_val)

class CompareWindow(tk.Toplevel):
    def __init__(self, parent, title, texts, icon):
        super().__init__(parent)
        self.withdraw() # --- 核心修改：先隐藏窗口 ---
        
        self.title(f"对比模式 - {title}")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        self.texts = texts
        
        w, h = 600, 540
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self.var_a = tk.StringVar(value="0")
        self.var_b = tk.StringVar(value="0")
        
        container = tk.Frame(self, bg=THEME["bg_window"])
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.panel_a = PanelColumn(container, f"{title} (A)", self.var_a, texts, icon, show_compare_btn=False, entry_width=70)
        self.panel_a.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.panel_b = PanelColumn(container, f"{title} (B)", self.var_b, texts, icon, show_compare_btn=False, entry_width=70)
        self.panel_b.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        self.var_a.trace_add("write", self.check_diff)
        self.var_b.trace_add("write", self.check_diff)
        
        self.deiconify() # --- 核心修改：布局完成后再显示 ---

    def check_diff(self, *args):
        val_a = self.panel_a.parse_value(self.var_a.get()) or 0
        val_b = self.panel_b.parse_value(self.var_b.get()) or 0
        
        for i in range(len(self.panel_a.rows)):
            row_a = self.panel_a.rows[i]
            row_b = self.panel_b.rows[i]
            
            val_row_a = (val_a >> row_a.shift) & row_a.mask
            val_row_b = (val_b >> row_b.shift) & row_b.mask
            
            is_diff = (val_row_a != val_row_b)
            
            row_a.set_highlight(is_diff)
            row_b.set_highlight(is_diff)

class SelectionWindow(tk.Toplevel):
    def __init__(self, parent, configs, current_selection, on_confirm):
        super().__init__(parent)
        self.withdraw()
        
        self.title("选择显示内容")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        self.on_confirm = on_confirm
        self.configs = configs
        self.max_selection = 4

        w, h = 300, 450
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(False, False)

        self.check_vars = {}
        
        main_frame = tk.Frame(self, bg=THEME["bg_window"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(main_frame, text="请勾选需显示的控制/状态字 (最多4项)", 
                 font=("Microsoft YaHei UI", 10, "bold"), fg=THEME["title_fg"], bg=THEME["bg_window"]).pack(pady=(0, 10))

        for i, (key, config) in enumerate(configs.items(), 1):
            var = tk.BooleanVar(value=(key in current_selection))
            var.trace_add("write", lambda *args, k=key: self.on_check_change(k))
            self.check_vars[key] = var
            
            text_str = f"{i}. {config['title']}"
            
            chk = tk.Checkbutton(main_frame, text=text_str, 
                                 variable=var, 
                                 bg=THEME["bg_window"], fg=THEME["text_main"], selectcolor=THEME["bg_panel"],
                                 activebackground=THEME["bg_window"], activeforeground=THEME["text_main"],
                                 font=("Microsoft YaHei UI", 10))
            chk.pack(anchor="w", pady=2)

        btn_frame = tk.Frame(self, bg=THEME["bg_window"])
        btn_frame.pack(side="bottom", fill="x", pady=20)
        
        confirm_btn = RoundedButton(btn_frame, text="确定", command=self.confirm_selection, 
                                    width=120, height=35, bg_normal=THEME["pill_on_bg"], outer_bg=THEME["bg_window"])
        confirm_btn.pack()
        
        self.deiconify()

    def on_check_change(self, changed_key):
        selected_count = sum(1 for var in self.check_vars.values() if var.get())
        if selected_count > self.max_selection:
            self.check_vars[changed_key].set(False)

    def confirm_selection(self):
        new_selection = [key for key in self.configs.keys() if self.check_vars[key].get()]
        self.on_confirm(new_selection)
        self.destroy()

class ProDriveDashboard(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.withdraw() 
        self.title("PROFINET Drive Monitor")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        self.vars = {} 

        self.panel_configs = {
            "STW1": {
                "title": "STW1", "icon": "⚡", 
                "texts": [
                    "OFF1 减速停机↑", "OFF2 自由停机", "OFF3 紧急停机", "允许运行", 
                    "不拒绝任务", "不暂停任务", "激活运行任务↑", "复位故障↑", 
                    "JOG1 点动", "JOG2 点动", "PLC 控制", "开始回原点", 
                    "保留", "外部程序段切换↑", "切换至转矩模式", "保留"
                ]
            },
            "POS_STW1": {
                "title": "POS_STW1 ", "icon": "⌖", 
                "texts": [
                    ("运行程序段选择 (Bit0-3)", 4), None, None, None, 
                    "保留", "保留", "保留", "保留", 
                    "定位模式 1=绝对/0=相对", 
                    ("定位方向 1=正向/2=负向", 2), None, 
                    "保留", "连续传输", "保留", "信号选择(Mode=3)", "MDI 选择"
                ]
            },
            "POS_STW2": {
                "title": "POS_STW2 ", "icon": "⚙️", 
                "texts": [
                    "保留", "设置参考点", "参考点挡块激活", "保留", 
                    "保留", "点动模式 1=位置/0=速度", "保留", "保留", 
                    "保留", "回原方向 (0=正/1=负)", "保留", "保留", 
                    "保留", "保留", "激活软件限位", "激活硬件限位"
                ]
            },
            "STW2": {
                "title": "STW2 ", "icon": "🔧", 
                "texts": [
                    "保留", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "保留", 
                    "运行至固定停止点", "保留", "保留", "保留", 
                    "主站心跳 Bit0", "主站心跳 Bit1", "主站心跳 Bit2", "主站心跳 Bit3"
                ]
            },
            "ZSW1": {
                "title": "ZSW1 ", "icon": "📊", 
                "texts": [
                    "准备开启", "准备就绪", "运行使能", "有故障", 
                    "OFF2 无效", "OFF3 无效", "禁止接通", "有报警", 
                    "无位置偏差故障", "PLC 控制请求", "到达目标位置", "已完成回参考点", 
                    "程序段应答", "驱动器静止", "转矩控制有效", "保留"
                ]
            },
            "ZSW2": {
                "title": "ZSW2 ", "icon": "📡", 
                "texts": [
                    "保留", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "保留", 
                    "运行至固定停止点", "保留", "保留", "保留", 
                    "生命信号 Bit0", "生命信号 Bit1", "生命信号 Bit2", "生命信号 Bit3"
                ]
            },
            "POS_ZSW1": {
                "title": "POS_ZSW1 ", "icon": "📈", 
                "texts": [
                    ("激活程序段0-15(Bit0-3)", 4), None, None, None, 
                    "保留", "保留", "保留", "保留", 
                    "负向硬限位触发", "正向硬限位触发", "JOG 模式激活", "回原模式激活", 
                    "保留", "程序段模式激活", "保留", "MDI 模式激活"
                ]
            },
            "POS_ZSW2": {
                "title": "POS_ZSW2", "icon": "📉", 
                "texts": [
                    "保留", "到达速度限制", "保留", "保留", 
                    "轴正向移动", "轴负向移动", "负向软限位触发", "正向软限位触发", 
                    "保留", "保留", "保留", "保留", 
                    "到达固定停止点", "达到夹紧转矩", "固定停止点功能激活", "保留"
                ]
            },
            "MELDW": {
                "title": "MELDW ", "icon": "💬", 
                "texts": [
                    "保留", "未到达转矩限制", "保留", "保留", 
                    "保留", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "驱动器使能", 
                    "运行准备好", "驱动器运行", "保留", "保留"
                ]
            }

        }
        
        self.visible_keys = ["STW1", "ZSW1", "POS_STW1", "POS_STW2"] 
        self.panels = {}
        
        self.container = tk.Frame(self, bg=THEME["bg_window"])
        self.container.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.footer = tk.Frame(self, bg=THEME["bg_window"])
        self.footer.pack(fill="x", side="bottom", padx=15, pady=(0, 15))
        
        self.btn_switch = RoundedButton(self.footer, text="切换", command=self.open_selection_dialog, 
                                        width=100, height=35, bg_normal='#EBCB8B', bg_hover='#D0B075', 
                                        fg_color='#2E3440', outer_bg=THEME["bg_window"])
        self.btn_switch.pack(side="right")

        self.refresh_panels()
        
        self.center_window(1100, 600)
        self.deiconify()

    def open_selection_dialog(self):
        SelectionWindow(self, self.panel_configs, self.visible_keys, self.update_visible_panels)

    def update_visible_panels(self, new_selection):
        self.visible_keys = new_selection
        self.vars.clear() 
        self.refresh_panels()

    def refresh_panels(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.panels.clear()
        
        for i in range(4):
            self.container.columnconfigure(i, weight=1)
            
        for idx, key in enumerate(self.visible_keys):
            if idx >= 4: break 
            
            cfg = self.panel_configs[key]
            if key not in self.vars:
                self.vars[key] = tk.StringVar(value="0")
                
            p = PanelColumn(self.container, cfg["title"], self.vars[key], cfg["texts"], cfg["icon"])
            p.grid(row=0, column=idx, sticky="nsew", padx=2)
            self.panels[key] = p

    def center_window(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() 
    app = ProDriveDashboard(root)
    app.protocol("WM_DELETE_WINDOW", lambda: (root.destroy(), sys.exit()))
    root.mainloop()