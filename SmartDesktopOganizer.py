import os
import shutil
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path
import heapq
import threading

# 归类规则保持不变
FILE_CATEGORIES = {
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "文档": [".pdf", ".doc", ".docx", ".txt", ".ppt", ".pptx", ".xls", ".xlsx"],
    "字幕": [".srt", ".ass", ".sub", ".vtt", ".ssa"],
    "压缩包": [".zip", ".rar", ".7z"],
    "安装包": [".exe", ".msi"],
    "视频音频": [".mp4", ".mov", ".mp3", ".wav"],
}


class SmartOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能系统助手 v4.1 (安全扫描版)")
        self.root.geometry("500x420")
        self.history = []

        tk.Label(root, text="🚀 智能系统助手", font=("微软雅黑", 18, "bold")).pack(pady=10)

        # 桌面归类区
        group_org = tk.LabelFrame(root, text="桌面归类", padx=10, pady=10)
        group_org.pack(padx=20, pady=10, fill="x")
        tk.Button(group_org, text="一键归类", command=self.run_organize, bg="#4CAF50", fg="white", width=12).pack(
            side="left", padx=20)
        tk.Button(group_org, text="一键撤销", command=self.run_undo, bg="#f44336", fg="white", width=12).pack(
            side="right", padx=20)

        # C盘清理区
        group_clean = tk.LabelFrame(root, text="C盘大文件管理 (已自动避开系统区)", padx=10, pady=10)
        group_clean.pack(padx=20, pady=10, fill="x")
        self.btn_scan = tk.Button(group_clean, text="安全扫描C盘大文件", command=self.start_scan_thread, bg="#2196F3",
                                  fg="white", width=30)
        self.btn_scan.pack(pady=5)

        self.progress_label = tk.Label(group_clean, text="", fg="orange", wraplength=400)
        self.progress_label.pack()

        self.status_label = tk.Label(root, text="准备就绪", fg="gray")
        self.status_label.pack(side="bottom", pady=10)

    # --- 桌面归类逻辑 (复用之前逻辑) ---
    def run_organize(self):
        desktop = Path.home() / "Desktop"
        self.history = []
        count = 0
        for item in desktop.iterdir():
            if item.is_dir() or item.suffix == ".lnk" or item.name.endswith(".py"): continue
            ext = item.suffix.lower()
            matched = False
            for cat, exts in FILE_CATEGORIES.items():
                if ext in exts:
                    dest = desktop / cat
                    dest.mkdir(exist_ok=True)
                    target = dest / item.name
                    self.history.append((str(item), str(target)))
                    shutil.move(str(item), str(target))
                    count += 1
                    matched = True
                    break
            if not matched and ext != "":
                dest = desktop / "其他文件"
                dest.mkdir(exist_ok=True)
                target = dest / item.name
                self.history.append((str(item), str(target)))
                shutil.move(str(item), str(target))
                count += 1
        messagebox.showinfo("完成", f"已整理 {count} 个文件")

    def run_undo(self):
        if not self.history: return
        for ori, mov in self.history:
            if os.path.exists(mov): shutil.move(mov, ori)
        self.history = []
        messagebox.showinfo("撤销", "已还原文件")

    # --- 增强：安全扫描逻辑 ---
    def start_scan_thread(self):
        self.btn_scan.config(state=tk.DISABLED)
        self.progress_label.config(text="正在避开系统文件夹扫描中...")
        threading.Thread(target=self.scan_logic, daemon=True).start()

    def scan_logic(self):
        large_files = []
        min_size = 100 * 1024 * 1024  # 100MB

        # 需要跳过的敏感/高负荷目录
        exclude_dirs = {'Windows', 'ProgramData', 'AppData'}

        try:
            for root_dir, dirs, files in os.walk("C:\\"):
                # 关键优化：原地修改 dirs 列表，os.walk 就会跳过这些目录
                dirs[:] = [d for d in dirs if d not in exclude_dirs]

                for name in files:
                    try:
                        path = os.path.join(root_dir, name)
                        if os.path.islink(path): continue

                        size = os.path.getsize(path)
                        if size > min_size:
                            large_files.append((size, path))
                    except:
                        continue

            top_files = heapq.nlargest(25, large_files)
            self.root.after(0, lambda: self.show_results(top_files))
        finally:
            self.root.after(0, self.reset_scan_btn)

    def reset_scan_btn(self):
        self.btn_scan.config(state=tk.NORMAL)
        self.progress_label.config(text="扫描完成！已过滤系统敏感区域。")

    def show_results(self, files):
        res_win = tk.Toplevel(self.root)
        res_win.title("扫描结果 - 已过滤系统区")
        res_win.geometry("800x500")

        canvas = tk.Canvas(res_win)
        scrollbar = ttk.Scrollbar(res_win, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        tk.Label(scroll_frame, text="以下是非系统区的大文件 (前25名)：", font=("微软雅黑", 10, "bold")).grid(row=0,
                                                                                                            column=0,
                                                                                                            columnspan=3,
                                                                                                            pady=10)

        for i, (size, path) in enumerate(files):
            size_mb = f"{round(size / (1024 * 1024), 2)} MB"
            tk.Label(scroll_frame, text=size_mb, fg="blue").grid(row=i + 1, column=0, padx=5, pady=5)
            tk.Label(scroll_frame, text=path, wraplength=500, justify="left").grid(row=i + 1, column=1, padx=5)

            btn_box = tk.Frame(scroll_frame)
            btn_box.grid(row=i + 1, column=2, padx=5)

            tk.Button(btn_box, text="打开目录", command=lambda p=path: self.open_path(p)).pack(side="left", padx=2)
            tk.Button(btn_box, text="删除", bg="#ffc107", command=lambda p=path: self.delete_file(p)).pack(side="left",
                                                                                                           padx=2)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def open_path(self, path):
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            os.startfile(folder)

    def delete_file(self, path):
        if messagebox.askyesno("确认删除", f"确定要永久删除此文件吗？\n\n{path}"):
            try:
                os.remove(path)
                messagebox.showinfo("成功", "文件已删除")
            except Exception as e:
                messagebox.showerror("错误", f"无法删除: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartOrganizerApp(root)
    root.mainloop()