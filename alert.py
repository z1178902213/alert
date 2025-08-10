import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys
from datetime import datetime, timedelta
import winreg
import ctypes
from ctypes import wintypes

class ReminderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("思源笔记提醒器")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 配置变量
        self.config_file = "reminder_config.json"
        self.is_running = False
        self.reminder_thread = None
        self.last_reminder_time = None
        
        # 加载配置
        self.load_config()
        
        # 创建UI
        self.create_ui()
        
        # 启动提醒线程
        self.start_reminder()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 最小化到系统托盘
        self.minimize_to_tray()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "enabled": True,
            "interval_hours": 1,
            "reminder_text": "该打开思源笔记看看自己的目标了！\n\n记得检查：\n1. 今天的目标完成情况\n2. 明天的计划安排\n3. 重要事项记录",
            "auto_start": False
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    # 确保所有配置项都存在
                    for key, value in default_config.items():
                        if key not in self.config:
                            self.config[key] = value
            else:
                self.config = default_config
                self.save_config()
        except:
            self.config = default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def create_ui(self):
        """创建用户界面"""
        # 主标题
        title_label = tk.Label(self.root, text="思源笔记提醒器", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # 状态显示
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = tk.Label(self.status_frame, text="状态: 运行中", fg="green", font=("Arial", 12))
        self.status_label.pack()
        
        self.next_reminder_label = tk.Label(self.status_frame, text="下次提醒: 计算中...", font=("Arial", 10))
        self.next_reminder_label.pack()
        
        # 控制按钮
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=20, padx=20, fill="x")
        
        self.toggle_button = tk.Button(control_frame, text="暂停提醒", command=self.toggle_reminder, 
                                     bg="#ff6b6b", fg="white", font=("Arial", 12))
        self.toggle_button.pack(fill="x", pady=5)
        
        test_button = tk.Button(control_frame, text="测试提醒", command=self.test_reminder,
                               bg="#4ecdc4", fg="white", font=("Arial", 12))
        test_button.pack(fill="x", pady=5)
        
        # 设置区域
        settings_frame = tk.LabelFrame(self.root, text="设置", font=("Arial", 12, "bold"))
        settings_frame.pack(pady=20, padx=20, fill="x")
        
        # 提醒间隔设置
        interval_frame = tk.Frame(settings_frame)
        interval_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(interval_frame, text="提醒间隔(小时):", font=("Arial", 10)).pack(side="left")
        self.interval_var = tk.StringVar(value=str(self.config["interval_hours"]))
        interval_spinbox = tk.Spinbox(interval_frame, from_=0.5, to=24, increment=0.5, 
                                    textvariable=self.interval_var, width=10)
        interval_spinbox.pack(side="right")
        
        # 开机自启动设置
        startup_frame = tk.Frame(settings_frame)
        startup_frame.pack(pady=10, padx=10, fill="x")
        
        self.auto_start_var = tk.BooleanVar(value=self.config["auto_start"])
        startup_check = tk.Checkbutton(startup_frame, text="开机自动启动", 
                                     variable=self.auto_start_var, font=("Arial", 10))
        startup_check.pack(side="left")
        
        # 提醒内容设置
        content_frame = tk.Frame(settings_frame)
        content_frame.pack(pady=10, padx=10, fill="x")
        
        tk.Label(content_frame, text="提醒内容:", font=("Arial", 10)).pack(anchor="w")
        self.content_text = tk.Text(content_frame, height=6, width=40, font=("Arial", 9))
        self.content_text.pack(fill="x", pady=5)
        self.content_text.insert("1.0", self.config["reminder_text"])
        
        # 保存按钮
        save_button = tk.Button(settings_frame, text="保存设置", command=self.save_settings,
                               bg="#45b7d1", fg="white", font=("Arial", 12))
        save_button.pack(pady=10, fill="x")
        
        # 底部信息
        info_frame = tk.Frame(self.root)
        info_frame.pack(side="bottom", pady=10)
        
        info_label = tk.Label(info_frame, text="程序将在后台运行，关闭窗口不会退出程序", 
                             font=("Arial", 9), fg="gray")
        info_label.pack()
        
        # 更新状态显示
        self.update_status_display()
    
    def update_status_display(self):
        """更新状态显示"""
        if self.is_running:
            self.status_label.config(text="状态: 运行中", fg="green")
            self.toggle_button.config(text="暂停提醒", bg="#ff6b6b")
        else:
            self.status_label.config(text="状态: 已暂停", fg="red")
            self.toggle_button.config(text="启动提醒", bg="#51cf66")
        
        # 计算下次提醒时间
        if self.is_running and self.last_reminder_time:
            next_time = self.last_reminder_time + timedelta(hours=self.config["interval_hours"])
            if next_time > datetime.now():
                time_diff = next_time - datetime.now()
                hours = int(time_diff.total_seconds() // 3600)
                minutes = int((time_diff.total_seconds() % 3600) // 60)
                self.next_reminder_label.config(text=f"下次提醒: {hours}小时{minutes}分钟后")
            else:
                self.next_reminder_label.config(text="下次提醒: 即将提醒")
        else:
            self.next_reminder_label.config(text="下次提醒: 未设置")
        
        # 每秒更新一次
        self.root.after(1000, self.update_status_display)
    
    def toggle_reminder(self):
        """切换提醒状态"""
        self.is_running = not self.is_running
        if self.is_running:
            self.start_reminder()
        self.update_status_display()
    
    def start_reminder(self):
        """启动提醒线程"""
        if not self.is_running:
            return
        
        if self.reminder_thread is None or not self.reminder_thread.is_alive():
            self.reminder_thread = threading.Thread(target=self.reminder_loop, daemon=True)
            self.reminder_thread.start()
    
    def reminder_loop(self):
        """提醒循环"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 检查是否需要提醒
                if (self.last_reminder_time is None or 
                    (current_time - self.last_reminder_time).total_seconds() >= 
                    self.config["interval_hours"] * 3600):
                    
                    # 显示提醒
                    self.show_reminder()
                    self.last_reminder_time = current_time
                
                # 等待1分钟再检查
                time.sleep(60)
                
            except Exception as e:
                print(f"提醒循环错误: {e}")
                time.sleep(60)
    
    def show_reminder(self):
        """显示提醒弹窗"""
        try:
            # 创建提醒窗口
            reminder_window = tk.Toplevel()
            reminder_window.title("思源笔记提醒")
            reminder_window.geometry("500x400")
            reminder_window.resizable(False, False)
            
            # 设置窗口置顶
            reminder_window.attributes('-topmost', True)
            reminder_window.focus_force()
            
            # 提醒图标和标题
            header_frame = tk.Frame(reminder_window)
            header_frame.pack(pady=20, padx=20, fill="x")
            
            title_label = tk.Label(header_frame, text="⏰ 提醒时间到！", 
                                 font=("Arial", 18, "bold"), fg="#e74c3c")
            title_label.pack()
            
            # 提醒内容
            content_frame = tk.Frame(reminder_window)
            content_frame.pack(pady=20, padx=20, fill="both", expand=True)
            
            content_text = tk.Text(content_frame, wrap="word", font=("Arial", 12), 
                                 bg="#f8f9fa", relief="flat", padx=15, pady=15)
            content_text.pack(fill="both", expand=True)
            content_text.insert("1.0", self.config["reminder_text"])
            content_text.config(state="disabled")
            
            # 按钮区域
            button_frame = tk.Frame(reminder_window)
            button_frame.pack(pady=20, padx=20, fill="x")
            
            open_siyuan_button = tk.Button(button_frame, text="打开思源笔记", 
                                         command=self.open_siyuan, bg="#3498db", fg="white",
                                         font=("Arial", 12), height=2)
            open_siyuan_button.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            close_button = tk.Button(button_frame, text="关闭提醒", 
                                   command=reminder_window.destroy, bg="#95a5a6", fg="white",
                                   font=("Arial", 12), height=2)
            close_button.pack(side="right", fill="x", expand=True, padx=(10, 0))
            
            # 设置窗口居中
            reminder_window.update_idletasks()
            x = (reminder_window.winfo_screenwidth() // 2) - (reminder_window.winfo_width() // 2)
            y = (reminder_window.winfo_screenheight() // 2) - (reminder_window.winfo_height() // 2)
            reminder_window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            print(f"显示提醒失败: {e}")
    
    def open_siyuan(self):
        """打开思源笔记"""
        try:
            # 尝试多种可能的思源笔记路径
            possible_paths = [
                r"C:\Users\%USERNAME%\AppData\Local\SiYuan\SiYuan.exe",
                r"C:\Program Files\SiYuan\SiYuan.exe",
                r"C:\Program Files (x86)\SiYuan\SiYuan.exe",
                r"D:\SiYuan\SiYuan.exe"
            ]
            
            for path in possible_paths:
                expanded_path = os.path.expandvars(path)
                if os.path.exists(expanded_path):
                    os.startfile(expanded_path)
                    return
            
            # 如果找不到，尝试通过注册表查找
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\SiYuan.exe")
                path, _ = winreg.QueryValueEx(key, "")
                winreg.CloseKey(key)
                os.startfile(path)
                return
            except:
                pass
            
            # 如果都找不到，提示用户
            messagebox.showinfo("提示", "未找到思源笔记程序，请手动打开。")
            
        except Exception as e:
            print(f"打开思源笔记失败: {e}")
            messagebox.showerror("错误", f"打开思源笔记失败: {e}")
    
    def test_reminder(self):
        """测试提醒"""
        self.show_reminder()
    
    def save_settings(self):
        """保存设置"""
        try:
            # 获取设置值
            self.config["interval_hours"] = float(self.interval_var.get())
            self.config["reminder_text"] = self.content_text.get("1.0", tk.END).strip()
            self.config["auto_start"] = self.auto_start_var.get()
            
            # 保存到文件
            self.save_config()
            
            # 设置开机自启动
            self.set_auto_start(self.config["auto_start"])
            
            messagebox.showinfo("成功", "设置已保存！")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def set_auto_start(self, enable):
        """设置开机自启动"""
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            app_name = "SiYuanReminder"
            
            if enable:
                # 获取当前程序路径
                current_path = sys.argv[0]
                if current_path.endswith('.py'):
                    # 如果是Python脚本，需要转换为exe路径
                    current_path = os.path.abspath(current_path)
                
                # 写入注册表
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{current_path}"')
                winreg.CloseKey(key)
            else:
                # 删除注册表项
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                    winreg.DeleteValue(key, app_name)
                    winreg.CloseKey(key)
                except:
                    pass
                    
        except Exception as e:
            print(f"设置开机自启动失败: {e}")
    
    def minimize_to_tray(self):
        """最小化到系统托盘"""
        # 在Windows上，我们可以隐藏窗口而不是真正的最小化到托盘
        # 这里我们只是设置窗口的初始状态
        pass
    
    def on_closing(self):
        """窗口关闭事件"""
        # 隐藏窗口而不是关闭
        self.root.withdraw()
        
        # 创建系统托盘图标（简化版本）
        self.create_tray_icon()
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 由于Windows系统托盘的复杂性，这里我们使用一个简单的隐藏窗口方案
        # 用户可以通过任务管理器找到程序并结束进程
        
        # 创建一个隐藏的根窗口来保持程序运行
        self.hidden_root = tk.Tk()
        self.hidden_root.withdraw()  # 隐藏窗口
        
        # 创建菜单
        menu = tk.Menu(self.hidden_root, tearoff=0)
        menu.add_command(label="显示主窗口", command=self.show_main_window)
        menu.add_command(label="测试提醒", command=self.test_reminder)
        menu.add_separator()
        menu.add_command(label="退出程序", command=self.quit_app)
        
        # 绑定右键菜单
        self.hidden_root.bind("<Button-3>", lambda e: self.show_context_menu(e, menu))
        
        # 启动隐藏窗口的主循环
        self.hidden_root.mainloop()
    
    def show_context_menu(self, event, menu):
        """显示右键菜单"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def show_main_window(self):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def quit_app(self):
        """退出程序"""
        self.is_running = False
        if self.reminder_thread and self.reminder_thread.is_alive():
            self.reminder_thread.join(timeout=1)
        
        # 删除开机自启动
        self.set_auto_start(False)
        
        # 退出程序
        os._exit(0)

def main():
    """主函数"""
    try:
        app = ReminderApp()
        app.root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {e}")

if __name__ == "__main__":
    main()
