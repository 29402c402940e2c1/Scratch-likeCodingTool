import json
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip_window, text=self.text, 
                         background="#ffffe0", relief="solid", 
                         borderwidth=1, padding=2)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class AutoSizeEntry(ttk.Entry):
    def __init__(self, parent, placeholder, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.placeholder = placeholder
        self.default_fg = self['foreground']
        self.put_placeholder()
        
        self.bind("<FocusIn>", self.clear_placeholder)
        self.bind("<FocusOut>", self.set_placeholder)
        
        Tooltip(self, placeholder)

    def put_placeholder(self):
        self.delete(0, tk.END)
        self.insert(0, self.placeholder)
        self['foreground'] = 'grey'

    def clear_placeholder(self, event):
        if self['foreground'] == 'grey':
            self.delete(0, tk.END)
            self['foreground'] = self.default_fg

    def set_placeholder(self, event):
        if not self.get():
            self.put_placeholder()

class CodeBlockDef:
    def __init__(self, name, params, template):
        self.name = name
        self.params = params
        self.template = template

class CodeBlockInstance:
    def __init__(self, definition, values):
        self.definition = definition
        self.values = values

class CodeBlockEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("可视化编程工具")
        self.block_definitions = []
        self.execution_blocks = []
        self.clipboard = None
        self.create_widgets()
        self.setup_bindings()
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", 
                            foreground="white",
                            background="#4CAF50",
                            font=('TkDefaultFont', 9, 'bold'))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        preset_frame = ttk.Frame(main_frame, width=250)
        preset_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        control_frame = ttk.Frame(preset_frame)
        control_frame.pack(pady=5, fill=tk.X)
        
        buttons = [
            ("新建代码块", self.create_new_block),
            ("导入配置", self.import_config),
            ("导出配置", self.export_config),
            ("保存进度", self.save_progress),
            ("加载进度", self.load_progress)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(control_frame, text=text, command=command, width=15)
            btn.pack(side=tk.TOP, fill=tk.X, pady=2)

        preset_container = ttk.Frame(preset_frame)
        preset_container.pack(fill=tk.BOTH, expand=True)
        
        self.preset_canvas = tk.Canvas(preset_container)
        scrollbar = ttk.Scrollbar(preset_container, orient="vertical", command=self.preset_canvas.yview)
        self.preset_frame = ttk.Frame(self.preset_canvas)
        
        self.preset_canvas.configure(yscrollcommand=scrollbar.set)
        self.preset_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preset_canvas.create_window((0,0), window=self.preset_frame, anchor="nw")

        exec_frame = ttk.Frame(main_frame)
        exec_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.exec_canvas = tk.Canvas(exec_frame)
        exec_scroll = ttk.Scrollbar(exec_frame, orient="vertical", command=self.exec_canvas.yview)
        self.exec_frame = ttk.Frame(self.exec_canvas)
        
        self.exec_canvas.configure(yscrollcommand=exec_scroll.set)
        self.exec_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        exec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.exec_canvas.create_window((0,0), window=self.exec_frame, anchor="nw")

        self.code_preview = tk.Text(main_frame, width=50, wrap=tk.WORD)
        self.code_preview.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

        self.update_preset_panel()

    def setup_bindings(self):
        self.preset_frame.bind("<Configure>", lambda e: self.preset_canvas.configure(scrollregion=self.preset_canvas.bbox("all")))
        self.exec_frame.bind("<Configure>", lambda e: self.exec_canvas.configure(scrollregion=self.exec_canvas.bbox("all")))

    def create_new_block(self):
        dialog = tk.Toplevel()
        dialog.title("新建代码块")
        
        ttk.Label(dialog, text="代码块名称:").grid(row=0, column=0)
        name_entry = ttk.Entry(dialog)
        name_entry.grid(row=0, column=1)
        
        ttk.Label(dialog, text="参数名称（用|分隔）:").grid(row=1, column=0)
        params_entry = ttk.Entry(dialog)
        params_entry.grid(row=1, column=1)
        
        ttk.Label(dialog, text="代码模板（使用{参数名}作为占位符）:").grid(row=2, column=0)
        code_entry = ttk.Entry(dialog, width=40)
        code_entry.grid(row=2, column=1)
        
        def save_block():
            params = [p.strip() for p in params_entry.get().split("|") if p.strip()]
            template = code_entry.get()
            missing = [p for p in params if f"{{{p}}}" not in template]
            if missing:
                messagebox.showerror("错误", f"以下参数未在模板中找到占位符: {', '.join(missing)}")
                return
            self.block_definitions.append(CodeBlockDef(name_entry.get(), params, template))
            self.update_preset_panel()
            dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=save_block).grid(row=3, columnspan=2)

    def update_preset_panel(self):
        for widget in self.preset_frame.winfo_children():
            widget.destroy()
        
        for idx, block in enumerate(self.block_definitions):
            frame = ttk.Frame(self.preset_frame, relief="groove", borderwidth=2)
            frame.pack(fill=tk.X, pady=2, padx=3)
            
            # 操作按钮区（左侧）
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(side=tk.LEFT, padx=3)
            
            # 显眼的选择按钮
            select_btn = ttk.Button(btn_frame, text="+", width=2,
                                style="Accent.TButton",
                                command=lambda b=block: self.add_to_execution(b))
            select_btn.pack(side=tk.LEFT)
            
            # 删除按钮
            del_btn = ttk.Button(btn_frame, text="×", width=2,
                                command=lambda i=idx: self.delete_preset_block(i))
            del_btn.pack(side=tk.LEFT)
            
            # 内容展示区（右侧）
            content_frame = ttk.Frame(frame)
            content_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            ttk.Label(content_frame, text=f"{block.name}", 
                    font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=5)
            ttk.Label(content_frame, text=f"<{' | '.join(block.params)}>", 
                    foreground="#666666").pack(side=tk.LEFT)
            
            # 添加工具提示
            Tooltip(select_btn, "添加至执行区")
            Tooltip(del_btn, "删除代码块定义")


    def bind_preset_events(self, parent, block):
        """递归绑定所有子组件的点击事件"""
        parent.bind("<Button-1>", lambda e, b=block: self.add_to_execution(b))
        for child in parent.winfo_children():
            child.bind("<Button-1>", lambda e, b=block: self.add_to_execution(b))
            self.bind_preset_events(child, block)

    def delete_preset_block(self, index):
        if 0 <= index < len(self.block_definitions):
            del self.block_definitions[index]
            self.update_preset_panel()
            messagebox.showinfo("成功", "预选区代码块已删除")

    def add_to_execution(self, definition, index=None):
        instance = CodeBlockInstance(definition, {param: "" for param in definition.params})
        if index is not None:
            self.execution_blocks.insert(index, instance)
        else:
            self.execution_blocks.append(instance)
        self.update_execution_panel()

    def update_execution_panel(self):
        

        for widget in self.exec_frame.winfo_children():
            widget.destroy()
        for idx, block in enumerate(self.execution_blocks):
            frame = ttk.Frame(self.exec_frame, relief="groove", borderwidth=2)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            # 操作菜单按钮
            menu_btn = ttk.Menubutton(frame, text="☰", width=3)
            menu = tk.Menu(menu_btn, tearoff=0)
            menu.add_command(label="在上方插入", command=lambda i=idx: self.insert_block_dialog(i))
            menu.add_command(label="在下方插入", command=lambda i=idx: self.insert_block_dialog(i+1))
            menu.add_separator()
            menu.add_command(label="删除", command=lambda i=idx: self.delete_block(i))
            menu.add_command(label="复制", command=lambda i=idx: self.copy_block(i))
            menu.add_command(label="剪切", command=lambda i=idx: self.cut_block(i))
            menu.add_command(label="粘贴", command=lambda i=idx: self.paste_block(i))
            menu_btn.configure(menu=menu)
            menu_btn.pack(side=tk.LEFT, padx=3)
            
            # 内容区域
            content_frame = ttk.Frame(frame)
            content_frame.pack(fill=tk.X, expand=True)
            
            ttk.Label(content_frame, text=f"{block.definition.name}").pack(side=tk.LEFT)
            ttk.Button(content_frame, text="×", width=2, 
                      command=lambda i=idx: self.delete_block(i)).pack(side=tk.RIGHT)
            
            param_frame = ttk.Frame(frame)
            param_frame.pack(fill=tk.X, padx=10)
            for param in block.definition.params:
                ttk.Label(param_frame, text=param+":").pack(side=tk.LEFT)
                entry = AutoSizeEntry(param_frame, placeholder=param, width=15)
                if block.values[param]:
                    entry.delete(0, tk.END)
                    entry.insert(0, block.values[param])
                    entry['foreground'] = entry.default_fg
                entry.bind("<KeyRelease>", lambda e, b=block, p=param: 
                          self.update_param_value(b, p, e.widget))
                entry.pack(side=tk.LEFT, padx=2)

    def insert_block_dialog(self, position):
        dialog = tk.Toplevel()
        dialog.title("选择要插入的代码块")
        container = ttk.Frame(dialog)
        container.pack(fill=tk.BOTH, expand=True)
        for block in self.block_definitions:
            btn = ttk.Button(container, text=f"{block.name}<{'><'.join(block.params)}>",
                           command=lambda b=block: (self.add_to_execution(b, position), dialog.destroy()))
            btn.pack(fill=tk.X, pady=2)
        ttk.Button(container, text="取消", command=dialog.destroy).pack()

    def update_param_value(self, block, param, entry):
        value = entry.get()
        block.values[param] = value if entry['foreground'] != 'grey' else ""
        self.update_code_preview()

    def update_code_preview(self):
        self.code_preview.delete(1.0, tk.END)
        for block in self.execution_blocks:
            code = block.definition.template
            for param, value in block.values.items():
                code = code.replace(f"{{{param}}}", value)
            self.code_preview.insert(tk.END, code + "\n\n")

    def delete_block(self, index):
        del self.execution_blocks[index]
        self.update_execution_panel()

    def copy_block(self, index):
        self.clipboard = self.execution_blocks[index]

    def cut_block(self, index):
        self.clipboard = self.execution_blocks.pop(index)
        self.update_execution_panel()

    def paste_block(self, index):
        if self.clipboard:
            self.execution_blocks.insert(index, self.clipboard)
            self.update_execution_panel()

    def import_config(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            try:
                with open(filepath) as f:
                    self.block_definitions = [
                        CodeBlockDef(item["name"], item["params"], item["template"]) 
                        for item in json.load(f)
                    ]
                self.update_preset_panel()
                messagebox.showinfo("成功", "配置导入成功！")
            except Exception as e:
                messagebox.showerror("导入错误", f"导入失败: {str(e)}")

    def export_config(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filepath:
            try:
                with open(filepath, "w") as f:
                    json.dump([
                        {"name": b.name, "params": b.params, "template": b.template}
                        for b in self.block_definitions
                    ], f, indent=2)
                messagebox.showinfo("成功", "配置导出成功！")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出失败: {str(e)}")

    def save_progress(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filepath:
            try:
                with open(filepath, "w") as f:
                    json.dump([
                        {"definition": self.block_definitions.index(b.definition), "values": b.values}
                        for b in self.execution_blocks
                    ], f, indent=2)
                messagebox.showinfo("成功", "进度保存成功！")
            except Exception as e:
                messagebox.showerror("保存错误", f"保存失败: {str(e)}")

    def load_progress(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            try:
                with open(filepath) as f:
                    progress_data = json.load(f)
                self.execution_blocks = [
                    CodeBlockInstance(
                        self.block_definitions[item["definition"]],
                        item["values"]
                    ) for item in progress_data
                ]
                self.update_execution_panel()
                messagebox.showinfo("成功", "进度加载成功！")
            except Exception as e:
                messagebox.showerror("加载错误", f"加载失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeBlockEditor(root)
    root.geometry("1280x720")
    root.mainloop()
    