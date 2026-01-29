import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import math
import os
import sys

# 导入监控界面模块
import gui_AI 

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
    except Exception as e:
        print(f'Warning: Failed to load icon: {e}')
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# --- 修改：手动几何绘制圆角矩形，替换原有的 splines 绘制 ---
def _draw_rounded_rect_manual(canvas, x, y, w, h, r, **kwargs):
    r = min(r, h/2, w/2)
    points = []
    # 1. Top-left
    for i in range(180, 270+1, 5):
        a = math.radians(i)
        points.extend([x + r + r*math.cos(a), y + r + r*math.sin(a)])
    # 2. Top-right
    for i in range(270, 360+1, 5):
        a = math.radians(i)
        points.extend([x + w - r + r*math.cos(a), y + r + r*math.sin(a)])
    # 3. Bottom-right
    for i in range(0, 90+1, 5):
        a = math.radians(i)
        points.extend([x + w - r + r*math.cos(a), y + h - r + r*math.sin(a)])
    # 4. Bottom-left
    for i in range(90, 180+1, 5):
        a = math.radians(i)
        points.extend([x + r + r*math.cos(a), y + h - r + r*math.sin(a)])
        
    return canvas.create_polygon(points, smooth=False, **kwargs)

class RoundedEntry(tk.Canvas):

    def __init__(self, parent, textvariable, width=120, height=30, corner_radius=10, bg_color='#434C5E', fg_color='white', outer_bg='#2E3440', state='normal', font_size=9, validate='none', validatecommand=None, **kwargs):
        super().__init__(parent, width=width, height=height, bg=outer_bg, bd=0, highlightthickness=0, **kwargs)
        self.textvariable = textvariable
        self.bg_normal = bg_color
        self.bg_disabled = '#232831'
        self.fg_normal = fg_color
        self.fg_disabled = '#4C566A'
        self.corner_radius = corner_radius
        # 使用新绘制方法
        self.rect_id = _draw_rounded_rect_manual(self, 2, 2, width - 2, height - 2, corner_radius, fill=bg_color)
        font_style = ('Microsoft YaHei UI', font_size)
        current_bg = bg_color
        current_fg = fg_color
        if state == 'readonly':
            font_style = ('Consolas', font_size + 2, 'bold')
            current_fg = '#A3BE8C'
            current_bg = '#232831'
            self.itemconfig(self.rect_id, fill=current_bg)
        self.entry = tk.Entry(self, textvariable=textvariable, font=font_style, bg=current_bg, fg=current_fg, bd=0, justify='center', state=state, disabledbackground=current_bg, disabledforeground=self.fg_disabled, readonlybackground=current_bg, insertbackground='white', validate=validate, validatecommand=validatecommand)
        self.create_window(width / 2, height / 2, window=self.entry, width=width - 12, height=height - 8)

    def set_state(self, state):
        self.entry.config(state=state)
        if state == 'disabled':
            bg = self.bg_disabled
            fg = self.fg_disabled
        elif state == 'readonly':
            bg = '#232831'
            fg = '#A3BE8C'
        else:
            bg = self.bg_normal
            fg = self.fg_normal
        self.itemconfig(self.rect_id, fill=bg)
        self.entry.config(bg=bg, fg=fg, disabledbackground=bg)

class RoundedButton(tk.Canvas):

    def __init__(self, parent, text, command, width=180, height=45, corner_radius=15, bg_normal='#5E81AC', bg_hover='#81A1C1', fg_color='white', outer_bg='#2E3440', font_size=11, **kwargs):
        super().__init__(parent, width=width, height=height, bg=outer_bg, bd=0, highlightthickness=0, cursor='hand2', **kwargs)
        self.command = command
        self.bg_normal = bg_normal
        self.bg_hover = bg_hover
        # 使用新绘制方法
        self.rect_id = _draw_rounded_rect_manual(self, 2, 2, width - 2, height - 2, corner_radius, fill=bg_normal)
        self.text_id = self.create_text(width / 2, height / 2, text=text, fill=fg_color, font=('Microsoft YaHei UI', font_size, 'bold'))
        self.bind('<Enter>', lambda e: self.itemconfig(self.rect_id, fill=self.bg_hover))
        self.bind('<Leave>', lambda e: self.itemconfig(self.rect_id, fill=self.bg_normal))
        self.bind('<Button-1>', lambda e: self.command() if self.command else None)

class GearCalcWindow(tk.Toplevel):

    def __init__(self, parent, colors, callback=None):
        super().__init__(parent)
        self.withdraw()
        self.title('计算助手')
        set_window_icon(self)
        self.colors = colors
        self.callback = callback
        self.configure(bg=colors['bg_main'])
        self.window_height = 280
        self._anim_job = None
        self.vcmd = (self.register(self.validate_int), '%P')
        self.enc_res = tk.StringVar(value='8388608')
        self.cmd_pulse = tk.StringVar(value='10000')
        self.gear_data = []
        self.gear_id_counter = 0
        self.res_n = tk.StringVar(value='---')
        self.res_d = tk.StringVar(value='---')
        self.has_calculated = False
        self.setup_ui()
        self.add_gear_data(is_init=True)
        self.update_idletasks()
        self._center_window_init()
        self.deiconify()

    def validate_int(self, P):
        if P == '':
            return True
        return P.isdigit()

    def setup_ui(self):
        self.main_container = tk.Frame(self, bg=self.colors['bg_panel'])
        self.main_container.pack(fill='both', expand=True, padx=20, pady=20)
        self.equation_frame = tk.Frame(self.main_container, bg=self.colors['bg_panel'])
        self.equation_frame.pack(expand=True, anchor='center')
        btm_bar = tk.Frame(self, bg=self.colors['bg_main'])
        btm_bar.pack(fill='x', pady=(0, 15), side='bottom')
        self.btn_apply = RoundedButton(btm_bar, text='应用结果到主界面', command=self.apply_result, width=200, height=40, bg_normal=self.colors['accent_green'], outer_bg=self.colors['bg_main'], fg_color='#2E3440')
        self.btn_apply.pack()

    def _center_window_init(self):
        req_width = self.equation_frame.winfo_reqwidth()
        target_width = max(450, req_width + 60)
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = int(ws / 2 - target_width / 2)
        y = int(hs / 2 - self.window_height / 2)
        self.geometry(f'{target_width}x{self.window_height}+{x}+{y}')

    def update_window_size(self):
        self.equation_frame.update_idletasks()
        req_width = self.equation_frame.winfo_reqwidth()
        target_width = req_width + 60
        if target_width < 450:
            target_width = 450
        ws = self.winfo_screenwidth()
        target_x = int(ws / 2 - target_width / 2)
        y = int(self.winfo_screenheight() / 2 - self.window_height / 2)
        self._smooth_resize(target_width, target_x, y)

    def _smooth_resize(self, target_w, target_x, fixed_y):
        if self._anim_job:
            self.after_cancel(self._anim_job)
        current_w = self.winfo_width()
        current_x = self.winfo_x()
        diff_w = target_w - current_w
        diff_x = target_x - current_x
        if abs(diff_w) < 1 and abs(diff_x) < 1:
            self.geometry(f'{int(target_w)}x{self.window_height}+{int(target_x)}+{fixed_y}')
            self._anim_job = None
            return
        new_w = current_w + diff_w / 3
        new_x = current_x + diff_x / 3
        self.geometry(f'{int(new_w)}x{self.window_height}+{int(new_x)}+{fixed_y}')
        self._anim_job = self.after(10, lambda: self._smooth_resize(target_w, target_x, fixed_y))

    def add_gear_data(self, is_init=False):
        if len(self.gear_data) >= 5:
            return
        self.gear_id_counter += 1
        self.gear_data.append({'id': self.gear_id_counter, 'n': tk.StringVar(value='1'), 'd': tk.StringVar(value='1')})
        self.refresh_equation_layout(animate=not is_init)

    def remove_gear_data(self, target_id):
        if len(self.gear_data) <= 1:
            return
        self.gear_data = [g for g in self.gear_data if g['id'] != target_id]
        self.refresh_equation_layout(animate=True)

    def refresh_equation_layout(self, animate=True):
        for widget in self.equation_frame.winfo_children():
            widget.destroy()
        self._draw_fraction_block(self.equation_frame, '编码器分辨率', self.enc_res, '指令脉冲数', self.cmd_pulse, is_input=True)
        count = len(self.gear_data)
        for i, gear in enumerate(self.gear_data):
            self._draw_operator(self.equation_frame, '*')
            allow_delete = count > 1
            self._draw_fraction_block(self.equation_frame, f'减速机{i + 1} 分子', gear['n'], f'减速机{i + 1} 分母', gear['d'], is_input=True, delete_id=gear['id'] if allow_delete else None)
        self._draw_operator(self.equation_frame, '*')
        if count < 5:
            self._draw_add_button(self.equation_frame)
        else:
            self._draw_max_limit_label(self.equation_frame)
        self._draw_eq_button(self.equation_frame)
        self._draw_fraction_block(self.equation_frame, '电子齿轮比分子', self.res_n, '电子齿轮比分母', self.res_d, is_input=False)
        if animate:
            self.update_window_size()

    def _draw_fraction_block(self, parent, label_top, var_top, label_bot, var_bot, is_input=True, delete_id=None):
        container = tk.Frame(parent, bg=self.colors['bg_panel'])
        container.pack(side='left', padx=5, pady=10, anchor='center')
        top_ctrl = tk.Frame(container, bg=self.colors['bg_panel'], height=18)
        top_ctrl.pack(fill='x')
        if delete_id is not None:
            del_btn = tk.Label(top_ctrl, text='×', font=('Arial', 12, 'bold'), fg='#BF616A', bg=self.colors['bg_panel'], cursor='hand2')
            del_btn.pack(side='right')
            del_btn.bind('<Button-1>', lambda e: self.remove_gear_data(delete_id))
        else:
            tk.Label(top_ctrl, text=' ', font=('Arial', 12), bg=self.colors['bg_panel']).pack()
        tk.Label(container, text=label_top, font=('Microsoft YaHei UI', 8), fg=self.colors['fg_label'], bg=self.colors['bg_panel']).pack()
        if is_input:
            RoundedEntry(container, textvariable=var_top, width=100, height=26, outer_bg=self.colors['bg_panel'], validate='key', validatecommand=self.vcmd).pack(pady=2)
        else:
            RoundedEntry(container, textvariable=var_top, width=120, height=30, state='readonly', outer_bg=self.colors['bg_panel']).pack(pady=2)
        line = tk.Frame(container, height=2, bg='white', width=100)
        line.pack(pady=4, fill='x')
        if is_input:
            RoundedEntry(container, textvariable=var_bot, width=100, height=26, outer_bg=self.colors['bg_panel'], validate='key', validatecommand=self.vcmd).pack(pady=2)
        else:
            RoundedEntry(container, textvariable=var_bot, width=120, height=30, state='readonly', outer_bg=self.colors['bg_panel']).pack(pady=2)
        tk.Label(container, text=label_bot, font=('Microsoft YaHei UI', 8), fg=self.colors['fg_label'], bg=self.colors['bg_panel']).pack()

    def _draw_operator(self, parent, symbol):
        tk.Label(parent, text=symbol, font=('Arial', 18, 'bold'), fg=self.colors['fg_label'], bg=self.colors['bg_panel']).pack(side='left', padx=0, anchor='center')

    def _draw_add_button(self, parent):
        frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        frame.pack(side='left', padx=8, anchor='center')
        RoundedButton(frame, text='+', command=self.add_gear_data, width=36, height=36, corner_radius=18, font_size=16, bg_normal='#81A1C1', outer_bg=self.colors['bg_panel']).pack()
        tk.Label(frame, text='新增', font=('Microsoft YaHei UI', 7), fg=self.colors['fg_label'], bg=self.colors['bg_panel']).pack(pady=2)

    def _draw_max_limit_label(self, parent):
        frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        frame.pack(side='left', padx=8, anchor='center')
        tk.Label(frame, text='MAX', font=('Arial', 8, 'bold'), fg='#BF616A', bg=self.colors['bg_panel']).pack()

    def _draw_eq_button(self, parent):
        frame = tk.Frame(parent, bg=self.colors['bg_panel'])
        frame.pack(side='left', padx=15, anchor='center')
        RoundedButton(frame, text='=', command=self.calculate, width=45, height=45, corner_radius=22, font_size=20, bg_normal=self.colors['accent_gold'], fg_color='#2E3440', outer_bg=self.colors['bg_panel']).pack()

    def calculate(self):
        try:
            enc_str, cmd_str = (self.enc_res.get(), self.cmd_pulse.get())
            if not enc_str or not cmd_str:
                raise ValueError('参数为空')
            enc, cmd = (int(enc_str), int(cmd_str))
            if cmd == 0:
                raise ValueError('分母为0')
            mech_total_n = 1
            mech_total_d = 1
            for gear in self.gear_data:
                ns, ds = (gear['n'].get(), gear['d'].get())
                if not ns or not ds:
                    raise ValueError('参数为空')
                n, d = (int(ns), int(ds))
                if d == 0:
                    raise ValueError('分母为0')
                mech_total_n *= n
                mech_total_d *= d
            else:
                mech_common = math.gcd(mech_total_n, mech_total_d)
                self.calculated_mech_n = mech_total_n // mech_common
                self.calculated_mech_d = mech_total_d // mech_common
                final_n = enc * mech_total_n
                final_d = cmd * mech_total_d
                common = math.gcd(final_n, final_d)
                self.res_n.set(str(final_n // common))
                self.res_d.set(str(final_d // common))
                self.has_calculated = True
        except ValueError:
            messagebox.showerror('错误', '请输入有效数字')
            self.has_calculated = False

    def apply_result(self):
        if not self.has_calculated:
            self.calculate()
        if self.has_calculated and self.res_n.get():
            if self.callback:
                self.callback(self.res_n.get(), self.res_d.get(), str(self.calculated_mech_n), str(self.calculated_mech_d), self.enc_res.get())
            self.destroy()
        else:
            messagebox.showwarning('提示', '请先计算结果')

def draw_rotary_icon(canvas, x, y, size=60, color='#88C0D0'):
    y_offset = 10
    canvas.create_oval(x, y + y_offset, x + size, y + size + y_offset, outline=color, width=3)
    cx, cy = (x + size / 2, y + size / 2 + y_offset)
    r = size / 3
    canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=30, extent=240, style='arc', outline=color, width=2)
    canvas.create_polygon(cx + r - 5, cy + r / 2, cx + r + 5, cy + r / 2 - 5, cx + r + 5, cy + r / 2 + 10, fill=color)
    canvas.create_text(cx, cy + size / 1.3 + 5, text='Rotary', fill='white', font=('Arial', 9))

def draw_linear_icon(canvas, x, y, w=80, h=40, color='#EBCB8B'):
    y_center = y + 35
    canvas.create_line(x, y_center, x + w, y_center, fill=color, width=2)
    for i in range(0, w, 10):
        canvas.create_line(x + i, y_center - 5, x + i + 5, y_center + 5, fill=color, width=1)
    canvas.create_rectangle(x + w / 2 - 10, y_center - 10, x + w / 2 + 10, y_center + 10, outline=color, width=2, fill='#2E3440')
    canvas.create_line(x + w / 2 + 15, y_center, x + w - 5, y_center, arrow='last', fill=color)
    canvas.create_text(x + w / 2, y_center + 25, text='Linear', fill='white', font=('Arial', 9))

class FB284Calculator(tk.Tk):

    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title('Epos Calculator Pro')
        set_window_icon(self)
        self.colors = {'bg_main': '#2E3440', 'bg_panel': '#3B4252', 'bg_output': '#252A33', 'fg_text': '#ECEFF4', 'fg_label': '#D8DEE9', 'fg_disabled': '#4C566A', 'accent_blue': '#88C0D0', 'accent_gold': '#EBCB8B', 'accent_green': '#A3BE8C', 'line_color': '#ECEFF4'}
        self.configure(bg=self.colors['bg_main'])
        
        # --- 初始高度调整 ---
        self.center_window(1150, 720) 
        # ------------------
        
        self.setup_style()
        self.init_variables()
        self.create_smart_scroll_container()
        self.create_widgets(self.scrollable_frame)
        self.deiconify()

    def center_window(self, width, height):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # --- 最小高度调整 ---
        self.minsize(1000, 620)
        # ------------------

    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        c = self.colors
        style.configure('TFrame', background=c['bg_main'])
        style.configure('Panel.TFrame', background=c['bg_panel'])
        style.configure('Output.TFrame', background=c['bg_output'])
        style.configure('Card.TLabelframe', background=c['bg_panel'], relief='flat', borderwidth=0)
        style.configure('Card.TLabelframe.Label', background=c['bg_panel'], foreground=c['accent_blue'], font=('Microsoft YaHei UI', 11, 'bold'), padding=(5, 5))
        style.configure('Result.TLabelframe', background=c['bg_output'], relief='solid', borderwidth=1, bordercolor='#4C566A')
        style.configure('Result.TLabelframe.Label', background=c['bg_output'], foreground=c['accent_green'], font=('Microsoft YaHei UI', 12, 'bold'), padding=(5, 5))
        style.configure('TLabel', background=c['bg_panel'], foreground=c['fg_label'], font=('Microsoft YaHei UI', 9))
        style.configure('Output.TLabel', background=c['bg_output'], foreground=c['fg_label'], font=('Microsoft YaHei UI', 10))
        style.configure('SubHeader.TLabel', foreground=c['accent_gold'], font=('Microsoft YaHei UI', 9, 'bold'), background=c['bg_panel'])
        style.configure('GreenHeader.TLabel', foreground=c['accent_green'], font=('Microsoft YaHei UI', 9, 'bold'), background=c['bg_panel'])
        style.configure('Unit.TLabel', foreground='#8FBCBB', font=('Microsoft YaHei UI', 8), background=c['bg_panel'])
        style.configure('TSeparator', background='#434C5E')
        style.configure('Radio.TRadiobutton', background=c['bg_panel'], foreground='white', font=('Microsoft YaHei UI', 10))
        style.configure('Vertical.TScrollbar', gripcount=0, background=c['bg_panel'], darkcolor=c['bg_main'], lightcolor=c['bg_main'], troughcolor=c['bg_main'], bordercolor=c['bg_main'], arrowcolor=c['fg_label'])
        style.map('Vertical.TScrollbar', background=[('active', '#4C566A')])

    def init_variables(self):
        self.gear_n = tk.StringVar(value='---')
        self.gear_d = tk.StringVar(value='---')
        self.mech_res_rev = tk.StringVar(value='---')
        self.mech_res_deg = tk.StringVar(value='---')
        self.motor_res_rev = tk.StringVar(value='---')
        self.motor_res_deg = tk.StringVar(value='---')
        self.mech_type = tk.StringVar(value='linear')
        self.linear_lead = tk.StringVar(value='10')
        self.ratio_n = tk.StringVar(value='8388608')
        self.ratio_d = tk.StringVar(value='10000')
        self.enc_res = tk.StringVar(value='8388608')
        self.rated_spd = tk.StringVar(value='3000')
        self.OverV = tk.StringVar(value='100')
        self.OverAcc = tk.StringVar(value='100')
        self.OverDec = tk.StringVar(value='100')
        self.Velocity = tk.StringVar(value='0')
        self.Epos_Acc_Max = tk.StringVar(value='100')
        self.Epos_Dec_Max = tk.StringVar(value='100')
        self.Jog_V_Pct = tk.StringVar(value='10')
        self.Jog_Acc = tk.StringVar(value='5')
        self.Jog_Dec = tk.StringVar(value='5')
        
        self.act_vel_code = tk.StringVar(value='0') 
        self.res_act_vel = tk.StringVar(value='---') 
        
        # --- 新增变量: 实际负载转速 ---
        self.res_act_load_vel = tk.StringVar(value='---')
        # ----------------------------

        self.res_pos_cmd = tk.StringVar(value='---')
        self.res_unit_convert = tk.StringVar(value='---')
        self.res_pos_ref_unit = tk.StringVar(value='---')
        self.res_vel_max = tk.StringVar(value='---')
        self.res_motor_spd = tk.StringVar(value='---')
        self.res_real_spd = tk.StringVar(value='---')
        self.res_real_spd_unit = tk.StringVar(value='mm/s')
        self.res_epos_acc_t = tk.StringVar(value='---')
        self.res_epos_dec_t = tk.StringVar(value='---')
        self.res_jog_acc_t = tk.StringVar(value='---')
        self.res_jog_dec_t = tk.StringVar(value='---')

    def create_smart_scroll_container(self):
        self.outer_frame = ttk.Frame(self)
        self.outer_frame.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(self.outer_frame, bg=self.colors['bg_main'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.outer_frame, orient='vertical', command=self.canvas.yview, style='Vertical.TScrollbar')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.bind_all('<MouseWheel>', self._on_mousewheel)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self._check_scrollbar()

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._check_scrollbar()

    def _check_scrollbar(self):
        if not self.canvas.bbox('all'):
            return
        scroll_region_height = self.canvas.bbox('all')[3]
        visible_height = self.canvas.winfo_height()
        if scroll_region_height > visible_height and visible_height > 10:
            if not self.scrollbar.winfo_ismapped():
                self.scrollbar.pack(side='right', fill='y')
        elif self.scrollbar.winfo_ismapped():
            self.scrollbar.pack_forget()

    def _on_mousewheel(self, event):
        if self.scrollbar.winfo_ismapped():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def create_widgets(self, parent):
        main = ttk.Frame(parent)
        main.pack(fill='both', expand=True, padx=20, pady=(15, 5))
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=5)
        left_container = ttk.Frame(main)
        left_container.grid(row=0, column=0, sticky='nsew', padx=(0, 15))
        self.create_mechanism_panel(left_container)
        ttk.Frame(left_container, height=10).pack()
        self.create_mech_panel(left_container)
        right_container = ttk.Frame(main)
        right_container.grid(row=0, column=1, sticky='nsew')
        self.create_input_panel(right_container)
        ttk.Frame(right_container, height=10).pack()
        self.create_result_panel(right_container)

    def create_mechanism_panel(self, parent):
        panel = ttk.LabelFrame(parent, text=' 🏗️ 机构模型 (Model) ', style='Card.TLabelframe', padding=10)
        panel.pack(fill='x', side='top')
        container = ttk.Frame(panel, style='Panel.TFrame')
        container.pack(expand=True, anchor='center')
        f_lin = ttk.Frame(container, style='Panel.TFrame')
        f_lin.pack(side='left', padx=15)
        cv_lin = tk.Canvas(f_lin, width=100, height=100, bg=self.colors['bg_panel'], highlightthickness=0)
        cv_lin.pack()
        draw_linear_icon(cv_lin, 10, 0)
        rb_lin = ttk.Radiobutton(f_lin, text='线性机构', variable=self.mech_type, value='linear', command=self.update_mech_ui, style='Radio.TRadiobutton')
        rb_lin.pack(pady=2)
        self.f_lin_input = ttk.Frame(f_lin, style='Panel.TFrame')
        self.f_lin_input.pack(pady=(0, 5))
        ttk.Label(self.f_lin_input, text='导程', font=('Microsoft YaHei UI', 8)).pack(side='left', padx=(0, 2))
        self.entry_lead = RoundedEntry(self.f_lin_input, textvariable=self.linear_lead, width=60, height=24, outer_bg=self.colors['bg_panel'])
        self.entry_lead.pack(side='left')
        self.lbl_unit_mm = ttk.Label(self.f_lin_input, text='mm', font=('Microsoft YaHei UI', 8), foreground=self.colors['fg_label'])
        self.lbl_unit_mm.pack(side='left', padx=(3, 0))
        ttk.Separator(container, orient='vertical').pack(side='left', fill='y', padx=10)
        f_rot = ttk.Frame(container, style='Panel.TFrame')
        f_rot.pack(side='left', padx=15)
        cv_rot = tk.Canvas(f_rot, width=80, height=110, bg=self.colors['bg_panel'], highlightthickness=0)
        cv_rot.pack()
        draw_rotary_icon(cv_rot, 10, 0, size=60)
        rb_rot = ttk.Radiobutton(f_rot, text='旋转机构', variable=self.mech_type, value='rotary', command=self.update_mech_ui, style='Radio.TRadiobutton')
        rb_rot.pack(pady=5)
        tk.Frame(f_rot, height=29, bg=self.colors['bg_panel']).pack()
        self.update_mech_ui()

    def create_mech_panel(self, parent):
        panel = ttk.LabelFrame(parent, text=' ⚙️ 机械传动 (Mech) ', style='Card.TLabelframe', padding=15)
        panel.pack(fill='x', side='top')
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=0)
        panel.columnconfigure(2, weight=1)
        self.create_rounded_row(panel, 0, '减速比分子 (电机):', self.gear_n)
        self.create_rounded_row(panel, 1, '减速比分母 (负载):', self.gear_d)
        ttk.Separator(panel, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky='ew', pady=10)
        ttk.Label(panel, text='📌 机械比计算结果(Results)', style='GreenHeader.TLabel').grid(row=3, column=0, columnspan=3, sticky='w', pady=(0, 10))
        ttk.Label(panel, text='电机转 1 圈 ➜ 负载输出:').grid(row=4, column=0, columnspan=3, sticky='w', pady=(5, 5))
        self.create_mech_result_row(panel, 5, '负载圈数:', self.mech_res_rev, 'rev')
        self.create_mech_result_row(panel, 6, '负载角度:', self.mech_res_deg, '°')
        ttk.Label(panel, text='负载转 1 圈 ➜ 电机需转:').grid(row=7, column=0, columnspan=3, sticky='w', pady=(10, 5))
        self.create_mech_result_row(panel, 8, '电机圈数:', self.motor_res_rev, 'rev')
        self.create_mech_result_row(panel, 9, '电机角度:', self.motor_res_deg, '°')
        btn_mech = RoundedButton(panel, text='执行机械比计算', command=self.calc_mechanical, width=160, height=40, bg_normal='#A3BE8C', bg_hover='#B5D19E', fg_color='#2E3440', outer_bg=self.colors['bg_panel'])
        btn_mech.grid(row=10, column=0, columnspan=3, pady=(15, 0))

    def create_mech_result_row(self, parent, row_idx, label_text, var, unit_text):
        lbl = ttk.Label(parent, text=label_text)
        lbl.grid(row=row_idx, column=0, sticky='e', padx=(0, 10), pady=4)
        entry = RoundedEntry(parent, textvariable=var, width=120, height=28, state='readonly', outer_bg=self.colors['bg_panel'])
        entry.grid(row=row_idx, column=1, sticky='w')
        u_lbl = ttk.Label(parent, text=unit_text, foreground='#8FBCBB', font=('Microsoft YaHei UI', 9))
        u_lbl.grid(row=row_idx, column=2, sticky='w', padx=(10, 0))

    def create_input_panel(self, parent):
        panel = ttk.LabelFrame(parent, text=' 📝 EPOS 参数设定 (EPOS Parameters) ', style='Card.TLabelframe', padding=15)
        panel.pack(fill='x', side='top')
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)
        panel.columnconfigure(2, weight=1)
        
        f_hw = ttk.Frame(panel, style='Panel.TFrame')
        f_hw.grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 10))
        
        # === 标题栏容器 ===
        header_frame = ttk.Frame(f_hw, style='Panel.TFrame')
        header_frame.pack(fill='x', pady=(0, 5))

        # 1. 标题 (左对齐)
        ttk.Label(header_frame, text='⚡ 电机与齿轮参数 (Motor)', style='SubHeader.TLabel').pack(side='left', anchor='center')

        # 2. 状态监控按钮 (紧跟标题左侧，增加 padx 间距)
        btn_monitor = RoundedButton(header_frame, text='📊 状态监控', command=self.open_monitor_ui, 
                                    width=100, height=30, # 适应标题栏高度
                                    corner_radius=10, font_size=9, 
                                    bg_normal='#EBCB8B', bg_hover='#D0B075', # 金色风格
                                    outer_bg=self.colors['bg_panel'], fg_color='#2E3440')
        btn_monitor.pack(side='left', padx=(20, 0)) 
        # ----------------------------------------

        hw_grid = ttk.Frame(f_hw, style='Panel.TFrame')
        hw_grid.pack(fill='x')
        col1_frame = ttk.Frame(hw_grid, style='Panel.TFrame')
        col1_frame.pack(side='left', fill='y', padx=(0, 20))
        self.create_row_simple_label_left(col1_frame, 'D02.22 编码器分辨率:', self.enc_res, width=100)
        ttk.Frame(col1_frame, height=5, style='Panel.TFrame').pack()
        self.create_row_simple_label_left(col1_frame, 'D00.05 电机额定转速 (RPM):', self.rated_spd, width=100)
        ratio_frame = ttk.Frame(hw_grid, style='Panel.TFrame')
        ratio_frame.pack(side='left', padx=20)
        ttk.Label(ratio_frame, text='电子齿轮比 (G00.06 / G00.08):').pack(side='left', padx=(0, 10))
        frac_frame = ttk.Frame(ratio_frame, style='Panel.TFrame')
        frac_frame.pack(side='left')
        RoundedEntry(frac_frame, textvariable=self.ratio_n, width=80, height=24, outer_bg=self.colors['bg_panel']).pack()
        tk.Frame(frac_frame, height=2, bg=self.colors['line_color'], width=80).pack(pady=3, fill='x')
        RoundedEntry(frac_frame, textvariable=self.ratio_d, width=80, height=24, outer_bg=self.colors['bg_panel']).pack()
        btn_gear_calc = RoundedButton(ratio_frame, text='⚙️ 计算助手', command=self.open_gear_calculator, width=100, height=40, corner_radius=10, font_size=9, bg_normal='#EBCB8B', bg_hover='#D0B075', outer_bg=self.colors['bg_panel'], fg_color='#2E3440')
        btn_gear_calc.pack(side='left', padx=(15, 0))
        ttk.Separator(panel, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', pady=10)
        f_lim = ttk.Frame(panel, style='Panel.TFrame')
        f_lim.grid(row=2, column=0, sticky='nsew', padx=(0, 10))
        ttk.Label(f_lim, text='🚀 速度与限制', style='SubHeader.TLabel').pack(anchor='w', pady=(5, 5))
        self.create_row_simple(f_lim, 'Velocity(1000LU/min):', self.Velocity)
        
        self.create_row_simple(f_lim, 'ActVelocity(0x40000000):', self.act_vel_code)
        
        self.create_row_simple(f_lim, 'G03.33 EPOS最大加速度 (1000LU/s²):', self.Epos_Acc_Max)
        self.create_row_simple(f_lim, 'G03.34 EPOS最大减速度 (1000LU/s²):', self.Epos_Dec_Max)
        f_ov = ttk.Frame(panel, style='Panel.TFrame')
        f_ov.grid(row=2, column=1, sticky='nsew', padx=5)
        ttk.Label(f_ov, text='🎛️ 倍率设定', style='SubHeader.TLabel').pack(anchor='w', pady=(5, 5))
        self.create_row_simple(f_ov, 'OverV (%):', self.OverV)
        self.create_row_simple(f_ov, 'OverAcc (%):', self.OverAcc)
        self.create_row_simple(f_ov, 'OverDec (%):', self.OverDec)
        f_jog = ttk.Frame(panel, style='Panel.TFrame')
        f_jog.grid(row=2, column=2, sticky='nsew', padx=(10, 0))
        ttk.Label(f_jog, text='👆 JOG 速度点动', style='SubHeader.TLabel').pack(anchor='w', pady=(5, 5))
        self.create_row_simple(f_jog, 'B03.16 JOG Speed (%):', self.Jog_V_Pct)
        self.create_row_simple(f_jog, 'B04.02 JOG Acc (s):', self.Jog_Acc)
        self.create_row_simple(f_jog, 'B04.03 JOG Dec (s):', self.Jog_Dec)

    def create_result_panel(self, parent):
        panel = ttk.LabelFrame(parent, text=' 📌 EPOS计算结果 (Results) ', style='Result.TLabelframe', padding=20)
        panel.pack(fill='both', expand=True)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=0)
        panel.columnconfigure(2, weight=1)
        res_col1 = ttk.Frame(panel, style='Output.TFrame')
        res_col1.grid(row=0, column=0, sticky='n')
        res_col1.columnconfigure(0, weight=1)
        res_col1.columnconfigure(1, weight=0)
        res_col1.columnconfigure(2, weight=0)
        
        # --- 修改点：左侧列从 row=0 开始排列，修复对齐问题 ---
        self.create_output_row_grid(res_col1, 0, '🚀 设定电机转速:', self.res_motor_spd, 'RPM')
        self.create_output_row_grid_dynamic_unit(res_col1, 1, '🚀 设定负载转速:', self.res_real_spd, self.res_real_spd_unit)
        self.create_output_row_grid(res_col1, 2, '🚀 额定电机转速:', self.res_vel_max, '1000LU/min')
        self.create_output_row_grid(res_col1, 3, '🚀 实际电机转速:', self.res_act_vel, 'RPM')
        self.create_output_row_grid_dynamic_unit(res_col1, 4, '🚀 实际负载转速:', self.res_act_load_vel, self.res_real_spd_unit)
        # -------------------------------------------------
        
        ttk.Separator(panel, orient='vertical').grid(row=0, column=1, sticky='ns', padx=20)
        res_col2 = ttk.Frame(panel, style='Output.TFrame')
        res_col2.grid(row=0, column=2, sticky='n')
        res_col2.columnconfigure(0, weight=1)
        res_col2.columnconfigure(1, weight=0)
        res_col2.columnconfigure(2, weight=0)
        self.create_output_row_grid(res_col2, 0, '⏱️ EPOS 加速时间:', self.res_epos_acc_t, 's')
        self.create_output_row_grid(res_col2, 1, '⏱️ EPOS 减速时间:', self.res_epos_dec_t, 's')
        self.create_output_row_grid(res_col2, 2, '⏱️ JOG 实际加速时间:', self.res_jog_acc_t, 's')
        self.create_output_row_grid(res_col2, 3, '⏱️ JOG 实际减速时间:', self.res_jog_dec_t, 's')
        
        self.create_output_row_grid(res_col2, 4, '📍 电机单圈位置指令:', self.res_pos_cmd, 'LU/圈')
        self.create_output_row_grid_dynamic_unit(res_col2, 5, '📍 负载单圈位置指令:', self.res_unit_convert, self.res_pos_ref_unit)

        btn_calc = RoundedButton(panel, text='执行EPOS计算', command=self.calc_drive, width=220, height=50, bg_normal='#A3BE8C', bg_hover='#B5D19E', fg_color='#2E3440', outer_bg=self.colors['bg_output'])
        btn_calc.grid(row=1, column=0, columnspan=3, pady=(15, 0))

    def create_rounded_row(self, parent, row, label, var):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky='e', padx=(0, 10), pady=6)
        RoundedEntry(parent, textvariable=var, width=120, height=28, outer_bg=self.colors['bg_panel']).grid(row=row, column=1, sticky='w')

    def create_row_simple(self, parent, label, var):
        f = ttk.Frame(parent, style='Panel.TFrame')
        f.pack(fill='x', pady=4)
        ttk.Label(f, text=label).pack(side='left', padx=(0, 5))
        RoundedEntry(f, textvariable=var, width=90, height=26, outer_bg=self.colors['bg_panel']).pack(side='right')

    def create_row_simple_label_left(self, parent, label, var, width=90):
        f = ttk.Frame(parent, style='Panel.TFrame')
        f.pack(fill='x', pady=5)
        ttk.Label(f, text=label).pack(side='left', padx=(0, 5))
        RoundedEntry(f, textvariable=var, width=width, height=26, outer_bg=self.colors['bg_panel']).pack(side='right')

    def create_output_row_grid(self, parent, row_idx, label, var, unit=''):
        lbl = ttk.Label(parent, text=label, style='Output.TLabel')
        # --- 修改点：pady 从 8 改为 4 ---
        lbl.grid(row=row_idx, column=0, sticky='e', padx=(0, 15), pady=4) 
        # -----------------------------
        # --- 修改点：width 从 150 改为 110 ---
        entry = RoundedEntry(parent, textvariable=var, width=110, height=30, state='readonly', outer_bg=self.colors['bg_output'])
        # -----------------------------------
        entry.grid(row=row_idx, column=1, sticky='w')
        if unit:
            u_lbl = ttk.Label(parent, text=unit, style='Output.TLabel', foreground='#687586', width=12) # Added width
            u_lbl.grid(row=row_idx, column=2, sticky='w', padx=(10, 0))

    def create_output_row_grid_dynamic_unit(self, parent, row_idx, label, var, unit_var):
        lbl = ttk.Label(parent, text=label, style='Output.TLabel')
        # --- 修改点：pady 从 8 改为 4 ---
        lbl.grid(row=row_idx, column=0, sticky='e', padx=(0, 15), pady=4)
        # -----------------------------
        # --- 修改点：width 从 150 改为 110 ---
        entry = RoundedEntry(parent, textvariable=var, width=110, height=30, state='readonly', outer_bg=self.colors['bg_output'])
        # -----------------------------------
        entry.grid(row=row_idx, column=1, sticky='w')
        u_lbl = ttk.Label(parent, textvariable=unit_var, style='Output.TLabel', foreground='#687586', width=12) # Added width
        u_lbl.grid(row=row_idx, column=2, sticky='w', padx=(10, 0))

    def reset_results(self):
        # --- 修改点：增加重置项 ---
        result_vars = [self.res_pos_cmd, self.res_unit_convert, self.res_pos_ref_unit, self.res_vel_max, self.res_motor_spd, self.res_real_spd, self.res_epos_acc_t, self.res_epos_dec_t, self.res_jog_acc_t, self.res_jog_dec_t, self.res_act_vel, self.res_act_load_vel]
        # ------------------------
        for var in result_vars:
            var.set('---')

    def update_mech_ui(self):
        self.reset_results()
        m_type = self.mech_type.get()
        if m_type == 'linear':
            self.entry_lead.set_state('normal')
            self.lbl_unit_mm.config(foreground=self.colors['fg_label'])
            self.res_real_spd_unit.set('mm/s')
            lead = self.linear_lead.get()
        else:
            self.entry_lead.set_state('disabled')
            self.lbl_unit_mm.config(foreground=self.colors['fg_disabled'])
            self.res_real_spd_unit.set('°/s')

    def get_float(self, var):
        try:
            val = var.get()
            return float(val) if val else 0.0
        except ValueError:
            return 0.0

    def open_gear_calculator(self):

        def apply_callback(elec_n, elec_d, mech_n, mech_d, enc_res_val):
            self.ratio_n.set(elec_n)
            self.ratio_d.set(elec_d)
            self.gear_n.set(mech_n)
            self.gear_d.set(mech_d)
            self.enc_res.set(enc_res_val)
            self.calc_mechanical()
        GearCalcWindow(self, self.colors, callback=apply_callback)

    # 监控界面入口
    def open_monitor_ui(self):
        try:
            if hasattr(self, 'monitor_win') and self.monitor_win.winfo_exists():
                self.monitor_win.lift()  
                self.monitor_win.focus_force() 
                return

            self.monitor_win = gui_AI.ProDriveDashboard(self)
        except Exception as e:
            messagebox.showerror("无法打开监控界面", f"加载 gui_AI 失败: {str(e)}")

    def calc_mechanical(self):
        try:
            raw_n, raw_d = (self.gear_n.get(), self.gear_d.get())
            if raw_n == '-' or raw_d == '-' or (not raw_n) or (not raw_d):
                return
            n, d = (float(raw_n), float(raw_d))
            if n == 0 or d == 0:
                raise ValueError('减速比不能为0')
            self.mech_res_rev.set(f'{d / n:.4g}')
            self.mech_res_deg.set(f'{360 * d / n:.4g}')
            self.motor_res_rev.set(f'{n / d:.4g}')
            self.motor_res_deg.set(f'{360 * n / d:.4g}')
        except ValueError:
            messagebox.showerror('错误', '请输入有效的数字')
        except Exception as e:
            messagebox.showerror('错误', str(e))

    def calc_drive(self):
        try:
            rn, rd = (self.get_float(self.ratio_n), self.get_float(self.ratio_d))
            enc, rated = (self.get_float(self.enc_res), self.get_float(self.rated_spd))
            ov_v = self.get_float(self.OverV)
            if rd == 0 or enc == 0 or rn == 0 or (ov_v == 0):
                raise ValueError('关键 EPOS 参数不能为 0')
            
            try:
                act_code_val = float(self.act_vel_code.get())
                # 公式: 额定转速 * (输入值 / 1073741824)
                act_real_rpm = rated * (act_code_val / 1073741824.0)
                self.res_act_vel.set(f'{act_real_rpm:.2f}')
                
                # --- 实际负载转速逻辑 (严谨模式) ---
                try:
                    # 获取机械参数 (严格校验，非法则不计算)
                    raw_mn = self.gear_n.get()
                    raw_md = self.gear_d.get()
                    
                    # 检查是否为初始化值 '---' 或空
                    if not raw_mn or not raw_md or raw_mn == '---' or raw_md == '---':
                        raise ValueError

                    mn = float(raw_mn)
                    md = float(raw_md)
                    
                    if mn == 0 or md == 0: 
                        raise ValueError
                    
                    act_load_rpm = act_real_rpm * (md / mn)
                    
                    if self.mech_type.get() == 'rotary':
                        act_load_val = act_load_rpm * 6.0 
                    else:
                        lead = self.get_float(self.linear_lead)
                        act_load_val = act_load_rpm / 60.0 * lead 
                    
                    self.res_act_load_vel.set(f'{act_load_val:.2f}')
                
                except (ValueError, TypeError):
                    self.res_act_load_vel.set('---')
                # ----------------------------------------

            except ValueError:
                self.res_act_vel.set('---')
                self.res_act_load_vel.set('---')

            pos_lu_per_motor_rev = rd * enc / rn
            self.res_pos_cmd.set(f'{pos_lu_per_motor_rev:.0f}')
            mech_type = self.mech_type.get()
            lead_val = 0.0
            vel = self.get_float(self.Velocity)
            rpm = vel * 1000 * (ov_v / 100) / enc * (rn / rd)
            self.res_motor_spd.set(f'{rpm:.2f}')
            try:
                raw_mech_n = self.gear_n.get()
                raw_mech_d = self.gear_d.get()
                mech_n = float(raw_mech_n)
                mech_d = float(raw_mech_d)
                if mech_d == 0 or mech_n == 0:
                    raise ValueError
                motor_revs_per_load_rev = mech_n / mech_d
                lu_total = pos_lu_per_motor_rev * motor_revs_per_load_rev
                self.res_unit_convert.set(f'{lu_total:.0f}')
                if mech_type == 'rotary':
                    self.res_pos_ref_unit.set('LU/360°')
                else:
                    lead_val = self.get_float(self.linear_lead)
                    self.res_pos_ref_unit.set(f'LU/{lead_val}mm')
                load_rpm = rpm * (mech_d / mech_n)
                real_speed = load_rpm * 6.0 if mech_type == 'rotary' else load_rpm / 60.0 * lead_val
                self.res_real_spd.set(f'{real_speed:.2f}')
            except (ValueError, TypeError):
                self.res_unit_convert.set('---')
                self.res_pos_ref_unit.set('---')
                self.res_real_spd.set('---')
            v_max = rated * rd * enc * 100 / (rn * 1000 * ov_v)
            epos_acc, epos_dec = (self.get_float(self.Epos_Acc_Max), self.get_float(self.Epos_Dec_Max))
            ov_acc, ov_dec = (self.get_float(self.OverAcc), self.get_float(self.OverDec))
            t_epos_acc = vel * ov_v / (epos_acc * ov_acc * 60) if epos_acc * ov_acc > 0 else 0
            t_epos_dec = vel * ov_v / (epos_dec * ov_dec * 60) if epos_dec * ov_dec > 0 else 0
            jog_v, jog_a, jog_d = (self.get_float(self.Jog_V_Pct), self.get_float(self.Jog_Acc), self.get_float(self.Jog_Dec))
            t_jog_acc = jog_v * jog_a / 100.0
            t_jog_dec = jog_v * jog_d / 100.0
            self.res_vel_max.set(f'{v_max:.0f}')
            self.res_epos_acc_t.set(f'{t_epos_acc:.3f}')
            self.res_epos_dec_t.set(f'{t_epos_dec:.3f}')
            self.res_jog_acc_t.set(f'{t_jog_acc:.3f}')
            self.res_jog_dec_t.set(f'{t_jog_dec:.3f}')
        except Exception as e:
            messagebox.showerror('计算错误', str(e))
if __name__ == '__main__':
    app = FB284Calculator()
    app.mainloop()