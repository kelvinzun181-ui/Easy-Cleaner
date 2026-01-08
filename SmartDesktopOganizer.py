import os
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import heapq
import threading

# ==========================================
# 1. 核心分类字典（已加入专业设计及工程文件）
# ==========================================
FINE_GRAINED_CATEGORIES = {
    "设计与工程": {
        "Photoshop工程": [".psd", ".psb"],
        "Premiere视频剪辑": [".prproj"],
        "AfterEffects特效": [".aep"],
        "Illustrator矢量图": [".ai", ".eps"],
        "AutoCAD图纸": [".dwg", ".dxf"],
        "3D建模与工程": [".obj", ".fbx", ".stl", ".3ds", ".max", ".c4d"],
    },
    "文档": {
        "Excel表格": [".xls", ".xlsx", ".csv"],
        "Word文档": [".doc", ".docx"],
        "PPT演示": [".ppt", ".pptx"],
        "文本文件": [".txt"],
        "PDF文档": [".pdf"]
    },
    "视频": {
        "视频成品": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv"]
    },
    "音频": {
        "音频素材": [".mp3", ".wav", ".flac", ".m4a", ".aac"]
    },
    "图片": {
        "图像素材": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]
    },
    "字幕": {
        "字幕文件": [".srt", ".ass", ".sub", ".vtt"]
    },
    "压缩包": {
        "压缩文件": [".zip", ".rar", ".7z", ".tar", ".gz"]
    },
    "安装包": {
        "安装程序": [".exe", ".msi", ".dmg", ".pkg"]
    }
}


class SmartOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能系统助手 v5.5 (专业设计增强版)")
        self.root.geometry("550x480")
        self.history = []

        # 标题
        tk.Label(root, text="🚀 智能系统助手", font=("微软雅黑", 20, "bold")).pack(pady=15)

        # --- 桌面归类控制区 ---
        group_org = tk.LabelFrame(root, text="桌面精细化整理", padx=15, pady=15)
        group_org.pack(padx=20, pady=10, fill="x")

        tk.Button(group_org, text="一键精细归类", command=self.run_organize,
                  bg="#4CAF50", fg="white", font=("微软雅黑", 10), width=15).pack(side="left", padx=10)
        tk.Button(group_org, text="一键撤销归类", command=self.run_undo,
                  bg="#f44336", fg="white", font=("微软雅黑", 10), width=15).pack(side="right", padx=10)

        # --- C盘清理控制区 ---
        group_clean = tk.LabelFrame(root, text="C盘安全瘦身 (跳过系统敏感区)", padx=15, pady=15)
        group_clean.pack(padx=20, pady=10, fill="x")

        self.btn_scan = tk.Button(group_clean, text="开始扫描大文件 (>100MB)", command=self.start_scan_thread,
                                  bg="#2196F3", fg="white", font=("微软雅黑", 10), width=35)
        self.btn_scan.pack()

        self.progress_label = tk.Label(group_clean, text="", fg="#666", wraplength=450)
        self.progress_label.pack(pady=5)

        self.status_bar = tk.Label(root, text="准备就绪 | 建议以管理员身份运行以获得完整权限", bd=1, relief=tk.SUNKEN,
                                   anchor=tk.W)
        self.status_bar.pack(side="bottom", fill="x")

    # ==========================================
    # 2. 桌面精细化归类逻辑
    # ==========================================
    def run_organize(self):
        desktop = Path.home() / "Desktop"
        self.history = []
        count = 0

        try:
            for item in desktop.iterdir():
                # 排除文件夹、快捷方式和脚本自身
                if item.is_dir() or item.suffix == ".lnk" or item.name == "SmartOrganizer.py":
                    continue

                ext = item.suffix.lower()
                matched = False

                # 查找匹配的细分规则
                for main_cat, sub_dict in FINE_GRAINED_CATEGORIES.items():
                    for sub_cat, exts in sub_dict.items():
                        if ext in exts:
                            # 目标路径: 桌面/大分类/子分类/文件名
                            dest_dir = desktop / main_cat / sub_cat
                            dest_dir.mkdir(parents=True, exist_ok=True)

                            target = dest_dir / item.name
                            # 处理重名文件
                            if target.exists():
                                target = dest_dir / f"new_{item.name}"

                            self.history.append((str(item), str(target)))
                            shutil.move(str(item), str(target))
                            count += 1
                            matched = True
                            break
                    if matched: break

                # 兜底：未识别的文件
                if not matched and ext != "":
                    dest_dir = desktop / "其他文件"
                    dest_dir.mkdir(exist_ok=True)
                    target = dest_dir / item.name
                    if target.exists(): target = dest_dir / f"new_{item.name}"
                    self.history.append((str(item), str(target)))
                    shutil.move(str(item), str(target))
                    count += 1

            messagebox.showinfo("成功", f"整理完成！\n已将 {count} 个文件分类到专属文件夹中。")
        except Exception as e:
            messagebox.showerror("错误", f"归类失败: {e}")

    def run_undo(self):
        if not self.history:
            messagebox.showwarning("提示", "当前没有可撤销的操作记录。")
            return

        try:
            undo_count = 0
            for original, moved in self.history:
                if os.path.exists(moved):
                    shutil.move(moved, original)
                    undo_count += 1
            self.history = []
            messagebox.showinfo("撤销完成", f"已将 {undo_count} 个文件搬回桌面。")
        except Exception as e:
            messagebox.showerror("错误", f"撤销失败: {e}")

    # ==========================================
    # 3. C盘安全扫描逻辑 (多线程)
    # ==========================================
    def start_scan_thread(self):
        self.btn_scan.config(state=tk.DISABLED)
        self.progress_label.config(text="🔍 正在全盘搜索，请耐心等待（已过滤系统文件）...")
        threading.Thread(target=self.scan_logic, daemon=True).start()

    def scan_logic(self):
        large_files = []
        min_size = 100 * 1024 * 1024  # 阈值 100MB
        # 安全过滤黑名单：不进入这些目录
        exclude_dirs = {'Windows', 'ProgramData', 'AppData', '$Recycle.Bin', 'System Volume Information'}

        try:
            for root_dir, dirs, files in os.walk("C:\\"):
                # 原地修改 dirs 以跳过黑名单目录
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

                for name in files:
                    try:
                        file_path = os.path.join(root_dir, name)
                        if os.path.islink(file_path): continue

                        file_size = os.path.getsize(file_path)
                        if file_size > min_size:
                            large_files.append((file_size, file_path))
                    except:
                        continue

            top_files = heapq.nlargest(30, large_files)
            self.root.after(0, lambda: self.show_results(top_files))
        finally:
            self.root.after(0, self.reset_scan_ui)

    def reset_scan_ui(self):
        self.btn_scan.config(state=tk.NORMAL)
        self.progress_label.config(text="扫描任务已结束。")

    def show_results(self, files):
        res_win = tk.Toplevel(self.root)
        res_win.title("C盘大文件管理清单")
        res_win.geometry("850x550")

        # 滚动区域设置
        container = ttk.Frame(res_win)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        tk.Label(scrollable_frame, text="💡 提示：删除前请点“打开目录”确认文件用途，以免影响软件运行。",
                 fg="red", font=("微软雅黑", 9)).grid(row=0, column=0, columnspan=3, pady=10)

        for i, (size, path) in enumerate(files):
            size_str = f"{round(size / (1024 * 1024), 2)} MB"

            tk.Label(scrollable_frame, text=size_str, font=("Consolas", 10, "bold"), fg="blue").grid(row=i + 1,
                                                                                                     column=0, padx=10,
                                                                                                     pady=5)
            tk.Label(scrollable_frame, text=path, wraplength=550, justify="left").grid(row=i + 1, column=1, padx=5,
                                                                                       sticky="w")

            btn_box = tk.Frame(scrollable_frame)
            btn_box.grid(row=i + 1, column=2, padx=10)

            tk.Button(btn_box, text="定位", command=lambda p=path: self.open_folder(p)).pack(side="left", padx=2)
            tk.Button(btn_box, text="删除", bg="#ffc107", command=lambda p=path: self.delete_file(p)).pack(side="left",
                                                                                                           padx=2)

        container.pack(fill="both", expand=True)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def open_folder(self, path):
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            os.startfile(folder)

    def delete_file(self, path):
        if messagebox.askyesno("二次确认", f"确定永久删除此文件吗？此操作无法撤销！\n\n{path}"):
            try:
                os.remove(path)
                messagebox.showinfo("成功", "文件已被永久删除。")
            except Exception as e:
                messagebox.showerror("失败", f"无法删除：\n{e}\n\n该文件可能正在运行或受到系统保护。")


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartOrganizerApp(root)
    root.mainloop()