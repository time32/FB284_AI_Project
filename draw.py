import sys
import os
import pandas as pd
import numpy as np
import pyqtgraph as pg
import ctypes 
import time
from io import StringIO
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QDoubleSpinBox, QCheckBox, QMessageBox, QFrame, 
                             QStyleFactory, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMenu, QAction, QDialog, QComboBox, 
                             QListWidget, QGroupBox, QGridLayout, QFormLayout, 
                             QDialogButtonBox, QAbstractItemView, QListView)

from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QBrush, QPainter, QPen, QCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF, QPointF

# === [新增] 导入 Word COM 接口库 ===
try:
    import win32com.client as win32
    import pythoncom
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("提示: 未检测到 pywin32 库，Word 解密读取功能将不可用。建议执行: pip install pywin32")

# === 1. 图标资源配置 ===
ICON_FILE = 'svg_code_to_png.ico'

def resource_path(relative_path):
    base_path = os.path.abspath('.') 
    full_path = os.path.join(base_path, relative_path)
    if not os.path.exists(full_path):
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, relative_path)
    return full_path

def set_window_icon(target_obj):
    try:
        icon_path = resource_path(ICON_FILE)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            target_obj.setWindowIcon(icon)
            return icon
    except Exception:
        pass

# === Windows 任务栏图标修复 ===
try:
    myappid = 'mycompany.oscilloscope.pro.final_v26_XY_measure'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# === 全局配置 ===
pg.setConfigOptions(antialias=False) 
pg.setConfigOption('background', '#000000') 
pg.setConfigOption('foreground', '#DCDFE4') 

WAVE_COLORS = ['#98C379', '#E06C75', '#E5C07B', '#61AFEF', '#C678DD', '#56B6C2', '#D19A66', '#ABB2BF']
MAX_RENDER_POINTS = 200000

# === 新增：智能坐标轴 (支持 Hex 显示) ===
class SmartAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fmt = 'dec' 

    def set_format(self, fmt):
        self.fmt = fmt
        self.picture = None 
        self.update()

    def tickStrings(self, values, scale, spacing):
        if self.fmt == 'hex':
            return [f"0x{int(v):X}" for v in values]
        return super().tickStrings(values, scale, spacing)

# === 加载动画控件 ===
class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents) 
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.text = "处理中..."
        self.hide()

    def rotate(self):
        self.angle = (self.angle + 15) % 360
        self.update()

    def start(self, msg="处理中..."):
        self.text = msg
        self.angle = 0
        self.timer.start(30) 
        self.show()
        self.raise_() 

    def stop(self):
        self.timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        w, h = self.width(), self.height()
        center_x, center_y = w // 2, h // 2
        radius = 35
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)
        pen = QPen(QColor('#61AFEF'))
        pen.setWidth(6)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(QRectF(-radius, -radius, radius*2, radius*2), 0, 300 * 16)
        painter.rotate(-self.angle)
        painter.translate(-center_x, -center_y)
        font = QFont("Microsoft YaHei UI", 12, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor('white'))
        text_rect = QRectF(0, center_y + 50, w, 40)
        painter.drawText(text_rect, Qt.AlignCenter, self.text)

    def resizeEvent(self, event):
        if self.parent(): self.resize(self.parent().size())
        super().resizeEvent(event)

# === 高级合并管理器 ===
class MergeManagerDialog(QDialog):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据合并配置")
        self.resize(550, 480)
        self.df = df
        self.pending_merges = [] 
        self.removed_cols = []   
        self.source_cols = list(df.columns)
        
        self.setStyleSheet("""
            QDialog { background-color: #282C34; color: #DCDFE4; font-family: "Microsoft YaHei UI"; }
            QGroupBox {
                border: 1px solid #3B4048; border-radius: 6px; margin-top: 24px; font-weight: bold; color: #E5C07B;
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 5px; }
            QLabel { color: #ABB2BF; font-size: 13px; font-weight: normal; }
            QComboBox { background-color: #21252B; border: 1px solid #3B4048; border-radius: 4px; padding: 5px 10px; color: #DCDFE4; min-height: 20px; }
            QComboBox:hover { border: 1px solid #61AFEF; }
            QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left-width: 0px; }
            QComboBox QAbstractItemView { background-color: #21252B; border: 1px solid #3B4048; color: #DCDFE4; selection-background-color: #3E4451; }
            QListWidget { background-color: #21252B; border: 1px solid #3B4048; border-radius: 6px; color: #98C379; font-family: Consolas, "Microsoft YaHei"; padding: 5px; outline: none; }
            QListWidget::item { padding: 5px; border-bottom: 1px solid #2C313A; }
            QListWidget::item:selected { background-color: #3E4451; color: #FFFFFF; }
            QPushButton { border: none; border-radius: 4px; padding: 6px 15px; font-weight: bold; font-size: 12px; }
            QPushButton#BtnAdd { background-color: #98C379; color: #282C34; }
            QPushButton#BtnAdd:hover { background-color: #B3D69B; }
            QPushButton#BtnRemove { background-color: #21252B; color: #E06C75; border: 1px solid #E06C75; }
            QPushButton#BtnRemove:hover { background-color: #E06C75; color: white; }
            QPushButton#BtnOK { background-color: #61AFEF; color: #282C34; }
            QPushButton#BtnOK:hover { background-color: #82C2F5; }
            QPushButton#BtnCancel { background-color: #3B4048; color: #DCDFE4; }
            QPushButton#BtnCancel:hover { background-color: #4B5263; }
        """)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        grp_new = QGroupBox("新增合并规则 (Signed 32-bit)")
        grp_layout = QGridLayout(grp_new)
        grp_layout.setContentsMargins(15, 25, 15, 15)
        grp_layout.setVerticalSpacing(15)
        
        lbl_h = QLabel("高16位 (High Word):")
        self.cb_high = QComboBox()
        self.cb_high.setView(QListView()) 
        self.cb_high.addItems(self.source_cols)
        grp_layout.addWidget(lbl_h, 0, 0)
        grp_layout.addWidget(self.cb_high, 0, 1)
        
        lbl_l = QLabel("低16位 (Low Word):")
        self.cb_low = QComboBox()
        self.cb_low.setView(QListView()) 
        self.cb_low.addItems(self.source_cols)
        if len(self.source_cols) > 1: self.cb_low.setCurrentIndex(1)
        grp_layout.addWidget(lbl_l, 1, 0)
        grp_layout.addWidget(self.cb_low, 1, 1)
        
        self.btn_add = QPushButton("⬇  生成并添加到列表")
        self.btn_add.setObjectName("BtnAdd")
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self.add_merge_task)
        grp_layout.addWidget(self.btn_add, 2, 0, 1, 2)
        
        main_layout.addWidget(grp_new)

        lbl_list = QLabel("待处理任务队列:")
        lbl_list.setStyleSheet("color: #E5C07B; font-weight: bold; margin-top: 5px;")
        main_layout.addWidget(lbl_list)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(False)
        main_layout.addWidget(self.list_widget)

        bot_layout = QHBoxLayout()
        bot_layout.setContentsMargins(0, 10, 0, 0)
        
        self.btn_remove = QPushButton("移除选中项")
        self.btn_remove.setObjectName("BtnRemove")
        self.btn_remove.setCursor(Qt.PointingHandCursor)
        self.btn_remove.clicked.connect(self.remove_merge_task)
        bot_layout.addWidget(self.btn_remove)
        
        bot_layout.addStretch()
        
        self.btn_cancel = QPushButton("取 消")
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.setFixedSize(80, 32)
        self.btn_cancel.clicked.connect(self.reject)
        bot_layout.addWidget(self.btn_cancel)

        self.btn_ok = QPushButton("应用合并")
        self.btn_ok.setObjectName("BtnOK")
        self.btn_ok.setFixedSize(100, 32)
        self.btn_ok.clicked.connect(self.accept)
        bot_layout.addWidget(self.btn_ok)
        
        main_layout.addLayout(bot_layout)
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        for col in self.df.columns:
            if col.startswith("M_") and col not in self.removed_cols:
                self.list_widget.addItem(f"🔗 [已存在] {col}")
        for name, h, l in self.pending_merges:
            self.list_widget.addItem(f"✨ [新添加] {name}")

    def add_merge_task(self):
        h = self.cb_high.currentText()
        l = self.cb_low.currentText()
        if h == l:
            QMessageBox.warning(self, "逻辑错误", "高位和低位不能选择同一列数据！")
            return
        name = f"M_{l}"
        if name in self.df.columns and name not in self.removed_cols:
            QMessageBox.information(self, "提示", "该合并列已存在，无需重复添加。")
            return
        for n, _, _ in self.pending_merges:
            if n == name: return
        self.pending_merges.append((name, h, l))
        if name in self.removed_cols: self.removed_cols.remove(name)
        self.refresh_list()
        self.list_widget.scrollToBottom()

    def remove_merge_task(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        item_text = self.list_widget.item(row).text()
        if "[新添加]" in item_text:
            idx = -1
            target = item_text.replace("✨ [新添加] ", "").strip()
            for i, (n, h, l) in enumerate(self.pending_merges):
                if n == target: idx = i; break
            if idx != -1: self.pending_merges.pop(idx)
        elif "[已存在]" in item_text:
            self.removed_cols.append(item_text.replace("🔗 [已存在] ", "").strip())
        self.refresh_list()

class CustomViewBox(pg.ViewBox):
    sigDragEvent = pyqtSignal(object, object)
    sigRightClickDouble = pyqtSignal() 
    sigRightClick = pyqtSignal(object) 
    sigZoomEvent = pyqtSignal(float, object)
    sigRectZoom = pyqtSignal(float, float) 

    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.setMouseMode(self.RectMode)
        self._click_timer = QTimer()
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(300) 
        self._click_timer.timeout.connect(self._emit_single_click)
        self._last_screen_pos = None

    def _emit_single_click(self):
        if self._last_screen_pos:
            self.sigRightClick.emit(self._last_screen_pos)
            self._last_screen_pos = None

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.RightButton:
            ev.accept() 
            self._last_screen_pos = ev.screenPos()
            self._click_timer.start()
        else:
            super().mouseClickEvent(ev)
    
    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.RightButton:
            ev.accept()
            self._click_timer.stop()
            self._last_screen_pos = None
            self.sigRightClickDouble.emit() 
        else:
            super().mouseDoubleClickEvent(ev)
            
    def mouseDragEvent(self, ev, axis=None):
        if ev.button() == Qt.RightButton:
            ev.accept()
            self.sigDragEvent.emit(ev.pos(), ev.lastPos())
        else:
            if ev.isFinish():
                pre_range = self.viewRange()[1]
                self.setMouseMode(self.RectMode)
                super().mouseDragEvent(ev, axis=axis)
                post_range = self.viewRange()[1]
                y_span = pre_range[1] - pre_range[0]
                if y_span != 0:
                    rel_min = (post_range[0] - pre_range[0]) / y_span
                    rel_max = (post_range[1] - pre_range[0]) / y_span
                    self.sigRectZoom.emit(rel_min, rel_max)
            else:
                self.setMouseMode(self.RectMode)
                super().mouseDragEvent(ev, axis=axis)

    def wheelEvent(self, ev, axis=None):
        ev.accept()
        delta = ev.delta() 
        if delta > 0:
            scale_factor = 1.0 / 1.15
        else:
            scale_factor = 1.15
        self.sigZoomEvent.emit(scale_factor, ev.scenePos())

    def suggestPadding(self, axis):
        if axis == 1: return 0.1 
        return 0.0

class FileLoaderThread(QThread):
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def _read_via_word_chunked(self, file_path):
        """ 
        优化版：
        1. 细化了加载状态提示，让你知道程序卡在哪一步。
        2. 禁用了 Word 的拼写/语法检查，加速大文件打开。
        3. 保持分块读取和进度条功能。
        """
        word_app = None
        doc = None
        temp_save_path = file_path + "_decrypted.txt"
        CHUNK_SIZE = 50000 

        try:
            # --- 步骤 1: 启动 Word ---
            self.info_signal.emit("正在启动引擎...")
            pythoncom.CoInitialize()
            word_app = win32.DispatchEx("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = False
            
            # [关键优化] 禁用拼写和语法检查，显著提高打开大文件的速度
            word_app.Options.CheckSpellingAsYouType = False
            word_app.Options.CheckGrammarAsYouType = False
            word_app.Options.CheckGrammarWithSpelling = False

            # --- 步骤 2: 打开文件 (最耗时的一步) ---
            file_abs_path = os.path.abspath(file_path)
            file_size_mb = os.path.getsize(file_abs_path) / (1024 * 1024)
            
            # 根据文件大小给出不同提示
            if file_size_mb > 50:
                self.info_signal.emit(f"正在载入大文件 ({file_size_mb:.1f}MB)，请耐心等待...")
            else:
                self.info_signal.emit("正在打开文件...")

            # 这里是阻塞的，Word 正在解析文件，程序会在此暂停直到打开完成
            doc = word_app.Documents.Open(
                FileName=file_abs_path, 
                ConfirmConversions=False, 
                ReadOnly=True, 
                AddToRecentFiles=False
            )
            
            # --- 步骤 3: 准备读取 ---
            self.info_signal.emit("文件打开成功，正在分析结构...")
            total_chars = doc.Content.End
            
            # --- 步骤 4: 分块解密 ---
            with open(temp_save_path, 'w', encoding='utf-8') as f_out:
                start_index = 0
                while start_index < total_chars:
                    end_index = min(start_index + CHUNK_SIZE, total_chars)
                    
                    rng = doc.Range(Start=start_index, End=end_index)
                    chunk_text = rng.Text
                    
                    if chunk_text:
                        chunk_text = chunk_text.replace('\r', '\n').replace('\x0b', '').replace('\x00', '')
                        f_out.write(chunk_text)
                    
                    # 更新进度条
                    if total_chars > 0:
                        percent = (end_index / total_chars) * 100
                        self.info_signal.emit(f"正在解密: {int(percent)}%")
                    
                    start_index = end_index

            print(f"[+] 解密完成: {temp_save_path}")
            return temp_save_path

        except Exception as e:
            print(f"[!] Word 处理失败: {e}")
            if os.path.exists(temp_save_path):
                try: os.remove(temp_save_path)
                except: pass
            return None

        finally:
            if doc:
                try: doc.Close(SaveChanges=0)
                except: pass
            if word_app:
                try: word_app.Quit()
                except: pass
            pythoncom.CoUninitialize()

    def run(self):
        temp_file_path = None
        try:
            df = None
            
            # --- 1. 尝试常规读取 ---
            try:
                df = pd.read_csv(self.file_path, encoding='utf-8', low_memory=False, engine='c')
            except Exception:
                try:
                    df = pd.read_csv(self.file_path, encoding='gbk', on_bad_lines='skip', low_memory=False, engine='c')
                except Exception:
                    pass

            # --- 2. 判断是否需要解密 ---
            # 如果读出来是空，或者列很少，说明可能被加密了
            is_invalid = (df is None) or (len(df) == 0) or (len(df.columns) < 1)
            
            if is_invalid and HAS_WIN32:
                self.info_signal.emit("常规解析失败，准备解密...")
                
                # 调用分块读取方法，直接返回生成的文件路径
                temp_file_path = self._read_via_word_chunked(self.file_path)
            
            # --- 3. 读取解密后的临时文件 ---
            # 如果 temp_file_path 存在，说明是通过 Word 解密生成的
            if temp_file_path and os.path.exists(temp_file_path):
                self.info_signal.emit("解密完成，正在加载数据...")
                try:
                    # 读取生成的临时文件
                    df = pd.read_csv(temp_file_path, sep=None, engine='python', encoding='utf-8')
                except Exception as e:
                    print(f"临时文件解析失败: {e}")
                
                # 读取完后清理临时文件
                try:
                    os.remove(temp_file_path)
                except:
                    pass

            # --- 4. 数据最终处理 ---
            if df is not None and len(df) > 0:
                # 删除全空列
                df.dropna(how='all', axis=1, inplace=True)
                # 强制转数值
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                # 压缩内存
                df = df.astype(np.float32)
                # 清理列名空格
                df.columns = df.columns.str.strip()
                
                self.finished_signal.emit(df)
            else:
                extra_msg = "" if HAS_WIN32 else "\n(未检测到 pywin32，无法使用 Word 解密)"
                raise Exception(f"无法读取文件，可能格式错误或加密无法解析。{extra_msg}")

        except Exception as e:
            self.error_signal.emit(f"加载异常: {str(e)}")
            # 异常时清理残留文件
            if temp_file_path and os.path.exists(temp_file_path):
                try: os.remove(temp_file_path)
                except: pass

# === 线程: 后台数据点优化 ===
class DotPreparerThread(QThread):
    finished_signal = pyqtSignal(dict)

    def __init__(self, df, time_axis):
        super().__init__()
        self.df = df
        self.time_axis = time_axis

    def run(self):
        try:
            dots_data = {}
            total_rows = len(self.df)
            target_points = 80000 
            step = max(1, total_rows // target_points)
            indices = np.arange(0, total_rows, step)
            x_downsampled = self.time_axis[indices]
            
            for col in self.df.columns:
                y_downsampled = self.df[col].values[indices]
                dots_data[col] = (x_downsampled, y_downsampled)
            
            self.finished_signal.emit(dots_data)
        except Exception:
            pass

# === 主窗口 ===
class ProOscilloscope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("波形分析器")
        self.adapt_to_screen()
        set_window_icon(self)
        
        font = QFont("Microsoft YaHei UI", 9)
        self.setFont(font)
        QApplication.setFont(font)

        self.apply_stylesheet()

        self.df = None
        self.time_axis = None
        self.dots_cache = None 
        self.main_vb = None 
        self.overlay_views = [] 
        self.all_views = []     
        self.trace_dict = {}
        self.col_formats = {}
        self.hidden_cols = set()
        self.df_values = None
        self.col_index_map = {}
        self.visible_cols_cache = []

        self.v_line = None
        self.h_line = None
        self.crosshair_label = None
        
        # 光标变量
        self.cursor_x1 = None 
        self.cursor_x2 = None 
        self.cursor_y1 = None
        self.cursor_y2 = None
        
        self.proxy = None 
        self.loader = None
        self.dot_worker = None

        # === UI 构建 ===
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 顶部工具栏 ===
        top_container = QFrame()
        top_container.setObjectName("TopPanel")
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(10, 5, 10, 5)
        top_layout.setSpacing(10)

        lbl_rate = QLabel("采样(ms):")
        lbl_rate.setStyleSheet("color: #ABB2BF; font-weight: bold;")
        top_layout.addWidget(lbl_rate)

        self.spin_rate = QDoubleSpinBox()
        self.spin_rate.setRange(0.001, 10000)
        self.spin_rate.setValue(2.0)
        self.spin_rate.setDecimals(3)
        self.spin_rate.setFixedWidth(70)
        self.spin_rate.valueChanged.connect(self.recalc_time)
        top_layout.addWidget(self.spin_rate)
        
        self.chk_separate = QCheckBox("分轴")
        self.chk_separate.setChecked(True) 
        self.chk_separate.toggled.connect(self.update_plot_wrapper)
        top_layout.addWidget(self.chk_separate)

        self.chk_crosshair = QCheckBox("光标")
        self.chk_crosshair.toggled.connect(self.toggle_crosshair)
        top_layout.addWidget(self.chk_crosshair)

        self.chk_measure = QCheckBox("测量")
        self.chk_measure.toggled.connect(self.toggle_measure)
        top_layout.addWidget(self.chk_measure)

        self.chk_dots = QCheckBox("数据点")
        self.chk_dots.setEnabled(False)
        self.chk_dots.toggled.connect(self.update_plot_wrapper)
        top_layout.addWidget(self.chk_dots)
        
        self.chk_antialias = QCheckBox("抗锯齿")
        self.chk_antialias.toggled.connect(self.toggle_antialias)
        top_layout.addWidget(self.chk_antialias)
                
        self.btn_merge = QPushButton("🔗 合并数据")
        self.btn_merge.clicked.connect(self.open_merge_manager)
        self.btn_merge.setStyleSheet("background-color: #98C379; color: #282C34; font-weight: bold;")
        top_layout.addWidget(self.btn_merge)
        
        top_layout.addStretch() 

        line1 = QFrame()
        line1.setFrameShape(QFrame.VLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet("border: 1px solid #3B4048;")
        top_layout.addWidget(line1)

        self.btn_reset = QPushButton("↺ 复位")
        self.btn_reset.setObjectName("BtnReset")
        self.btn_reset.clicked.connect(self.reset_views)
        top_layout.addWidget(self.btn_reset)

        self.btn_load = QPushButton("📂 导入")
        self.btn_load.clicked.connect(self.load_file)
        self.btn_load.setStyleSheet("background-color: #98C379; color: #282C34; font-weight: bold;")
        top_layout.addWidget(self.btn_load)

        main_layout.addWidget(top_container)

        # 2. 绘图区
        self.plot_layout = pg.GraphicsLayoutWidget()
        self.plot_layout.ci.layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.plot_layout)
        
        # 3. 底部图例栏
        self.legend_frame = QFrame()
        self.legend_frame.setObjectName("LegendPanel")
        
        # 改为网格布局
        self.legend_layout = QGridLayout(self.legend_frame) 
        self.legend_layout.setContentsMargins(15, 5, 15, 5)
        self.legend_layout.setHorizontalSpacing(20)
        self.legend_layout.setVerticalSpacing(5)
        self.legend_layout.setAlignment(Qt.AlignLeft)
        
        main_layout.addWidget(self.legend_frame)

        # 4. 统计表格
        self.stats_table = QTableWidget()
        self.setup_stats_table()
        main_layout.addWidget(self.stats_table)
        
        self.status_label = QLabel(" 准备就绪")
        self.status_label.setStyleSheet("color: #5C6370; font-size: 11px; padding: 2px;")
        self.statusBar().addWidget(self.status_label)
        self.statusBar().setStyleSheet("background: #21252B; border-top: 1px solid #181A1F;")

        self.loading_overlay = LoadingOverlay(self)

    def adapt_to_screen(self):
        screen_geo = QApplication.primaryScreen().availableGeometry()
        w, h = screen_geo.width(), screen_geo.height()
        target_w = min(1400, int(w * 0.95))
        target_h = min(950, int(h * 0.90))
        self.resize(target_w, target_h)
        self.move(screen_geo.x() + (w - target_w)//2, screen_geo.y() + (h - target_h)//2)

    def resizeEvent(self, event):
        self.loading_overlay.resize(self.size())
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.loader and self.loader.isRunning(): self.loader.terminate(); self.loader.wait()
        if self.dot_worker and self.dot_worker.isRunning(): self.dot_worker.terminate(); self.dot_worker.wait()
        event.accept()

    def open_merge_manager(self):
        if self.df is None:
            QMessageBox.warning(self, "提示", "请先导入数据文件！")
            return
        
        dialog = MergeManagerDialog(self.df, self)
        if dialog.exec_() == QDialog.Accepted:
            need_refresh = False
            for col in dialog.removed_cols:
                if col in self.df.columns:
                    self.df.drop(columns=[col], inplace=True)
                    if col in self.col_formats: del self.col_formats[col]
                    need_refresh = True
            
            if dialog.pending_merges:
                self.loading_overlay.start("正在计算合并数据...")
                QApplication.processEvents()
                try:
                    for name, h_col, l_col in dialog.pending_merges:
                        low_vals = self.df[l_col].fillna(0).astype(np.int64).values
                        high_vals = self.df[h_col].fillna(0).astype(np.int64).values
                        merged = (high_vals << 16) | (low_vals & 0xFFFF)
                        mask = merged >= 0x80000000
                        merged[mask] -= 0x100000000
                        self.df[name] = merged.astype(np.float32)
                        self.hidden_cols.add(h_col)
                        self.hidden_cols.add(l_col)
                    need_refresh = True
                except Exception as e:
                    self.loading_overlay.stop()
                    QMessageBox.critical(self, "合并失败", f"数据转换错误：\n{str(e)}")
                finally:
                    self.loading_overlay.stop()
            
            if need_refresh:
                self.recalc_time() 

    def rebuild_column_cache(self):
        if self.df is None:
            self.col_index_map = {}
            self.visible_cols_cache = []
            return
        self.col_index_map = {name: i for i, name in enumerate(self.df.columns)}
        self.visible_cols_cache = [
            c for c in self.df.columns if self.trace_dict.get(c, {}).get('visible', False)
        ]

    def format_val(self, col_name, val):
        if np.isnan(val): return "NaN"
        fmt = self.col_formats.get(col_name, 'dec')
        if fmt == 'hex':
            try:
                int_val = int(val)
                return f"0x{int_val & 0xFFFFFFFF:X}"
            except: return "Err"
        else:
            return f"{val:.0f}"

    def set_col_format(self, col_name, fmt):
        self.col_formats[col_name] = fmt
        self.update_stats_table()

    def setup_stats_table(self):
        cols = ["波形名称", "Ymin", "Ymax", "Y_Vpp", "Ymean", "Y1", "Y2", "ΔY"]
        self.stats_table.setColumnCount(len(cols))
        self.stats_table.setHorizontalHeaderLabels(cols)
        self.stats_table.verticalHeader().setVisible(False) 
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stats_table.setSelectionMode(QTableWidget.NoSelection)
        self.stats_table.setFixedHeight(120 if self.height() < 800 else 150)
        
        header = self.stats_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch) 
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        self.stats_table.setStyleSheet("""
            QTableWidget { background-color: #21252B; color: #DCDFE4; gridline-color: #3B4048; border-top: 1px solid #181A1F; font-family: Consolas; font-size: 12px; }
            QHeaderView::section { background-color: #282C34; color: #E5C07B; padding: 4px; border: 1px solid #181A1F; font-weight: bold; }
        """)

    def update_stats_table(self):
        if self.df is None or self.df_values is None or self.main_vb is None: return
        try:
            x_min_view, x_max_view = self.main_vb.viewRange()[0]
        except: return

        idx_start = np.searchsorted(self.time_axis, x_min_view, side='left')
        idx_end = np.searchsorted(self.time_axis, x_max_view, side='right')
        idx_start = max(0, idx_start)
        idx_end = min(len(self.df), idx_end)
        
        has_cursor_y = (self.cursor_y1 is not None and self.cursor_y2 is not None)
        y1_raw = 0
        y2_raw = 0
        
        if has_cursor_y:
            y1_raw = self.cursor_y1.value()
            y2_raw = self.cursor_y2.value()

        visible_cols = self.visible_cols_cache
        self.stats_table.setRowCount(len(visible_cols))

        for row_idx, col_name in enumerate(visible_cols):
            col_idx = self.col_index_map.get(col_name)
            if idx_start < idx_end and col_idx is not None:
                d = self.df_values[idx_start:idx_end, col_idx]
                if len(d) > 0:
                    y_min, y_max, y_mean = np.nanmin(d), np.nanmax(d), np.nanmean(d)
                    y_vpp = y_max - y_min
                else:
                    y_min = y_max = y_mean = y_vpp = 0
            else:
                y_min = y_max = y_mean = y_vpp = 0

            val_at_y1 = 0
            val_at_y2 = 0
            diff_y = 0
            
            if has_cursor_y:
                curve_item = self.trace_dict[col_name]['curve']
                target_vb = curve_item.getViewBox()
                
                if target_vb == self.main_vb:
                    val_at_y1 = y1_raw
                    val_at_y2 = y2_raw
                else:
                    pt1_scene = self.main_vb.mapViewToScene(QPointF(0, y1_raw))
                    pt2_scene = self.main_vb.mapViewToScene(QPointF(0, y2_raw))
                    pt1_view = target_vb.mapSceneToView(pt1_scene)
                    pt2_view = target_vb.mapSceneToView(pt2_scene)
                    val_at_y1 = pt1_view.y()
                    val_at_y2 = pt2_view.y()
                
                diff_y = val_at_y2 - val_at_y1

            c_idx = self.col_index_map.get(col_name, 0)
            color = QColor(WAVE_COLORS[c_idx % len(WAVE_COLORS)])
            
            item_nm = QTableWidgetItem(f"■ {col_name}")
            item_nm.setForeground(QBrush(color))
            item_nm.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
            self.stats_table.setItem(row_idx, 0, item_nm)
            
            for c, val in enumerate([y_min, y_max, y_vpp, y_mean], 1):
                it = QTableWidgetItem(self.format_val(col_name, val))
                it.setTextAlignment(Qt.AlignCenter) 
                self.stats_table.setItem(row_idx, c, it)
                
            if has_cursor_y:
                vals = [val_at_y1, val_at_y2, diff_y]
                for i, val in enumerate(vals):
                    it = QTableWidgetItem(self.format_val(col_name, val))
                    it.setTextAlignment(Qt.AlignCenter) 
                    self.stats_table.setItem(row_idx, 5 + i, it)
            else:
                for c in range(5, 8):
                    it = QTableWidgetItem("--")
                    it.setTextAlignment(Qt.AlignCenter) 
                    self.stats_table.setItem(row_idx, c, it)

    def add_legend_item(self, name, color, index, checked=True):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        cb = QCheckBox(f"■ {name}")
        cb.setChecked(checked) 
        cb.setStyleSheet(f"""
            QCheckBox {{ color: {color}; font-weight: bold; font-family: Consolas, 'Microsoft YaHei'; }}
            QCheckBox::indicator:checked {{ background: {color}; border: 1px solid {color}; }}
        """)
        cb.stateChanged.connect(lambda state, col=name: self.on_wave_toggle(state, col))
        layout.addWidget(cb)

        btn_fmt = QPushButton("DEC")
        btn_fmt.setFixedSize(45, 22) 
        curr_fmt = self.col_formats.get(name, 'dec')
        btn_fmt.setText("HEX" if curr_fmt == 'hex' else "DEC")
        
        btn_fmt.setStyleSheet("""
            QPushButton { 
                background-color: #3B4048; color: #E5C07B; border: 1px solid #5C6370; 
                border-radius: 3px; font-size: 11px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #61AFEF; color: white; }
        """)
        btn_fmt.clicked.connect(lambda _, col=name, b=btn_fmt: self.toggle_col_format_btn(col, b))
        layout.addWidget(btn_fmt)

        row = index // 4
        col = index % 4
        self.legend_layout.addWidget(container, row, col)

    def toggle_col_format_btn(self, col_name, btn_obj):
        old_fmt = self.col_formats.get(col_name, 'dec')
        new_fmt = 'hex' if old_fmt == 'dec' else 'dec'
        self.set_col_format(col_name, new_fmt)
        btn_obj.setText(new_fmt.upper())
        if self.chk_separate.isChecked():
            trace_obj = self.trace_dict.get(col_name)
            if trace_obj and trace_obj['axis']:
                trace_obj['axis'].set_format(new_fmt)

    def on_wave_toggle(self, state, col):
        is_visible = (state == Qt.Checked)
        objs = self.trace_dict.get(col)
        if objs:
            objs['visible'] = is_visible
            for key in ['curve', 'scatter', 'axis']:
                item = objs.get(key)
                if item is not None:
                    try:
                        item.setVisible(is_visible)
                    except RuntimeError:
                        pass
        self.rebuild_column_cache()
        self.update_stats_table()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #282C34; }
            QFrame#TopPanel { background-color: #21252B; border-bottom: 1px solid #181A1F; }
            QFrame#LegendPanel { background-color: #21252B; border-top: 1px solid #181A1F; }
            QCheckBox { color: #ABB2BF; font-size: 13px; spacing: 5px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #5C6370; background: #282C34; }
            QCheckBox::indicator:checked { background: #98C379; border: 1px solid #98C379; }
            QDoubleSpinBox { background-color: #3B4048; color: #DCDFE4; border: 1px solid #181A1F; border-radius: 4px; padding: 4px; font-weight: bold; }
            QPushButton { background-color: #3B4048; color: #DCDFE4; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background-color: #4B5263; color: #FFFFFF; }
            QPushButton#BtnReset { color: #98C379; background-color: #2C313A; border: 1px solid #98C379; }
            QMenu { background-color: #282C34; color: #DCDFE4; border: 1px solid #4B5263; }
            QMenu::item:selected { background-color: #4B5263; }
            QScrollBar:vertical { border: none; background: #21252B; width: 10px; }
            QScrollBar::handle:vertical { background: #4B5263; min-height: 20px; border-radius: 5px; }
        """)

    def toggle_antialias(self, enabled):
        pg.setConfigOptions(antialias=enabled)
        self.update_plot_wrapper() 

    def toggle_measure(self, enabled):
        if enabled: self.setup_cursors()
        else: self.remove_cursors()
    
    def setup_cursors(self):
        if self.main_vb is None: return
        if self.cursor_x1 is not None: return 
        
        vr = self.main_vb.viewRange()
        x_cen, x_span = (vr[0][0]+vr[0][1])/2, (vr[0][1]-vr[0][0])/4
        y_cen, y_span = (vr[1][0]+vr[1][1])/2, (vr[1][1]-vr[1][0])/4
        
        opts = {'position':0.05, 'color':'#E5C07B', 'movable':True, 'fill':(0,0,0,200)}
        self.cursor_x1 = pg.InfiniteLine(pos=x_cen-x_span, angle=90, movable=True, 
                                        pen=pg.mkPen('#E5C07B', width=2, style=Qt.DashLine), 
                                        label='X1: {value:.1f}', labelOpts=opts)
        self.cursor_x2 = pg.InfiniteLine(pos=x_cen+x_span, angle=90, movable=True, 
                                        pen=pg.mkPen('#E5C07B', width=2, style=Qt.DashLine), 
                                        label='X2: {value:.1f}', labelOpts=opts)
        
        self.cursor_y1 = pg.InfiniteLine(pos=y_cen-y_span, angle=0, movable=True, 
                                        pen=pg.mkPen('#61AFEF', width=2, style=Qt.DashLine))
        self.cursor_y2 = pg.InfiniteLine(pos=y_cen+y_span, angle=0, movable=True, 
                                        pen=pg.mkPen('#61AFEF', width=2, style=Qt.DashLine))

        self.main_vb.addItem(self.cursor_x1)
        self.main_vb.addItem(self.cursor_x2)
        self.main_vb.addItem(self.cursor_y1)
        self.main_vb.addItem(self.cursor_y2)
        
        self.cursor_x1.sigPositionChanged.connect(self.update_cursors_label)
        self.cursor_x2.sigPositionChanged.connect(self.update_cursors_label)
        self.cursor_y1.sigPositionChanged.connect(self.update_cursors_label)
        self.cursor_y2.sigPositionChanged.connect(self.update_cursors_label)
        
        self.update_cursors_label()
        self.update_stats_table()

    def update_cursors_label(self):
        if self.cursor_x1 and self.cursor_x2:
            v1 = self.cursor_x1.value()
            v2 = self.cursor_x2.value()
            diff = v2 - v1
            self.cursor_x1.label.setFormat(f"X1: {v1:.1f}")
            self.cursor_x2.label.setFormat(f"X2: {v2:.1f}\nΔX: {diff:.1f}")
            self.update_stats_table() 
            
        if self.cursor_y1 and self.cursor_y2:
            self.update_stats_table()

    def remove_cursors(self):
        if self.main_vb:
            if self.cursor_x1: self.main_vb.removeItem(self.cursor_x1)
            if self.cursor_x2: self.main_vb.removeItem(self.cursor_x2)
            if self.cursor_y1: self.main_vb.removeItem(self.cursor_y1)
            if self.cursor_y2: self.main_vb.removeItem(self.cursor_y2)
            self.cursor_x1 = None; self.cursor_x2 = None
            self.cursor_y1 = None; self.cursor_y2 = None
        self.update_stats_table()

    def on_view_dragged(self, pos, last_pos):
        if not self.main_vb: return
        pt_curr = self.main_vb.mapToView(pos)
        pt_last = self.main_vb.mapToView(last_pos)
        self.main_vb.translateBy(-(pt_curr - pt_last))
        for v in self.overlay_views: 
            v.translateBy(y=-(v.mapToView(pos) - v.mapToView(last_pos)).y())

    def reset_views(self):
        if self.main_vb: self.main_vb.autoRange()
        for v in self.overlay_views: v.autoRange()
        self.status_label.setText(" 视图已复位")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        acts = [("分轴显示", self.chk_separate), ("十字光标", self.chk_crosshair), ("测量模式", self.chk_measure), 
                ("抗锯齿", self.chk_antialias), ("显示数据点", self.chk_dots)]
        for name, widget in acts:
            a = QAction(name, self, checkable=True)
            a.setChecked(widget.isChecked())
            a.triggered.connect(widget.click)
            menu.addAction(a)
        menu.exec_(QCursor.pos())

    def load_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "Data (*.csv *.txt)")
        if not fname: return
        self.loading_overlay.start("正在读取文件...")
        self.btn_load.setEnabled(False)
        self.chk_dots.setEnabled(False)
        self.status_label.setText(f" 读取: {os.path.basename(fname)}")
        self.cleanup_plot() 
        self.dots_cache = None
        self.col_formats = {} 
        self.hidden_cols = set() 
        self.loader = FileLoaderThread(fname)
        self.loader.finished_signal.connect(self.on_loaded)
        self.loader.error_signal.connect(self.on_error)
        self.loader.info_signal.connect(lambda msg: self.loading_overlay.start(msg))
        self.loader.start()

    def on_loaded(self, df):
        self.df = df
        self.loading_overlay.start("正在渲染图形...")
        QTimer.singleShot(50, self.recalc_time)

    def on_error(self, msg):
        self.loading_overlay.stop()
        self.btn_load.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)

    def recalc_time(self):
        if self.df is None: return
        try:
            rate = self.spin_rate.value()
            self.time_axis = np.arange(len(self.df), dtype=np.float32) * rate
            self.df_values = self.df.to_numpy(dtype=np.float32, copy=False)
            self.rebuild_column_cache()
            if self.dot_worker and self.dot_worker.isRunning():
                self.dot_worker.terminate()
                self.dot_worker.wait()
            self.dots_cache = None
            self.chk_dots.blockSignals(True)
            self.chk_dots.setChecked(False)
            self.chk_dots.blockSignals(False)
            self.chk_dots.setEnabled(True)
            self.update_plot()
            self.btn_load.setEnabled(True)
            self.status_label.setText(f" 就绪 | {len(self.df)} 行")
            self.loading_overlay.stop()
        except Exception as e:
            self.loading_overlay.stop()
            QMessageBox.critical(self, "计算错误", str(e))

    def on_dots_prepared(self, dots_data):
        self.dots_cache = dots_data
        self.chk_dots.setEnabled(True)
        self.status_label.setText(f" 就绪 | {len(self.df)} 行")
        self.loading_overlay.stop()
        if self.chk_dots.isChecked():
            self.update_plot_wrapper()

    def cleanup_plot(self):
        if self.proxy: 
            try: self.proxy.disconnect()
            except: pass
        self.proxy = None
        self.v_line = None; self.h_line = None; self.crosshair_label = None
        self.cursor_x1 = None; self.cursor_x2 = None; self.cursor_y1 = None; self.cursor_y2 = None
        for v in self.overlay_views: 
            if v.scene(): v.scene().removeItem(v)
        self.overlay_views.clear(); self.all_views.clear(); self.trace_dict.clear()
        self.visible_cols_cache = []
        self.col_index_map = {}
        self.plot_layout.clear(); self.stats_table.clearContents(); self.stats_table.setRowCount(0)
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def update_views_geometry(self):
        if not self.main_vb: return
        rect = self.main_vb.sceneBoundingRect()
        for v in self.overlay_views: v.setGeometry(rect); v.linkedViewChanged(self.main_vb, v.XAxis)

    def on_global_zoom(self, factor, scene_pos):
        if not self.main_vb: return
        center_main = self.main_vb.mapSceneToView(scene_pos)
        self.main_vb.scaleBy(x=factor, y=1, center=center_main)
        for view in self.all_views:
            center_view = view.mapSceneToView(scene_pos)
            view.scaleBy(x=1, y=factor, center=center_view)

    def on_rect_zoom(self, rel_min, rel_max):
        sender = self.sender()
        for view in self.all_views:
            if view == sender:
                continue
            current_y = view.viewRange()[1]
            span = current_y[1] - current_y[0]
            new_min = current_y[0] + span * rel_min
            new_max = current_y[0] + span * rel_max
            view.setYRange(new_min, new_max, padding=0)

    def get_render_series(self, col_name):
        idx = self.col_index_map.get(col_name)
        if idx is None:
            y = self.df[col_name].values
        else:
            y = self.df_values[:, idx]
        if len(self.time_axis) <= MAX_RENDER_POINTS:
            return self.time_axis, y
        step = max(1, len(self.time_axis) // MAX_RENDER_POINTS)
        return self.time_axis[::step], y[::step]

    def create_view_box(self):
        vb = CustomViewBox()
        vb.sigDragEvent.connect(self.on_view_dragged)
        vb.sigRightClickDouble.connect(self.reset_views) 
        vb.sigXRangeChanged.connect(self.update_stats_table) 
        vb.sigRightClick.connect(self.show_context_menu)
        vb.sigZoomEvent.connect(self.on_global_zoom)
        vb.sigRectZoom.connect(self.on_rect_zoom)
        return vb

    def update_plot_wrapper(self):
        if self.chk_dots.isChecked() and self.dots_cache is None:
            self.prepare_dots_cache()
            return
        self.loading_overlay.start("正在刷新视图...")
        QTimer.singleShot(20, self.update_plot)

    def prepare_dots_cache(self):
        if self.df is None or self.time_axis is None:
            return
        if self.dot_worker and self.dot_worker.isRunning():
            return
        self.chk_dots.setEnabled(False)
        self.loading_overlay.start("正在后台优化数据点...")
        self.dot_worker = DotPreparerThread(self.df, self.time_axis)
        self.dot_worker.finished_signal.connect(self.on_dots_prepared)
        self.dot_worker.start()

    def update_plot(self):
        try:
            if self.df is None: return
            self.cleanup_plot() 
            cols = self.df.columns
            separate = self.chk_separate.isChecked()
            show_dots = self.chk_dots.isChecked() and (self.dots_cache is not None)
            
            self.main_vb = self.create_view_box()
            self.all_views.append(self.main_vb)
            
            def draw(target_plot, col, color, visible=True):
                x_data, y_data = self.get_render_series(col)
                curve = pg.PlotCurveItem(x=x_data, y=y_data, pen=pg.mkPen(color, width=1), connect='finite')
                if hasattr(curve, 'setDownsampling'): curve.setDownsampling(auto=True, method='peak')
                if hasattr(curve, 'setClipToView'): curve.setClipToView(True)
                
                curve.setVisible(visible)
                target_plot.addItem(curve)
                
                scatter = None
                if show_dots:
                    dx, dy = self.dots_cache[col]
                    scatter = pg.ScatterPlotItem(x=dx, y=dy, pen=None, brush=color, size=5, symbol='o')
                    scatter.setVisible(visible) 
                    target_plot.addItem(scatter)
                    
                self.trace_dict[col] = {'curve': curve, 'scatter': scatter, 'axis': None, 'visible': visible}
                return curve, scatter

            if not separate:
                p = self.plot_layout.addPlot(row=0, col=0, viewBox=self.main_vb)
                p.setLabel('bottom', "Time", units='ms'); p.getAxis('bottom').enableAutoSIPrefix(False)
                p.showGrid(x=True, y=True, alpha=0.3); p.setMenuEnabled(False)
                
                for i, col in enumerate(cols):
                    c = WAVE_COLORS[i % len(WAVE_COLORS)]
                    is_visible = col not in self.hidden_cols
                    draw(p, col, c, visible=is_visible)
                    self.add_legend_item(col, c, i, checked=is_visible)
            else:
                p_main = self.plot_layout.addPlot(row=0, col=len(cols), viewBox=self.main_vb)
                p_main.showAxis('left', False); p_main.showGrid(x=True, y=False, alpha=0.3)
                p_main.setLabel('bottom', "Time", units='ms'); p_main.getAxis('bottom').enableAutoSIPrefix(False)
                p_main.setMenuEnabled(False); self.main_vb.sigResized.connect(self.update_views_geometry)
                
                for i, col in enumerate(cols):
                    c = WAVE_COLORS[i % len(WAVE_COLORS)]
                    is_visible = col not in self.hidden_cols
                    
                    ax = SmartAxisItem(orientation='left')
                    ax.setPen(c); ax.setTextPen(c)
                    
                    current_fmt = self.col_formats.get(col, 'dec')
                    ax.set_format(current_fmt)
                    ax.setVisible(is_visible) 
                    
                    self.plot_layout.addItem(ax, row=0, col=i)
                    if i==0: view = self.main_vb
                    else:
                        view = self.create_view_box(); view.enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)
                        p_main.scene().addItem(view); view.setXLink(self.main_vb)
                        self.overlay_views.append(view); self.all_views.append(view)
                        view.setVisible(is_visible)

                    ax.linkToView(view)
                    draw(view, col, c, visible=is_visible)
                    self.trace_dict[col]['axis'] = ax 
                    
                    self.add_legend_item(col, c, i, checked=is_visible)
                    
                self.update_views_geometry()
            
            self.rebuild_column_cache()
            if self.chk_crosshair.isChecked(): self.setup_crosshair()
            if self.chk_measure.isChecked(): self.setup_cursors()
            self.update_stats_table()
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "绘图错误", str(e))
        finally:
            if not (self.dot_worker and self.dot_worker.isRunning()): self.loading_overlay.stop()

    def toggle_crosshair(self, enabled):
        if enabled: self.setup_crosshair()
        else: self.remove_crosshair()

    def setup_crosshair(self):
        if self.df is None or not self.main_vb: return
        if self.crosshair_label: return
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#FFFFFF', width=1, style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#FFFFFF', width=1, style=Qt.DashLine))
        self.main_vb.addItem(self.v_line); self.main_vb.addItem(self.h_line)
        self.crosshair_label = pg.TextItem(anchor=(0, 1), color='#DCDFE4', fill=QColor(40, 44, 52, 200))
        self.main_vb.addItem(self.crosshair_label)
        self.proxy = pg.SignalProxy(self.plot_layout.scene().sigMouseMoved, rateLimit=60, slot=self.on_mouse_move)

    def remove_crosshair(self):
        if self.proxy: 
            try: self.proxy.disconnect()
            except: pass
        self.proxy = None
        if self.main_vb:
            if self.v_line: self.main_vb.removeItem(self.v_line)
            if self.h_line: self.main_vb.removeItem(self.h_line)
            if self.crosshair_label: self.main_vb.removeItem(self.crosshair_label)
        self.v_line = None; self.h_line = None; self.crosshair_label = None

    def on_mouse_move(self, evt):
        if self.df is None or self.df_values is None or not self.crosshair_label: return
        if not self.chk_crosshair.isChecked(): return
        try:
            pos = evt[0]
            if self.main_vb.sceneBoundingRect().contains(pos):
                pt = self.main_vb.mapSceneToView(pos)
                final_x = pt.x(); final_y = pt.y()
                rate = self.spin_rate.value() 
                idx = int(round(final_x / rate))
                if idx < 0: idx = 0
                if idx >= len(self.df): idx = len(self.df) - 1
                final_x = self.time_axis[idx]
                if self.v_line: self.v_line.setPos(final_x)
                if self.h_line: self.h_line.setPos(final_y)
                info = f"<span style='color: #ABB2BF'>Time: {final_x:.1f} ms</span><br>"
                row_vals = self.df_values[idx]
                for col in self.visible_cols_cache:
                    col_idx = self.col_index_map.get(col)
                    if col_idx is None:
                        continue
                    c = WAVE_COLORS[col_idx % len(WAVE_COLORS)]
                    v = row_vals[col_idx]
                    val_str = self.format_val(col, v)
                    info += f'<span style="color:{c}">■ {col}: {val_str}</span><br>'
                self.crosshair_label.setHtml(f'<div style="font-family: Consolas, sans-serif; font-size:12px">{info}</div>')
                self.crosshair_label.setPos(final_x, final_y)
        except Exception: pass

if __name__ == "__main__":
    if hasattr(Qt, 'AA_EnableHighDpiScaling'): QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'): QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    set_window_icon(app) 
    window = ProOscilloscope()
    window.show()
    sys.exit(app.exec_())