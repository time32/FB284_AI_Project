import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import math
import subprocess

# --- 引入 PIL 库用于图片缩放 (需 pip install pillow) ---
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

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
    
    "diff_bg":     "#8b2a2a",      # 差异高亮背景色 (红底)

    # 表格配色
    "tree_bg":     "#23272e",      # 基础背景
    "tree_bg_alt": "#3a404a",      # 偶数行背景 (斑马纹)
    "tree_fg":     "#ffffff",      # 默认文字
    "tree_head_bg": "#21252b",     
    "tree_head_fg": "#e5c07b",     # 金色表头
    "tree_sel":    "#61afef",      # 选中底色
    
    # 滚动条配色
    "scroll_bg":   "#21252b",      
    "scroll_thumb": "#4b5263",     
    "scroll_hover": "#5c6370",     
    
    # 特殊高亮
    "red_highlight": "#ff6666",    # 红色高亮文字
    "hover_row":     "#4b5263"     # 鼠标悬停行背景
}

# --- 报文数据定义 (新增) ---
# --- 报文数据定义 ---
TELEGRAM_DATA = {
    "1": {
        "title": "标准 1 号报文",
        "info": {
            "type": "标准 1 号报文", "mode": "速度控制模式", "class": "AC1",
            "qty_out": "2", "qty_in": "2"
        },
        "data": [
            ("PZD1", "STW1", "控制字 1", "ZSW1", "状态字 1"),
            ("PZD2", "NSOLL_A", "转速设定值 A (16 位)", "NIST_A", "转速实际值 A (16 位)")
        ]
    },
    "3": {
        "title": "标准 3 号报文",
        "info": {
            "type": "标准 3 号报文", "mode": "速度控制模式", "class": "AC1, AC4",
            "qty_out": "5", "qty_in": "9"
        },
        # data 仅存储简单行，复杂布局在 draw_3_layout 中硬编码
        "data": [] 
    },
    "102": {
        "title": "西门子 102 报文",
        "info": {
            "type": "西门子 102 报文", "mode": "速度控制模式", "class": "AC1, AC4",
            "qty_out": "6", "qty_in": "10"
        },
        "data": [] # 复杂布局在 draw_102_layout 中硬编码
    },
    "105": {
        "title": "西门子 105 报文",
        "info": {
            "type": "西门子 105 报文", "mode": "位置控制模式", "class": "AC4",
            "qty_out": "10", "qty_in": "10"
        },
        "data": [] # 复杂布局在 draw_105_layout 中硬编码
    },
    "111": {
        "title": "西门子 111 报文",
        "info": {
            "type": "西门子 111 报文", "mode": "位置控制模式", "class": "AC3",
            "qty_out": "12", "qty_in": "12"
        },
        "data": [
            ("PZD1",  "STW1", "控制字 1", "ZSW1", "状态字 1"),
            ("PZD2",  "POS_STW1", "定位控制字 1", "POS_ZSW1", "定位状态字 1"),
            ("PZD3",  "POS_STW2", "定位控制字 2", "POS_ZSW2", "定位状态字 2"),
            ("PZD4",  "STW2", "控制字 2", "ZSW2", "状态字 2"),
            ("PZD5",  "OVERRIDE", "位置速度倍率", "MELDW", "消息字"),
            ("PZD6-7","MDI_TARPOS", "MDI 位置 (32位)", "XIST_A", "位置实际值 A"),
            ("PZD8-9","MDI_VELOCITY", "MDI 速度 (32位)", "NIST_B", "转速实际值 B (32位)"),
            ("PZD10", "MDI_ACC", "MDI 加速度倍率", "FAULT_CODE", "故障代码"),
            ("PZD11", "MDI_DEC", "MDI 减速度倍率", "WARN_CODE", "警告代码"),
            ("PZD12", "自由配置", "调试软件自由配置\n(输入 PZD2)", "自由配置", "通过调试软件自由配置\n(PZD 输出 1)")
        ]
    },
    "352": {
        "title": "西门子 352 报文",
        "info": {
            "type": "西门子 352 报文", "mode": "速度控制模式", "class": "AC1",
            "qty_out": "6", "qty_in": "6"
        },
        "data": [
            ("PZD1", "STW1", "控制字 1", "ZSW1", "状态字 1"),
            ("PZD2", "NSOLL_A", "转速设定值 A (16 位)", "NIST_A_GLATT", "转速实际值"),
            ("PZD3", "自由配置", "通过调试软件自由配置\n(输入 PZD3)", "IAIST_GLATT", "电流实际值"),
            ("PZD4", "自由配置", "通过调试软件自由配置\n(输入 PZD4)", "MIST_GLATT", "转矩实际值"),
            ("PZD5", "自由配置", "通过调试软件自由配置\n(输入 PZD5)", "WARN_CODE", "警告代码"),
            ("PZD6", "自由配置", "通过调试软件自由配置\n(输入 PZD6)", "FAULT_CODE", "故障代码")
        ]
    }
}


# --- 模式表格数据定义 ---
MODE_TABLE_DATA = {
    1: [# 模式1 : MDI 相对定位
        ("STW1.%X4", "False", "*CancelTraversing 置1", "任务取消"),
        ("STW1.%X5", "False", "*IntermediateStop 置1", "任务暂停"),
        ("STW1.%X6", "False", "*ExecuteMode 上升沿触发", "定位触发信号"),
        ("STW1.%X8", "False", "", "Ture=点动 1 激活"),
        ("STW1.%X9", "False", "", "Ture=点动 2 激活"),
        ("STW1.%X11", "False", "RefTyp上升沿触发被动回参考点功能", "开启回参考点"),
        ("EPosSTW1.%X8", "False", "*False", "False=相对定位\nTure=绝对定位"),
        ("EPosSTW1.%X9", "False", "Positive=x9=1为正向\nPositive和Negative都为0或者1,则x9=x10=0", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X10", "False", "Negative=x10=1为负向\nPositive和Negative都为0或者1,则x9=x10=0", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X14", "False", "False", "Ture = 已选择信号调整(Mode=3)\nFalse = 已选择信号定位"),
        ("EPosSTW1.%X15", "False", "*True", "True=进入MDI模式"),
        ("EPosSTW2.%X1", "False", "", "Ture=设置参考点"),
        ("EPosSTW2.%X5", "False", "", "Ture = JOG,增量激活\nFalse = JOG,速度激活"),
        ("EPosSTW2.%X8", "False", "RefTyp上升沿触发,选择被动回参考点功能", "False=主动回参考点\nTure =被动回参考点"),
        ("EPosSTW2.%X9", "False", "", "Ture = 在负方向上开始搜索参考点\nFalse = 在正方向上开始搜索参考点"),
    ],
    2:  [# 模式2 : MDI 绝对定位
        ("STW1.%X4", "False", "*CancelTraversing 置1", "任务取消"),
        ("STW1.%X5", "False", "*IntermediateStop 置1", "任务暂停"),
        ("STW1.%X6", "False", "*ExecuteMode 上升沿触发", "定位触发信号"),
        ("STW1.%X8", "False", "", "Ture=点动 1 激活"),
        ("STW1.%X9", "False", "", "Ture=点动 2 激活"),
        ("STW1.%X11", "False", "RefTyp上升沿触发被动回参考点功能", "开启回参考点"),
        ("EPosSTW1.%X8", "False", "*True", "False=相对定位\nTure=绝对定位"),
        ("EPosSTW1.%X9", "False", "*Positive=x9=1为正向\nPositive和Negative都为0或者1,则x9=x10=0", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X10", "False", "*Negative=x10=1为负向\nPositive和Negative都为0或者1,则x9=x10=0", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X14", "False", "False", "Ture = 已选择信号调整(Mode=3)\nFalse = 已选择信号定位"),
        ("EPosSTW1.%X15", "False", "*True", "True=进入MDI模式"),
        ("EPosSTW2.%X1", "False", "", "Ture=设置参考点"),
        ("EPosSTW2.%X5", "False", "", "Ture = JOG,增量激活\nFalse = JOG,速度激活"),
        ("EPosSTW2.%X8", "False", "RefTyp上升沿触发,选择被动回参考点功能", "False=主动回参考点\nTure =被动回参考点"),
        ("EPosSTW2.%X9", "False", "", "Ture = 在负方向上开始搜索参考点\nFalse = 在正方向上开始搜索参考点"),
    ],
    3: [ # 模式3 : MDI 连续运行
        ("STW1.%X4", "False", "*CancelTraversing 置1", "任务取消"),
        ("STW1.%X5", "False", "*IntermediateStop 置1", "任务暂停"),
        ("STW1.%X6", "False", "*ExecuteMode 上升沿触发", "定位触发信号"),
        ("STW1.%X8", "False", "", "Ture=点动 1 激活"),
        ("STW1.%X9", "False", "", "Ture=点动 2 激活"),
        ("STW1.%X11", "False", "RefTyp上升沿触发被动回参考点功能", "开启回参考点"),
        ("EPosSTW1.%X8", "False", "*True", "False=相对定位\nTure=绝对定位"),
        ("EPosSTW1.%X9", "False", "*Positive=x9=1为正向\nPositive和Negative都为0或者1,则x9=x10=0", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X10", "False", "*Negative=x10=1为负向\nPositive和Negative都为0或者1,则x9=x10=0", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X14", "False", "*True", "Ture = 已选择信号调整(Mode=3)\nFalse = 已选择信号定位"),
        ("EPosSTW1.%X15", "False", "*True", "True=进入MDI模式"),
        ("EPosSTW2.%X1", "False", "", "Ture=设置参考点"),
        ("EPosSTW2.%X5", "False", "", "Ture = JOG,增量激活\nFalse = JOG,速度激活"),
        ("EPosSTW2.%X8", "False", "RefTyp上升沿触发,选择被动回参考点功能", "False=主动回参考点\nTure =被动回参考点"),
        ("EPosSTW2.%X9", "False", "", "Ture = 在负方向上开始搜索参考点\nFalse = 在正方向上开始搜索参考点"),
    ],
    4: [ # 模式4 : 主动回参考点
        ("STW1.%X4", "False", "", "任务取消"),
        ("STW1.%X5", "False", "", "任务暂停"),
        ("STW1.%X6", "False", "", "定位触发信号"),
        ("STW1.%X8", "False", "", "Ture=点动 1 激活"),
        ("STW1.%X9", "False", "", "Ture=点动 2 激活"),
        ("STW1.%X11", "False", "*ExecuteMode上升沿触发主动回参考点功能\n回原过程中保持1。", "开启回参考点"),
        ("EPosSTW1.%X8", "False", "", "False=相对定位\nTure=绝对定位"),
        ("EPosSTW1.%X9", "False", "", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X10", "False", "", "相对定位下本质上不使用此功能"),
        ("EPosSTW1.%X14", "False", "", "Ture = 已选择信号调整(Mode=3)\nFalse = 已选择信号定位"),
        ("EPosSTW1.%X15", "False", "", "True=进入MDI模式"),
        ("EPosSTW2.%X1", "False", "", "Ture=设置参考点"),
        ("EPosSTW2.%X5", "False", "", "Ture = JOG,增量激活\nFalse = JOG,速度激活"),
        ("EPosSTW2.%X8", "False", "*False主动回原", "False=主动回参考点\nTure =被动回参考点"),
        ("EPosSTW2.%X9", "False", "*Positive=1,为正方向回参考点\nNegative=1,为负方向回参考点\nPositive和Negative都为0或者1,则为正方向开始搜索参考点", "Ture = 在负方向上开始搜索参考点\nFalse = 在正方向上开始搜索参考点"),
    ],
    5:  [ # 模式5 : 设置参考点
        ("STW1.%X4", "False", "", "任务取消"),
        ("STW1.%X5", "False", "", "任务暂停"),
        ("STW1.%X6", "False", "", "定位触发信号"),
        ("STW1.%X8", "False", "", "点动 1 激活"),
        ("STW1.%X9", "False", "", "点动 2 激活"),
        ("STW1.%X11", "False", "", "开启回参考点"),
        ("EPosSTW1.%X0", "False", "", "程序段选择 Bit0(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X1", "False", "", "程序段选择 Bit1(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X2", "False", "", "程序段选择 Bit2(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X3", "False", "", "程序段选择 Bit3(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X4", "False", "", "程序段选择 Bit4(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X5", "False", "", "程序段选择 Bit5(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X8", "False", "", "False=相对定位\nTrue=绝对定位"),
        ("EPosSTW1.%X9", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X10", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X14", "False", "", "False=信号定位\nTrue=信号调整"),
        ("EPosSTW1.%X15", "False", "", "True=进入 MDI 模式"),

        ("EPosSTW2.%X1", "False", "*ExecuteMode上升沿触发设置参考点", "True=设置参考点 (不使能也生效)"),

        ("EPosSTW2.%X5", "False", "", "False=JOG速度\nTrue=JOG增量"),
        ("EPosSTW2.%X8", "False", "", "回参考点False=主动\nTrue=被动"),
    ],
    6: [ # 模式6 : 程序段模式
        ("STW1.%X4", "False", "*CancelTraversing", "任务取消"),
        ("STW1.%X5", "False", "*IntermediateStop", "任务暂停"),
        ("STW1.%X6", "False", "*ExecuteMode上升沿触发", "定位触发信号"),
        ("STW1.%X8", "False", "", "点动 1 激活"),
        ("STW1.%X9", "False", "", "点动 2 激活"),
        ("STW1.%X11", "False", "RefTyp上升沿触发被动回参考点功能", "开启回参考点"),
        ("EPosSTW1.%X0", "False", "*通过Position进行选择", "程序段选择 Bit0\n(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X1", "False", "*通过Position进行选择", "程序段选择 Bit1\n(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X2", "False", "*通过Position进行选择", "程序段选择 Bit2\n(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X3", "False", "*通过Position进行选择", "程序段选择 Bit3\n(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X4", "False", "*通过Position进行选择", "程序段选择 Bit4\n(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X5", "False", "*通过Position进行选择", "程序段选择 Bit5\n(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X8", "False", "", "False=相对定位\nTrue=绝对定位"),
        ("EPosSTW1.%X9", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X10", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X14", "False", "", "False=信号定位\nTrue=信号调整"),
        ("EPosSTW1.%X15", "False", "*False", "True=进入 MDI 模式"),

        ("EPosSTW2.%X1", "False", "", "True=设置参考点 (不使能也生效)"),

        ("EPosSTW2.%X5", "False", "", "False=JOG速度\nTrue=JOG增量"),
        ("EPosSTW2.%X8", "False", "RefTyp上升沿触发\n选择被动回参考点功能", "回参考点False=主动\nTrue=被动"),
    ],
    7: [ # 模式7 : JOG 速度模式
        ("STW1.%X4", "False", "", "任务取消"),
        ("STW1.%X5", "False", "", "任务暂停"),
        ("STW1.%X6", "False", "*ExecuteMode上升沿触发", "定位触发信号"),
        ("STW1.%X8", "False", "*Jog1=1 jog1激活\njog1与jog2同时为0或1,则都为不激活", "点动 1 激活"),
        ("STW1.%X9", "False", "*jog2=1 jog2激活\nog1与jog2同时为0或1,则都为不激活", "点动 2 激活"),
        ("STW1.%X11", "False", "RefTyp上升沿触发被动回参考点功能", "开启回参考点"),
        ("EPosSTW1.%X0", "False", "", "程序段选择 Bit0(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X1", "False", "", "程序段选择 Bit1(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X2", "False", "", "程序段选择 Bit2(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X3", "False", "", "程序段选择 Bit3(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X4", "False", "", "程序段选择 Bit4(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X5", "False", "", "程序段选择 Bit5(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X8", "False", "", "False=相对定位\nTrue=绝对定位"),
        ("EPosSTW1.%X9", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X10", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X14", "False", "", "False=信号定位\nTrue=信号调整"),
        ("EPosSTW1.%X15", "False", "", "True=进入 MDI 模式"),

        ("EPosSTW2.%X1", "False", "", "True=设置参考点 (不使能也生效)"),

        ("EPosSTW2.%X5", "False", "*False", "False=JOG速度\nTrue=JOG增量"),
        ("EPosSTW2.%X8", "False", "RefTyp上升沿触发\n选择被动回参考点功能", "回参考点False=主动\nTrue=被动"),
    ],
    8: [ # 模式8 : JOG 增量模式
        ("STW1.%X4", "False", "", "任务取消"),
        ("STW1.%X5", "False", "", "任务暂停"),
        ("STW1.%X6", "False", "*ExecuteMode上升沿触发", "定位触发信号"),
        ("STW1.%X8", "False", "*Jog1=1 jog1激活\njog1与jog2同时为0或1,则都为不激活", "点动 1 激活"),
        ("STW1.%X9", "False", "*jog2=1 jog2激活\nog1与jog2同时为0或1,则都为不激活", "点动 2 激活"),
        ("STW1.%X11", "False", "RefTyp上升沿触发被动回参考点功能", "开启回参考点"),
        ("EPosSTW1.%X0", "False", "", "程序段选择 Bit0(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X1", "False", "", "程序段选择 Bit1(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X2", "False", "", "程序段选择 Bit2(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X3", "False", "", "程序段选择 Bit3(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X4", "False", "", "程序段选择 Bit4(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X5", "False", "", "程序段选择 Bit5(支持0-15 西门子0-63)"),
        ("EPosSTW1.%X8", "False", "", "False=相对定位\nTrue=绝对定位"),
        ("EPosSTW1.%X9", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X10", "False", "", "相对定位下不使用"),
        ("EPosSTW1.%X14", "False", "", "False=信号定位\nTrue=信号调整"),
        ("EPosSTW1.%X15", "False", "", "True=进入 MDI 模式"),

        ("EPosSTW2.%X1", "False", "", "True=设置参考点 (不使能也生效)"),

        ("EPosSTW2.%X5", "False", "*True", "False=JOG速度\nTrue=JOG增量"),
        ("EPosSTW2.%X8", "False", "RefTyp上升沿触发\n选择被动回参考点功能", "回参考点False=主动\nTrue=被动"),
    ],
}

MODE_NAMES = {
    1: "模式1: MDI 相对定位",
    2: "模式2: MDI 绝对定位",
    3: "模式3: MDI 连续运行",
    4: "模式4: 主动回参考点",
    5: "模式5: 设置参考点",
    6: "模式6: 程序段模式",
    7: "模式7: JOG 速度模式",
    8: "模式8: JOG 增量模式"
}

# --- 资源辅助 ---
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

# --- 绘图工具 ---
def draw_rounded_rect(canvas, x, y, w, h, r, **kwargs):
    r = min(r, h/2, w/2)
    points = []
    for i in range(180, 270+1, 5):
        a = math.radians(i)
        points.extend([x + r + r*math.cos(a), y + r + r*math.sin(a)])
    for i in range(270, 360+1, 5):
        a = math.radians(i)
        points.extend([x + w - r + r*math.cos(a), y + r + r*math.sin(a)])
    for i in range(0, 90+1, 5):
        a = math.radians(i)
        points.extend([x + w - r + r*math.cos(a), y + h - r + r*math.sin(a)])
    for i in range(90, 180+1, 5):
        a = math.radians(i)
        points.extend([x + r + r*math.cos(a), y + h - r + r*math.sin(a)])
    return canvas.create_polygon(points, smooth=False, **kwargs)

# --- 自定义控件 ---
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

# --- 自定义暗色滚动条 ---
class DarkScrollbar(tk.Canvas):
    def __init__(self, parent, command=None, width=14, bg_color=THEME["scroll_bg"], thumb_color=THEME["scroll_thumb"], hover_color=THEME["scroll_hover"], **kwargs):
        super().__init__(parent, width=width, bg=bg_color, highlightthickness=0, **kwargs)
        self.command = command
        self.thumb_color = thumb_color
        self.hover_color = hover_color
        self.bg_color = bg_color
        
        self.start_y = 0
        self.top = 0.0
        self.bottom = 1.0
        
        self.thumb = self.create_rectangle(0, 0, width, 0, fill=thumb_color, outline="", width=0)
        
        self.tag_bind(self.thumb, "<Enter>", self.on_enter)
        self.tag_bind(self.thumb, "<Leave>", self.on_leave)
        self.tag_bind(self.thumb, "<ButtonPress-1>", self.on_press)
        self.tag_bind(self.thumb, "<B1-Motion>", self.on_drag)
        self.bind("<Button-1>", self.on_trough_click)
        
    def set(self, first, last):
        self.top = float(first)
        self.bottom = float(last)
        self.redraw()
        
    def redraw(self):
        h = self.winfo_height()
        w = self.winfo_width()
        if h == 0: return
        
        y0 = int(self.top * h)
        y1 = int(self.bottom * h)
        if y1 - y0 < 10: y1 = y0 + 10
            
        pad = 3
        self.coords(self.thumb, pad, y0, w-pad, y1)
        
    def on_enter(self, event):
        self.itemconfig(self.thumb, fill=self.hover_color)
    def on_leave(self, event):
        self.itemconfig(self.thumb, fill=self.thumb_color)
    def on_press(self, event):
        self.start_y = event.y
    def on_drag(self, event):
        dy = event.y - self.start_y
        h = self.winfo_height()
        if h == 0: return
        delta = dy / h
        new_top = self.top + delta
        if self.command: self.command("moveto", new_top)
        self.start_y = event.y
    def on_trough_click(self, event):
        h = self.winfo_height()
        if h == 0: return
        if self.command: self.command("moveto", event.y / h)

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
    def __init__(self, parent, title, var, texts, icon="⚡", show_compare_btn=True, entry_width=110):
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
        
        input_wrapper = tk.Frame(h_container, bg=THEME["bg_header"])
        input_wrapper.pack(side="right", padx=(0, 0), pady=7)
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

        if show_compare_btn:
            footer_frame = tk.Frame(self, bg=THEME["bg_panel"])
            footer_frame.pack(side="bottom", fill="x", pady=(10, 15)) 

            self.btn_compare = RoundedButton(footer_frame, text="+", command=self.open_compare_window, 
                                             width=30, height=30, corner_radius=15, font_size=14,
                                             bg_normal='#EBCB8B', bg_hover='#D0B075', 
                                             outer_bg=THEME["bg_panel"])
            self.btn_compare.pack(side="right", padx=15)

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
        if current_val is None: current_val = 0
        
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

class ImagePopup(tk.Toplevel):
    def __init__(self, parent, image_path, title="图片查看"):
        super().__init__(parent)
        self.title(title)
        self.withdraw()
        
        self.configure(bg=THEME["bg_window"])
        set_window_icon(self)

        try:
            self.original_image = Image.open(image_path)
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片:\n{e}")
            self.destroy()
            return

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        img_w, img_h = self.original_image.size
        max_w = sw - 100
        max_h = sh - 100
        scale = 1.0
        if img_w > max_w or img_h > max_h:
            scale = min(max_w / img_w, max_h / img_h)
            
        self.imscale = scale
        self.delta = 1.3
        self.image_id = None
        
        win_w = int(img_w * scale)
        win_h = int(img_h * scale)
        
        self.canvas = tk.Canvas(self, bg=THEME["bg_window"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind('<ButtonPress-1>', self.on_move_from)
        self.canvas.bind('<B1-Motion>', self.on_move_to)
        self.canvas.bind('<MouseWheel>', self.on_wheel)
        self.canvas.bind('<Button-4>', self.on_wheel)
        self.canvas.bind('<Button-5>', self.on_wheel)
        
        self.show_image()
        
        x = (sw - win_w) // 2
        y = (sh - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.deiconify()

    def show_image(self, event=None):
        if not self.original_image: return
        new_w = int(self.original_image.width * self.imscale)
        new_h = int(self.original_image.height * self.imscale)
        try:
            resized = self.original_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized)
            if self.image_id:
                self.canvas.itemconfig(self.image_id, image=self.tk_image)
            else:
                self.image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass

    def on_move_from(self, event):
        self.canvas.scan_mark(event.x, event.y)
    def on_move_to(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    def on_wheel(self, event):
        if event.num == 5 or event.delta < 0:
            self.imscale /= self.delta
        if event.num == 4 or event.delta > 0:
            self.imscale *= self.delta
        if self.imscale < 0.1: self.imscale = 0.1
        if self.imscale > 10.0: self.imscale = 10.0
        self.show_image()

class CompareWindow(tk.Toplevel):
    def __init__(self, parent, title, texts, icon):
        super().__init__(parent)
        self.withdraw()
        self.base_title = title
        self.texts = texts
        self.icon_symbol = icon
        self.max_columns = 5
        self.min_columns = 2
        self.panels = [] 
        
        self.title(f"{title}")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        self.main_container = tk.Frame(self, bg=THEME["bg_window"])
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.columns_frame = tk.Frame(self.main_container, bg=THEME["bg_window"])
        self.columns_frame.pack(side="top", fill="both", expand=True)

        self.footer_frame = tk.Frame(self.main_container, bg=THEME["bg_window"], height=45)
        self.footer_frame.pack(side="bottom", fill="x", pady=(10, 0))

        # --- 1. 定义颜色配置 ---
        self.add_colors = {
            "normal": '#EBCB8B',   # 金色
            "hover": '#D0B075'
        }
        self.remove_colors = {
            "normal": THEME["input_err"], # 红色
            "hover": "#ff6666"
        }
        self.disabled_color = "#4b5263"   # 灰色 (禁用)

        # --- 2. 创建按钮 ---
        # [+] 增加列按钮
        self.btn_add = RoundedButton(
            self.footer_frame, 
            text="+", 
            command=self.add_column, 
            width=30, height=30, corner_radius=15, 
            font_size=14,
            bg_normal=self.add_colors["normal"], 
            bg_hover=self.add_colors["hover"], 
            fg_color='#2E3440',
            outer_bg=THEME["bg_window"]
        )
        self.btn_add.pack(side="right", padx=(5, 0)) 

        # [-] 减少列按钮
        self.btn_remove = RoundedButton(
            self.footer_frame, 
            text="−", 
            command=self.remove_column, 
            width=30, height=30, corner_radius=15, 
            font_size=14,
            bg_normal=self.remove_colors["normal"], 
            bg_hover=self.remove_colors["hover"], 
            fg_color='#ffffff',
            outer_bg=THEME["bg_window"]
        )
        self.btn_remove.pack(side="right", padx=(0, 5)) 
        
        # 初始化默认添加两列 (A 和 B)
        self.add_column() 
        self.add_column() 
        
        # --- 3. [关键修复] 强制刷新按钮状态 ---
        # 必须在显示前调用一次，确保2列时减号按钮的内部属性被设为灰色
        self.update_button_visuals()
        
        self.deiconify()

    def add_column(self):
        if len(self.panels) >= self.max_columns:
            return
        col_char = chr(ord('A') + len(self.panels))
        col_title = f"{self.base_title} ({col_char})"
        var = tk.StringVar(value="0")
        var.trace_add("write", self.check_diff)
        panel = PanelColumn(self.columns_frame, col_title, var, self.texts, self.icon_symbol, show_compare_btn=False, entry_width=110)
        panel.pack(side="left", fill="both", expand=True, padx=5)
        self.panels.append(panel)
        self.refresh_ui_state()

    def remove_column(self):
        if len(self.panels) <= self.min_columns:
            return
        panel = self.panels.pop()
        panel.destroy()
        self.refresh_ui_state()

    def refresh_ui_state(self):
        self.resize_window()
        self.check_diff()
        self.update_button_visuals()

    def update_button_visuals(self):
        """
        根据当前列数动态修改按钮颜色。
        [核心修复逻辑]：
        直接修改 btn.bg_normal 和 btn.bg_hover 属性。
        这样即使鼠标触发了 <Enter> 事件，组件内部读取到的 hover 颜色也是灰色的，
        从而彻底防止颜色跳变。
        """
        count = len(self.panels)
        
        # --- 处理 [+] 按钮状态 ---
        if count >= self.max_columns:
            # 禁用：属性全改灰
            self.btn_add.bg_normal = self.disabled_color
            self.btn_add.bg_hover = self.disabled_color
            self.btn_add.itemconfig(self.btn_add.rect_id, fill=self.disabled_color)
        else:
            # 启用：恢复金色配置
            self.btn_add.bg_normal = self.add_colors["normal"]
            self.btn_add.bg_hover = self.add_colors["hover"]
            self.btn_add.itemconfig(self.btn_add.rect_id, fill=self.add_colors["normal"])

        # --- 处理 [-] 按钮状态 ---
        if count <= self.min_columns:
            # 禁用：属性全改灰
            self.btn_remove.bg_normal = self.disabled_color
            self.btn_remove.bg_hover = self.disabled_color
            self.btn_remove.itemconfig(self.btn_remove.rect_id, fill=self.disabled_color)
        else:
            # 启用：恢复红色配置
            self.btn_remove.bg_normal = self.remove_colors["normal"]
            self.btn_remove.bg_hover = self.remove_colors["hover"]
            self.btn_remove.itemconfig(self.btn_remove.rect_id, fill=self.remove_colors["normal"])

    def resize_window(self):
        col_width = 320 
        padding = 40
        total_width = (len(self.panels) * col_width) + padding
        sw = self.winfo_screenwidth()
        total_width = min(total_width, sw - 50)
        h = 600
        sh = self.winfo_screenheight()
        x = (sw - total_width) // 2
        y = (sh - h) // 2
        self.geometry(f"{total_width}x{h}+{x}+{y}")

    def check_diff(self, *args):
        if not self.panels: return
        current_vals = []
        for p in self.panels:
            val = p.parse_value(p.var.get())
            current_vals.append(val if val is not None else 0)
        if not self.panels[0].rows: return
        row_count = len(self.panels[0].rows)
        for r_i in range(row_count):
            bit_vals = []
            row_objs = [] 
            for col_idx, p in enumerate(self.panels):
                row_obj = p.rows[r_i]
                row_objs.append(row_obj)
                val = (current_vals[col_idx] >> row_obj.shift) & row_obj.mask
                bit_vals.append(val)
            is_diff = len(set(bit_vals)) > 1
            for row_obj in row_objs:
                row_obj.set_highlight(is_diff)

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

        w, h = 300, 550
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

class ModeResultWindow(tk.Toplevel):
    def __init__(self, parent, mode_id):
        super().__init__(parent)
        self.withdraw()
        
        title = MODE_NAMES.get(mode_id, f"模式 {mode_id}")
        self.title(f"控制字逻辑表 - {title}")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        w, h = 850, 550
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        style = ttk.Style(self)
        style.theme_use("clam")
        
        style.configure("Treeview",
                        background=THEME["tree_bg"],
                        foreground=THEME["tree_fg"],
                        fieldbackground=THEME["tree_bg"],
                        rowheight=65,
                        font=("Microsoft YaHei UI", 9),
                        borderwidth=0)
        
        style.configure("Treeview.Heading",
                        background=THEME["tree_head_bg"],
                        foreground=THEME["tree_head_fg"],
                        font=("Microsoft YaHei UI", 9, "bold"),
                        borderwidth=1,
                        relief="flat")
        
        style.map("Treeview", 
                  background=[("selected", THEME["tree_sel"])],
                  foreground=[("selected", "white")])

        header_frame = tk.Frame(self, bg=THEME["bg_window"])
        header_frame.pack(fill="x", padx=20, pady=(20, 10)) 
        
        tk.Label(header_frame, text=title, font=("Microsoft YaHei UI", 14, "bold"), 
                 fg=THEME["title_fg"], bg=THEME["bg_window"]).pack(anchor="w")
        
        tk.Label(header_frame, text="下表展示了所选控制模式下各控制字的逻辑含义及变化情况。", 
                 font=("Microsoft YaHei UI", 9), 
                 fg=THEME["text_dim"], bg=THEME["bg_window"]).pack(anchor="w")

        table_container = tk.Frame(self, bg=THEME["bg_window"])
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("control_word", "before", "after", "remark")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("control_word", text="控制字")
        self.tree.heading("before", text="使能前")
        self.tree.heading("after", text="使能后")
        self.tree.heading("remark", text="备注")
        
        self.tree.column("control_word", width=140, anchor="center")
        self.tree.column("before", width=80, anchor="center")
        self.tree.column("after", width=280, anchor="w")
        self.tree.column("remark", width=220, anchor="w")

        scrollbar = DarkScrollbar(table_container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", padx=(5,0))

        self.tree.tag_configure("evenrow", background=THEME["tree_bg_alt"])
        self.tree.tag_configure("red_text", foreground=THEME["red_highlight"]) 
        self.tree.tag_configure("hover_row", background=THEME["hover_row"])

        raw_rows = MODE_TABLE_DATA.get(mode_id, [])
        sorted_rows = sorted(raw_rows, key=lambda r: not any("*" in str(cell) for cell in r))

        for idx, row in enumerate(sorted_rows):
            tags = []
            if idx % 2 != 0: tags.append("evenrow")
            if any("*" in str(cell) for cell in row): tags.append("red_text")
            self.tree.insert("", "end", values=row, tags=tuple(tags))

        self.tree.bind("<Motion>", self.on_mouse_move)
        self.deiconify()

    def on_mouse_move(self, event):
        item_id = self.tree.identify_row(event.y)
        for item in self.tree.get_children():
            tags = list(self.tree.item(item, "tags"))
            if "hover_row" in tags:
                tags.remove("hover_row")
                self.tree.item(item, tags=tags)
        
        if item_id:
            tags = list(self.tree.item(item_id, "tags"))
            if "hover_row" not in tags:
                tags.append("hover_row")
                self.tree.item(item_id, tags=tags)

class StateDiagramSelectionWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title("状态机视图选择")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        self.diagrams = [
            ("通用状态图 (General State Diagram)", "General State Diagram.PNG"),
            ("定位模式状态图 (Positioning Mode)", "State_diagram_of_the_Positioning_Mode.PNG"),
            ("位置反馈接口状态图 (Position Feedback Interface)", "State diagram of the position feedback interfacewith designations of the states and transitions.svg")
        ]

        btn_height = 45 
        win_h = 100 + (len(self.diagrams) * btn_height)
        w = 480 
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{win_h}+{(sw-w)//2}+{(sh-win_h)//2}")
        self.resizable(False, False)

        container = tk.Frame(self, bg=THEME["bg_window"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(container, text="请选择要查看的状态图", 
                 font=("Microsoft YaHei UI", 11, "bold"), fg=THEME["title_fg"], bg=THEME["bg_window"]).pack(pady=(0, 15))

        for name, filename in self.diagrams:
            cmd = lambda f=filename: self.open_image(f)
            btn = RoundedButton(container, text=name, command=cmd,
                                width=440, height=35, corner_radius=8,
                                bg_normal=THEME["pill_on_bg"], bg_hover="#36bd55",
                                fg_color="white", outer_bg=THEME["bg_window"], font_size=9)
            btn.pack(pady=4)
        self.deiconify()

    def open_image(self, filename):
        self.destroy()
        try:
            img_path = resource_path(filename)
            if not os.path.exists(img_path):
                messagebox.showerror("文件缺失", f"未找到文件：\n{filename}\n请确保文件在程序运行目录下。")
                return
            if filename.lower().endswith(".svg"):
                if sys.platform == "win32":
                    os.startfile(img_path)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.call(["open", img_path])
                else:
                    import subprocess
                    subprocess.call(["xdg-open", img_path])
            else:
                if Image:
                    ImagePopup(self.master, img_path, title=filename)
                else:
                    messagebox.showwarning("依赖缺失", "查看 PNG 图片需要安装 Pillow 库。\n(pip install pillow)")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件：\n{e}")

class ModeSelectionWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title("控制模式选择")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        w, h = 400, 580
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(False, False)
        
        container = tk.Frame(self, bg=THEME["bg_window"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(container, text="请选择要模拟的控制模式", 
                 font=("Microsoft YaHei UI", 12, "bold"), fg=THEME["title_fg"], bg=THEME["bg_window"]).pack(pady=(0, 15))

        grid_frame = tk.Frame(container, bg=THEME["bg_window"])
        grid_frame.pack(fill="both", expand=True)

        btn_state = RoundedButton(grid_frame, text="状态机视图 (State Machine)", 
                            command=self.open_diagram_selector, 
                            width=360, height=35, corner_radius=8,
                            bg_normal=THEME["pill_on_bg"], bg_hover="#36bd55", 
                            fg_color="white", outer_bg=THEME["bg_window"], font_size=10)
        btn_state.pack(pady=(0, 10))

        for mode_id in range(1, 9):
            name = MODE_NAMES.get(mode_id, f"Mode {mode_id}")
            cmd = lambda m=mode_id: self.open_result_window(m)
            btn = RoundedButton(grid_frame, text=name, command=cmd, 
                                width=360, height=35, corner_radius=8,
                                bg_normal=THEME["input_bg"], bg_hover=THEME["pill_on_bg"], 
                                fg_color="white", outer_bg=THEME["bg_window"], font_size=10)
            btn.pack(pady=4)

        self.deiconify()

    def open_result_window(self, mode_id):
        ModeResultWindow(self.master, mode_id)
        self.destroy()

    def open_diagram_selector(self):
        StateDiagramSelectionWindow(self)

class TelegramTableWindow(tk.Toplevel):
    def __init__(self, parent, telegram_id):
        super().__init__(parent)
        self.withdraw()
        
        # --- 1. 基础窗口设置 ---
        self.cfg = TELEGRAM_DATA.get(telegram_id, {})
        title = self.cfg.get("title", f"报文 {telegram_id}")
        self.title(title)
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        # 调整窗口大小 (宽度加宽以容纳更多内容，高度适中)
        w, h = 980, 680
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # --- 2. 布局容器 ---
        # 顶部留一点边距，内容居中或靠上
        self.container = tk.Frame(self, bg=THEME["bg_window"])
        self.container.pack(fill="both", expand=True, padx=25, pady=25)

        # --- 3. 字体与颜色定义 ---
        self.header_bg = THEME["bg_header"]       
        self.header_fg = THEME["title_fg"]        
        self.sub_header_bg = "#2c313c"            
        self.sub_header_fg = "#ffffff"            
        self.data_bg_1 = THEME["bg_panel"]    
        self.data_bg_2 = THEME["bg_window"]   
        self.bold_font = ("Microsoft YaHei UI", 10, "bold")
        self.norm_font = ("Microsoft YaHei UI", 10)

        # --- 4. 绘制分发 ---
        if telegram_id == "1":
            self.draw_common_header(rows=6)
            self.draw_simple_data()
        elif telegram_id == "3":
            self.draw_common_header(rows=11)
            self.draw_3_layout()
        elif telegram_id == "102":
            self.draw_common_header(rows=12)
            self.draw_102_layout()
        elif telegram_id == "105":
            self.draw_common_header(rows=12)
            self.draw_105_layout()
        elif telegram_id == "111":
            self.draw_common_header(rows=16)
            self.draw_111_layout()
        elif telegram_id == "352":
            self.draw_common_header(rows=10)
            self.draw_simple_data()
            
        # --- 5. [核心修改] 优化列宽配置 ---
        # 这一步放在绘制之后执行，确保覆盖掉之前的配置
        # Col 0: 标题列 (固定宽度，不拉伸)
        self.container.columnconfigure(0, weight=0, minsize=110)   
        # Col 1: 控制器->驱动器 信号 (较窄)
        self.container.columnconfigure(1, weight=1, minsize=130)  
        # Col 2: 控制器->驱动器 说明 (较宽)
        self.container.columnconfigure(2, weight=3, minsize=200)  
        # Col 3: 驱动器->控制器 信号 (较窄)
        self.container.columnconfigure(3, weight=1, minsize=130)  
        # Col 4: 驱动器->控制器 说明 (较宽)
        self.container.columnconfigure(4, weight=3, minsize=200)  
            
        self.deiconify()

    def create_cell(self, row, col, text, rowspan=1, columnspan=1, bg_color=None, fg_color=None, font_style=None):
        """辅助函数：创建一个带边框的单元格"""
        if bg_color is None: bg_color = self.data_bg_1
        if fg_color is None: fg_color = THEME["text_main"]
        if font_style is None: font_style = self.norm_font
        border_color = THEME["border"]

        frame = tk.Frame(self.container, bg=border_color, padx=1, pady=1)
        frame.grid(row=row, column=col, rowspan=rowspan, columnspan=columnspan, sticky="nsew")
        
        # 增加 ipadx/ipady 让文字不贴边，增加行高舒适度
        lbl = tk.Label(frame, text=text, bg=bg_color, fg=fg_color, font=font_style, wraplength=190)
        lbl.pack(fill="both", expand=True, ipadx=5, ipady=4) 
        return lbl

    def draw_common_header(self, rows):
        """绘制顶部 4 行信息"""
        info = self.cfg.get("info", {})
        
        # Row 0
        self.create_cell(0, 0, "报文类型", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(0, 1, info.get("type",""), columnspan=4, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)
        
        # Row 1
        self.create_cell(1, 0, "控制模式", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(1, 1, info.get("mode",""), columnspan=4, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)
        
        # Row 2
        self.create_cell(2, 0, "应用等级", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(2, 1, info.get("class",""), columnspan=4, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)
        
        # Row 3
        self.create_cell(3, 0, "数量", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(3, 1, info.get("qty_out",""), columnspan=2, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)
        self.create_cell(3, 3, info.get("qty_in",""), columnspan=2, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)

        # Row 4-5
        self.create_cell(4, 0, "过程数据", rowspan=2, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(4, 1, "控制器 → 驱动器", columnspan=2, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)
        self.create_cell(4, 3, "驱动器 → 控制器", columnspan=2, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)

        titles = ["信号", "说明", "信号", "说明"]
        for i, t in enumerate(titles):
            self.create_cell(5, 1+i, t, bg_color=self.sub_header_bg, fg_color=self.sub_header_fg, font_style=self.bold_font)

        # [修改] 移除了 rowconfigure 循环，防止行高被强制拉伸

    def draw_simple_data(self):
        """适用于 1, 352"""
        data = self.cfg.get("data", [])
        for idx, row_data in enumerate(data):
            r = 6 + idx
            self.create_cell(r, 0, row_data[0], bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
            bg = self.data_bg_1 if idx % 2 == 0 else self.data_bg_2
            for i in range(1, 5):
                self.create_cell(r, i, row_data[i], bg_color=bg)

    def draw_111_layout(self):
        """111 报文布局"""
        data = self.cfg.get("data", [])
        for idx, row_data in enumerate(data):
            r = 6 + idx
            self.create_cell(r, 0, row_data[0], bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
            bg = self.data_bg_1 if idx % 2 == 0 else self.data_bg_2
            for i in range(1, 5):
                self.create_cell(r, i, row_data[i], bg_color=bg)

    def draw_3_layout(self):
        """标准 3 号报文"""
        # PZD1
        self.create_cell(6, 0, "PZD1", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(6, 1, "STW1", bg_color=self.data_bg_1)
        self.create_cell(6, 2, "控制字 1", bg_color=self.data_bg_1)
        self.create_cell(6, 3, "ZSW1", bg_color=self.data_bg_1)
        self.create_cell(6, 4, "状态字 1", bg_color=self.data_bg_1)

        # PZD2-3 (Merged)
        self.create_cell(7, 0, "PZD2\nPZD3", rowspan=2, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(7, 1, "NSOLL_B", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 2, "转速设定值 B (32 位)", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 3, "NIST_B", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 4, "转速实际值 B (32 位)", rowspan=2, bg_color=self.data_bg_2)

        # PZD4
        self.create_cell(9, 0, "PZD4", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(9, 1, "STW2", bg_color=self.data_bg_1)
        self.create_cell(9, 2, "控制字 2", bg_color=self.data_bg_1)
        self.create_cell(9, 3, "ZSW2", bg_color=self.data_bg_1)
        self.create_cell(9, 4, "状态字 2", bg_color=self.data_bg_1)

        # PZD5
        self.create_cell(10, 0, "PZD5", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(10, 1, "G1_STW", bg_color=self.data_bg_2)
        self.create_cell(10, 2, "编码器 1 控制字", bg_color=self.data_bg_2)
        self.create_cell(10, 3, "G1_ZSW", bg_color=self.data_bg_2)
        self.create_cell(10, 4, "编码器 1 状态字", bg_color=self.data_bg_2)

        # PZD6-9
        self.create_cell(11, 0, "PZD6\nPZD7\nPZD8\nPZD9", rowspan=4, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(11, 1, "无", rowspan=4, bg_color=self.data_bg_1)
        self.create_cell(11, 2, "无", rowspan=4, bg_color=self.data_bg_1)
        
        self.create_cell(11, 3, "G1_XIST1", rowspan=2, bg_color=self.data_bg_1)
        self.create_cell(11, 4, "增量位置", rowspan=2, bg_color=self.data_bg_1)
        
        self.create_cell(13, 3, "G1_XIST2", rowspan=2, bg_color=self.data_bg_1)
        self.create_cell(13, 4, "绝对位置和编码器故障码", rowspan=2, bg_color=self.data_bg_1)

    def draw_102_layout(self):
        """102 报文"""
        # PZD1
        self.create_cell(6, 0, "PZD1", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(6, 1, "STW1", bg_color=self.data_bg_1)
        self.create_cell(6, 2, "控制字 1", bg_color=self.data_bg_1)
        self.create_cell(6, 3, "ZSW1", bg_color=self.data_bg_1)
        self.create_cell(6, 4, "状态字 1", bg_color=self.data_bg_1)

        # PZD2-3
        self.create_cell(7, 0, "PZD2\nPZD3", rowspan=2, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(7, 1, "NSOLL_B", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 2, "转速设定值 B (32 位)", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 3, "NIST_B", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 4, "转速实际值 B (32 位)", rowspan=2, bg_color=self.data_bg_2)

        # PZD4
        self.create_cell(9, 0, "PZD4", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(9, 1, "STW2", bg_color=self.data_bg_1)
        self.create_cell(9, 2, "控制字 2", bg_color=self.data_bg_1)
        self.create_cell(9, 3, "ZSW2", bg_color=self.data_bg_1)
        self.create_cell(9, 4, "状态字 2", bg_color=self.data_bg_1)
        
        # PZD5
        self.create_cell(10, 0, "PZD5", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(10, 1, "MOMRED", bg_color=self.data_bg_2)
        self.create_cell(10, 2, "扭矩减速", bg_color=self.data_bg_2)
        self.create_cell(10, 3, "MELDW", bg_color=self.data_bg_2)
        self.create_cell(10, 4, "消息字", bg_color=self.data_bg_2)

        # PZD6
        self.create_cell(11, 0, "PZD6", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(11, 1, "G1_STW", bg_color=self.data_bg_1)
        self.create_cell(11, 2, "编码器 1 控制字", bg_color=self.data_bg_1)
        self.create_cell(11, 3, "G1_ZSW", bg_color=self.data_bg_1)
        self.create_cell(11, 4, "编码器 1 状态字", bg_color=self.data_bg_1)

        # PZD7-10
        self.create_cell(12, 0, "PZD7\nPZD8\nPZD9\nPZD10", rowspan=4, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(12, 1, "无", rowspan=4, bg_color=self.data_bg_2)
        self.create_cell(12, 2, "无", rowspan=4, bg_color=self.data_bg_2)

        self.create_cell(12, 3, "G1_XIST1", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(12, 4, "增量位置", rowspan=2, bg_color=self.data_bg_2)
        
        self.create_cell(14, 3, "G1_XIST2", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(14, 4, "绝对位置和编码器故障码", rowspan=2, bg_color=self.data_bg_2)

    def draw_105_layout(self):
        """105 报文"""
        # PZD1
        self.create_cell(6, 0, "PZD1", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(6, 1, "STW1", bg_color=self.data_bg_1)
        self.create_cell(6, 2, "控制字 1", bg_color=self.data_bg_1)
        self.create_cell(6, 3, "ZSW1", bg_color=self.data_bg_1)
        self.create_cell(6, 4, "状态字 1", bg_color=self.data_bg_1)

        # PZD2-3
        self.create_cell(7, 0, "PZD2\nPZD3", rowspan=2, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(7, 1, "NSOLL_B", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 2, "转速设定值 B (32 位)", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 3, "NIST_B", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(7, 4, "转速实际值 B (32 位)", rowspan=2, bg_color=self.data_bg_2)

        # PZD4
        self.create_cell(9, 0, "PZD4", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(9, 1, "STW2", bg_color=self.data_bg_1)
        self.create_cell(9, 2, "控制字 2", bg_color=self.data_bg_1)
        self.create_cell(9, 3, "ZSW2", bg_color=self.data_bg_1)
        self.create_cell(9, 4, "状态字 2", bg_color=self.data_bg_1)

        # PZD5
        self.create_cell(10, 0, "PZD5", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(10, 1, "MOMRED", bg_color=self.data_bg_2)
        self.create_cell(10, 2, "扭矩减速", bg_color=self.data_bg_2)
        self.create_cell(10, 3, "MELDW", bg_color=self.data_bg_2)
        self.create_cell(10, 4, "消息字", bg_color=self.data_bg_2)

        # PZD6
        self.create_cell(11, 0, "PZD6", bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(11, 1, "G1_STW", bg_color=self.data_bg_1)
        self.create_cell(11, 2, "编码器 1 控制字", bg_color=self.data_bg_1)
        self.create_cell(11, 3, "G1_ZSW", bg_color=self.data_bg_1)
        self.create_cell(11, 4, "编码器 1 状态字", bg_color=self.data_bg_1)

        # PZD7-8
        self.create_cell(12, 0, "PZD7\nPZD8", rowspan=2, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(12, 1, "XERR", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(12, 2, "位置偏差值", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(12, 3, "G1_XIST1", rowspan=2, bg_color=self.data_bg_2)
        self.create_cell(12, 4, "增量位置", rowspan=2, bg_color=self.data_bg_2)

        # PZD9-10
        self.create_cell(14, 0, "PZD9\nPZD10", rowspan=2, bg_color=self.header_bg, fg_color=self.header_fg, font_style=self.bold_font)
        self.create_cell(14, 1, "KPC", rowspan=2, bg_color=self.data_bg_1)
        self.create_cell(14, 2, "位置调节器增益", rowspan=2, bg_color=self.data_bg_1)
        self.create_cell(14, 3, "G1_XIST2", rowspan=2, bg_color=self.data_bg_1)
        self.create_cell(14, 4, "绝对位置和编码器故障码", rowspan=2, bg_color=self.data_bg_1)

class TelegramSelectionWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title("选择报文类型")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        # 增加高度以容纳更多按钮
        w, h = 350, 520 
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(False, False)
        
        container = tk.Frame(self, bg=THEME["bg_window"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(container, text="请选择要查看的报文", 
                 font=("Microsoft YaHei UI", 12, "bold"), fg=THEME["title_fg"], bg=THEME["bg_window"]).pack(pady=(0, 15))

        # 排序：1, 3, 102, 105, 111, 352
        telegram_list = [
            ("标准 1 号报文", "1"),
            ("标准 3 号报文", "3"),
            ("西门子 102 报文", "102"),
            ("西门子 105 报文", "105"),
            ("西门子 111 报文", "111"),
            ("西门子 352 报文", "352")
        ]

        for name, t_id in telegram_list:
            cmd = lambda tid=t_id: self.open_table(tid)
            btn = RoundedButton(container, text=name, command=cmd, 
                                width=310, height=40, corner_radius=10,
                                bg_normal=THEME["input_bg"], bg_hover=THEME["pill_on_bg"], 
                                fg_color="white", outer_bg=THEME["bg_window"], font_size=10)
            btn.pack(pady=6)
            
        self.deiconify()
        
    def open_table(self, telegram_id):
        TelegramTableWindow(self.master, telegram_id)
        self.destroy()

class ProDriveDashboard(tk.Toplevel):

    def open_draw_tool(self):
        try:
            # 判断是否为打包后的 exe 环境 (PyInstaller 会设置 sys.frozen)
            if getattr(sys, 'frozen', False):
                # 获取当前 exe 所在的目录
                base_path = os.path.dirname(sys.executable)
                # 设定目标 exe 路径 (假设 draw.exe 和主程序在同一目录下)
                exe_path = os.path.join(base_path, 'draw.exe')
                
                if os.path.exists(exe_path):
                    # 启动外部 exe，不等待其结束
                    subprocess.Popen([exe_path])
                else:
                    messagebox.showerror("文件缺失", f"未找到波形分析工具：\n{exe_path}\n请确保 draw.exe 与主程序在同一目录下。")
            else:
                # 源代码运行模式 (保持原样)
                current_dir = os.path.dirname(os.path.abspath(__file__))
                script_path = os.path.join(current_dir, 'draw.py')
                if os.path.exists(script_path):
                    subprocess.Popen([sys.executable, script_path])
                else:
                    messagebox.showerror("错误", "找不到 draw.py")

        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动工具：\n{str(e)}")

    def __init__(self, master=None):
        super().__init__(master)
        self.withdraw() 
        self.title("PROFINET Drive Monitor")
        set_window_icon(self)
        self.configure(bg=THEME["bg_window"])
        
        self.vars = {} 

        self.panel_configs = {
            "STW1": {
                "title": "STW1", "icon": "⚙️", 
                "texts": [
                    "OFF1 减速停机↑", "OFF2 自由停机", "OFF3 紧急停机", "允许运行", 
                    "不拒绝任务", "不暂停任务", "激活运行任务↑", "复位故障↑", 
                    "JOG1 点动", "JOG2 点动", "PLC 控制", "开始回原点", 
                    "保留", "外部程序段切换↑", "切换至转矩模式", "保留"
                ]
            },
            "POS_STW1": {
                "title": "POS_STW1 ", "icon": "⚙️", 
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
                "title": "STW2 ", "icon": "⚙️", 
                "texts": [
                    "保留", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "保留", 
                    "运行至固定停止点", "保留", "保留", "保留", 
                    "主站心跳 Bit0", "主站心跳 Bit1", "主站心跳 Bit2", "主站心跳 Bit3"
                ]
            },
            "ZSW1": {
                "title": "ZSW1 ", "icon": "⚙️", 
                "texts": [
                    "准备开启", "准备就绪", "运行使能", "有故障", 
                    "OFF2 无效", "OFF3 无效", "禁止接通", "有报警", 
                    "无位置偏差故障", "PLC 控制请求", "到达目标位置", "已完成回参考点", 
                    "程序段应答", "驱动器静止", "转矩控制有效", "保留"
                ]
            },
            "ZSW2": {
                "title": "ZSW2 ", "icon": "⚙️", 
                "texts": [
                    "保留", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "保留", 
                    "运行至固定停止点", "保留", "保留", "保留", 
                    "生命信号 Bit0", "生命信号 Bit1", "生命信号 Bit2", "生命信号 Bit3"
                ]
            },
            "POS_ZSW1": {
                "title": "POS_ZSW1 ", "icon": "⚙️", 
                "texts": [
                    ("激活程序段0-15(Bit0-3)", 4), None, None, None, 
                    "保留", "保留", "保留", "保留", 
                    "负向硬限位触发", "正向硬限位触发", "JOG 模式激活", "回原模式激活", 
                    "保留", "程序段模式激活", "保留", "MDI 模式激活"
                ]
            },
            "POS_ZSW2": {
                "title": "POS_ZSW2", "icon": "⚙️", 
                "texts": [
                    "保留", "到达速度限制", "保留", "保留", 
                    "轴正向移动", "轴负向移动", "负向软限位触发", "正向软限位触发", 
                    "保留", "保留", "保留", "保留", 
                    "到达固定停止点", "达到夹紧转矩", "固定停止点功能激活", "保留"
                ]
            },
            "MELDW": {
                "title": "MELDW ", "icon": "⚙️", 
                "texts": [
                    "保留", "未到达转矩限制", "保留", "保留", 
                    "保留", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "驱动器使能", 
                    "运行准备好", "驱动器运行", "保留", "保留"
                ]
            },
            "EposALWord Lo": {
                "title": "EposALWord Lo", "icon": "⚙️", 
                "texts": [
                    "MDI触发位", "多段触发位", "Home触发 关联STW1.11", "Jog1触发位", 
                    "Jog2触发位", "保留", "任务取消位", "任务暂停位", 
                    "Jog模式 0速度/1位置", "位置到达标志", "Home完成", "参考点已设置P01.90", 
                    "上电后编码器初始化完成", "MDI触发 0手动/1连续", "正向硬件限位状态", "负向硬件限位状态"
                ]
            },
            "EposALWord Ho": {
                "title": "EposALWord Ho", "icon": "⚙️", 
                "texts": [
                    "最小软件限位状态", "最大软件限位状态", ("轴实际方向 0停1正2负", 2), None, 
                    "到达速度限值标志", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "保留", 
                    "保留", "保留", "保留", "保留"
                ]
            }
        }
        
        self.visible_keys = ["STW1", "ZSW1", "POS_STW1", "POS_STW2"] 
        self.panels = {}
        
        self.container = tk.Frame(self, bg=THEME["bg_window"])
        self.container.pack(fill="both", expand=True, padx=8, pady=8)
        
        # --- 底部按钮布局修改 ---
        self.footer = tk.Frame(self, bg=THEME["bg_window"])
        self.footer.pack(fill="x", side="bottom", padx=15, pady=(0, 15))
        
        # 左侧容器 (存放 模式选择 和 报文选择)
        left_btn_frame = tk.Frame(self.footer, bg=THEME["bg_window"])
        left_btn_frame.pack(side="left")

        self.btn_mode = RoundedButton(left_btn_frame, text="模式选择", command=self.open_mode_dialog, 
                                        width=100, height=35, bg_normal=THEME["input_bg"], bg_hover=THEME["pill_on_bg"], 
                                        fg_color='white', outer_bg=THEME["bg_window"])
        self.btn_mode.pack(side="left", padx=(0, 10))

        # [新增] 报文选择按钮
        self.btn_telegram = RoundedButton(left_btn_frame, text="报文选择", command=self.open_telegram_dialog, 
                                        width=100, height=35, bg_normal=THEME["input_bg"], bg_hover=THEME["pill_on_bg"], 
                                        fg_color='white', outer_bg=THEME["bg_window"])
        self.btn_telegram.pack(side="left")

        self.btn_draw = RoundedButton(left_btn_frame, text="波形分析器", command=self.open_draw_tool, 
                                        width=100, height=35, bg_normal=THEME["input_bg"], bg_hover=THEME["pill_on_bg"], 
                                        fg_color='white', outer_bg=THEME["bg_window"])
        self.btn_draw.pack(side="left", padx=(10, 0)) # 左侧增加一点间距

        self.btn_switch = RoundedButton(self.footer, text="显示切换", command=self.open_selection_dialog, 
                                        width=100, height=35, bg_normal='#EBCB8B', bg_hover='#D0B075', 
                                        fg_color='#2E3440', outer_bg=THEME["bg_window"])
        self.btn_switch.pack(side="right")

        self.refresh_panels()
        self.center_window(1100, 620)
        self.deiconify()

    def open_selection_dialog(self):
        SelectionWindow(self, self.panel_configs, self.visible_keys, self.update_visible_panels)

    def open_mode_dialog(self):
        ModeSelectionWindow(self)
        
    def open_telegram_dialog(self):
        TelegramSelectionWindow(self)

    def update_visible_panels(self, new_selection):
        self.visible_keys = new_selection
        self.vars.clear() 
        self.refresh_panels()

    def refresh_panels(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.panels.clear()
        
        target_list = [{'key': k, 'title': self.panel_configs[k]['title'], 'val': 0} for k in self.visible_keys[:4]]

        for i in range(len(target_list)):
            self.container.columnconfigure(i, weight=1)
            
        for idx, item in enumerate(target_list):
            key = item['key']
            title = item['title']
            init_val = item.get('val', 0)
            
            var_key = f"{key}_MAIN_{idx}" 
            if var_key not in self.vars:
                self.vars[var_key] = tk.StringVar(value=str(init_val))
            else:
                self.vars[var_key].set(str(init_val))
                
            cfg = self.panel_configs[key]
            
            p = PanelColumn(self.container, title, self.vars[var_key], cfg["texts"], cfg["icon"], entry_width=90)
            
            p.grid(row=0, column=idx, sticky="nsew", padx=2)
            self.panels[var_key] = p

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