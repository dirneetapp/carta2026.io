import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mimetypes
import shutil
import urllib.request
import urllib.parse

MENU_FILE = 'menu.json'

# Theme Colors
COLOR_BG = "#121212"
COLOR_SURFACE = "#1e1e1e"
COLOR_PRIMARY = "#d4af37" # Gold
COLOR_TEXT = "#e0e0e0"
COLOR_TEXT_MUTED = "#a0a0a0"
FONT_MAIN = ("Segoe UI", 10)
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_TITLE = ("Playfair Display", 20, "bold")

class MenuManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Carta - Bar Sergios")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLOR_BG)
        
        self.setup_styles()
        
        self.data = self.load_menu()
        self.normalize_images()
        self.save_menu()
        
        self.create_widgets()
        self.refresh_tree()
        self.generate_site() # Ensure site is up to date with new template

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure Colors and Fonts
        style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=FONT_MAIN, borderwidth=0)
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Surface.TFrame", background=COLOR_SURFACE)
        
        # Buttons
        style.configure("TButton", 
                        background=COLOR_SURFACE, 
                        foreground=COLOR_PRIMARY, 
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor=COLOR_PRIMARY,
                        padding=6)
        style.map("TButton", 
                  background=[('active', COLOR_PRIMARY), ('pressed', COLOR_PRIMARY)], 
                  foreground=[('active', COLOR_BG), ('pressed', COLOR_BG)])
        
        # Treeview
        style.configure("Treeview", 
                        background=COLOR_SURFACE, 
                        foreground=COLOR_TEXT, 
                        fieldbackground=COLOR_SURFACE,
                        font=FONT_MAIN,
                        rowheight=35,
                        borderwidth=0)
        style.configure("Treeview.Heading", 
                        background=COLOR_BG, 
                        foreground=COLOR_PRIMARY, 
                        font=FONT_HEADER,
                        relief="flat",
                        padding=10)
        style.map("Treeview", 
                  background=[('selected', COLOR_PRIMARY)], 
                  foreground=[('selected', COLOR_BG)])
        
        # Entries and Combobox
        style.configure("TEntry", fieldbackground=COLOR_SURFACE, foreground=COLOR_TEXT, insertcolor=COLOR_TEXT, padding=5)
        style.configure("TCombobox", fieldbackground=COLOR_SURFACE, foreground=COLOR_TEXT, arrowcolor=COLOR_PRIMARY, padding=5)
        
        # Labels
        style.configure("TLabel", background=COLOR_SURFACE, foreground=COLOR_TEXT)
        style.configure("Header.TLabel", background=COLOR_BG, foreground=COLOR_PRIMARY, font=FONT_TITLE)

        # Scrollbar
        style.configure("Vertical.TScrollbar", background=COLOR_SURFACE, troughcolor=COLOR_BG, borderwidth=0, arrowcolor=COLOR_PRIMARY)

    def load_menu(self):
        if not os.path.exists(MENU_FILE):
            return {"categories": []}
        try:
            with open(MENU_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "El archivo menu.json está corrupto.")
            return {"categories": []}

    def save_menu(self):
        try:
            with open(MENU_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self.generate_site()
            self.set_status("Cambios guardados y web actualizada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def ensure_assets_dir(self):
        d = os.path.join(os.getcwd(), 'assets')
        if not os.path.exists(d):
            os.makedirs(d)
        return d

    def is_url(self, s):
        if not s:
            return False
        return s.startswith('http://') or s.startswith('https://')

    def is_asset_path(self, s):
        if not s:
            return False
        return s.startswith('assets/') or s.startswith('assets\\')

    def process_image(self, image_input, basename):
        if not image_input:
            return None
        if self.is_asset_path(image_input):
            return image_input
        assets = self.ensure_assets_dir()
        ext = ''
        if self.is_url(image_input):
            p = urllib.parse.urlparse(image_input)
            ext = os.path.splitext(p.path)[1]
            if not ext:
                try:
                    with urllib.request.urlopen(image_input) as resp:
                        ct = resp.info().get_content_type()
                    ext = mimetypes.guess_extension(ct) or '.jpg'
                except Exception:
                    ext = '.jpg'
            filename = f"{basename}{ext}"
            dest = os.path.join(assets, filename)
            try:
                with urllib.request.urlopen(image_input) as resp:
                    data = resp.read()
                with open(dest, 'wb') as f:
                    f.write(data)
                return os.path.join('assets', filename)
            except Exception:
                return image_input
        else:
            ext = os.path.splitext(image_input)[1] or '.jpg'
            filename = f"{basename}{ext}"
            dest = os.path.join(assets, filename)
            try:
                shutil.copyfile(image_input, dest)
                return os.path.join('assets', filename)
            except Exception:
                return image_input

    def normalize_images(self):
        for cat in self.data.get('categories', []):
            if cat.get('image'):
                processed = self.process_image(cat['image'], f"cat_{cat['id']}")
                if processed:
                    cat['image'] = processed
            for sub in cat.get('subcategories', []):
                if sub.get('image'):
                    processed = self.process_image(sub['image'], f"subcat_{cat['id']}_{sub['id']}")
                    if processed:
                        sub['image'] = processed
            for item in cat.get('items', []):
                if item.get('image'):
                    processed = self.process_image(item['image'], f"item_{cat['id']}_{item['id']}")
                    if processed:
                        item['image'] = processed

    def generate_site(self):
        # HTML Template parts
        header_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bar Sergios - {title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body class="theme-{theme}">
    <button class="menu-toggle" onclick="toggleMenu()">☰</button>
    
    <div id="mobileMenu" class="mobile-menu-overlay">
        <button class="menu-toggle" style="position:absolute; top:1rem; right:1rem; border:none; background:none; font-size:2rem;" onclick="toggleMenu()">✕</button>
        {mobile_links}
    </div>

    <header class="hero">
        <a href="index.html" class="home-btn" title="Volver al inicio">🏠</a>
        <div class="hero-content">
            <h1>Bar Sergios</h1>
            <p class="subtitle">Gastronomía & Buen Ambiente</p>
        </div>
    </header>

    <main class="container">
        <div class="menu-container">
            {content}
        </div>
    </main>

    <div id="imageModal" class="image-modal" onclick="hideImageModal()">
        <img id="imageModalImg" class="image-modal-content" alt="Imagen">
    </div>

    <footer>
        <p>&copy; 2026 Bar Sergios. Todos los derechos reservados.</p>
    </footer>

    <script>
        function toggleMenu() {{
            document.getElementById('mobileMenu').classList.toggle('open');
        }}
        function showImageModal(src) {{
            var img = document.getElementById('imageModalImg');
            img.src = src;
            document.getElementById('imageModal').classList.add('open');
        }}
        function hideImageModal() {{
            document.getElementById('imageModal').classList.remove('open');
        }}
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') hideImageModal();
        }});
    </script>
</body>
</html>"""

        # Generate Navigation Links
        nav_links = []
        mobile_links = []
        
        for cat in self.data['categories']:
            link = f'<a href="{cat["id"]}.html" class="nav-btn {{active_{cat["id"]}}}">{cat["name"]}</a>'
            nav_links.append(link)
            
            m_link = f'<a href="{cat["id"]}.html" class="mobile-menu-link {{active_{cat["id"]}}}">{cat["name"]}</a>'
            mobile_links.append(m_link)
        
        nav_html = "\n".join(nav_links)
        mobile_html = "\n".join(mobile_links)

        nav_html = "\n".join(nav_links)
        mobile_html = "\n".join(mobile_links)

        # 1. Generate Index (Category Grid)
        self.generate_index_page(nav_html, mobile_html, header_template)

        # 2. Generate Category Pages
        for cat in self.data['categories']:
            self.generate_category_page(cat, nav_html, mobile_html, header_template)

    def generate_index_page(self, nav_html, mobile_html, template):
        # Clean up active states for index
        import re
        current_nav = re.sub(r'\{active_\w+\}', '', nav_html)
        current_mobile = re.sub(r'\{active_\w+\}', '', mobile_html)
        
        # Generate Grid HTML
        grid_html = '<section class="menu-section"><h2 class="section-title" style="text-align:center; display:block; border:none;">Nuestra Carta</h2><div class="category-grid">'
        
        for cat in self.data['categories']:
            # Use category image or a default placeholder if missing
            img_src = cat.get('image', 'https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=500&q=80')
            
            grid_html += f"""
            <a href="{cat['id']}.html" class="category-card">
                <img src="{img_src}" alt="{cat['name']}" class="category-card-image">
                <div class="category-card-title">{cat['name']}</div>
                <div class="category-card-description">{cat.get('description', '')}</div>
            </a>
            """
        grid_html += "</div></section>"

        # Fill Template
        page_content = template.format(
            title="Inicio",
            theme="gold", # Default theme for index
            nav_links=current_nav,
            mobile_links=current_mobile,
            content=grid_html
        )

        with open("index.html", 'w', encoding='utf-8') as f:
            f.write(page_content)

    def generate_category_page(self, category, nav_html, mobile_html, template):
        # Highlight active button
        current_nav = nav_html.replace(f'{{active_{category["id"]}}}', 'active')
        current_mobile = mobile_html.replace(f'{{active_{category["id"]}}}', 'active')
        
        # Remove other placeholders
        import re
        current_nav = re.sub(r'\{active_\w+\}', '', current_nav)
        current_mobile = re.sub(r'\{active_\w+\}', '', current_mobile)
        
        # Get theme (default to gold if not set)
        theme = category.get('theme', 'gold')

        # Generate Items HTML with subcategories
        items_html = f'<section class="menu-section"><h2 class="section-title">{category["name"]}</h2><div class="items-list">'
        for item in category.get('items', []):
            image_html = (
                f"<img src='{item['image']}' alt='{item['name']}' class='item-image' onclick=\"showImageModal('{item['image']}')\">"
                if item.get('image') else ''
            )
            items_html += f"""
            <article class="menu-item">
                {image_html}
                <div class="item-details">
                    <h3 class="item-name">{item['name']}</h3>
                    <p class="item-description">{item['description']}</p>
                </div>
                <div class="item-price">{item['price']:.2f} €</div>
            </article>
            """
        items_html += "</div></section>"

        for sub in category.get('subcategories', []):
            sub_img = sub.get('image')
            items_html += f"<section class='menu-section'><h3 class='subsection-title'>{sub['name']}</h3><div class='items-list'>"
            for item in sub.get('items', []):
                image_html = (
                    f"<img src='{item['image']}' alt='{item['name']}' class='item-image' onclick=\"showImageModal('{item['image']}')\">"
                    if item.get('image') else ''
                )
                items_html += f"""
                <article class="menu-item">
                    {image_html}
                    <div class="item-details">
                        <h3 class="item-name">{item['name']}</h3>
                        <p class="item-description">{item['description']}</p>
                    </div>
                    <div class="item-price">{item['price']:.2f} €</div>
                </article>
                """
            items_html += "</div></section>"

        # Fill Template
        page_content = template.format(
            title=category['name'],
            theme=theme,
            nav_links=current_nav,
            mobile_links=current_mobile,
            content=items_html
        )

        filename = f"{category['id']}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_content)

    def on_double_click(self, event):
        """Handle double-click event on treeview items"""
        selected = self.tree.selection()
        if selected:
            self.edit_selected()

    def add_category(self):
        themes = ["gold", "ocean", "sunset", "forest", "lavender"]
        fields = [
            ("ID de la categoría (ej: postres)", "id", "entry", None),
            ("Nombre visible (ej: Postres)", "name", "entry", None),
            ("Tema de color", "theme", "combo", themes),
            ("Descripción (Opcional)", "description", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        result = self.show_custom_dialog("Nueva Categoría", fields)
        
        if result:
            cat_id = result['id']
            name = result['name']
            _, theme = result['theme']
            image = result['image']
            
            if not cat_id or not name:
                messagebox.showwarning("Aviso", "Todos los campos son obligatorios.")
                return
                
            if any(c['id'] == cat_id for c in self.data['categories']):
                messagebox.showerror("Error", "Ya existe una categoría con ese ID.")
                return
            
            new_cat = {
                "id": cat_id,
                "name": name,
                "theme": theme,
                "items": []
            }
            if image:
                processed = self.process_image(image, f"cat_{cat_id}")
                if processed:
                    new_cat["image"] = processed
            if result['description']:
                new_cat["description"] = result['description']

            self.data['categories'].append(new_cat)
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Categoría '{name}' añadida.")

    def add_item(self):
        if not self.data['categories']:
            messagebox.showwarning("Aviso", "Primero crea una categoría.")
            return

        cat_names = [c['name'] for c in self.data['categories']]
        
        fields = [
            ("Categoría", "cat_idx", "combo", cat_names),
            ("ID Producto (ej: bravas)", "id", "entry", None),
            ("Nombre del producto", "name", "entry", None),
            ("Precio (ej: 10.50)", "price", "entry", None),
            ("Descripción", "desc", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        
        result = self.show_custom_dialog("Añadir Producto", fields)
        
        if result:
            cat_idx, _ = result['cat_idx']
            if cat_idx == -1: return
            
            cat = self.data['categories'][cat_idx]
            item_id = result['id']
            name = result['name']
            desc = result['desc']
            image = result['image']
            
            try:
                price = float(result['price'])
            except ValueError:
                messagebox.showerror("Error", "Precio inválido.")
                return
            
            if not item_id or not name:
                messagebox.showerror("Error", "ID y Nombre son obligatorios.")
                return
                
            if any(i['id'] == item_id for i in cat['items']):
                messagebox.showerror("Error", "ID de producto duplicado en esta categoría.")
                return
                
            new_item = {
                "id": item_id,
                "name": name,
                "description": desc,
                "price": price
            }
            if image:
                processed = self.process_image(image, f"item_{cat['id']}_{item_id}")
                if processed:
                    new_item["image"] = processed

            cat['items'].append(new_item)
            
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Producto '{name}' añadido.")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="Gestión de Carta", style="Header.TLabel")
        title_label.pack(pady=(0, 20), anchor="center")

        toolbar = ttk.Frame(main_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        ttk.Button(toolbar, text="➕ Añadir Categoría", command=self.add_category).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="➕ Añadir Producto", command=self.add_item).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="✏️ Editar Seleccionado", command=self.edit_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="➕ Añadir Subcategoría", command=self.add_subcategory).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="🗑️ Borrar Seleccionado", command=self.delete_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="🔄 Refrescar", command=self.refresh_tree).pack(side=tk.RIGHT)
        ttk.Button(toolbar, text="Ver Productos", command=self.open_products_dialog).pack(side=tk.RIGHT, padx=(0, 10))

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('id', 'name', 'theme', 'price', 'description')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Nombre')
        self.tree.heading('theme', text='Tema')
        self.tree.heading('price', text='Precio (€)')
        self.tree.heading('description', text='Descripción')
        self.tree.column('id', width=100, anchor='center')
        self.tree.column('name', width=200)
        self.tree.column('theme', width=100, anchor='center')
        self.tree.column('price', width=100, anchor='e')
        self.tree.column('description', width=300)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-Button-1>", self.on_double_click)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=0, anchor=tk.W, bg=COLOR_PRIMARY, fg=COLOR_BG, font=("Segoe UI", 9, "bold"), padx=10, pady=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message):
        if hasattr(self, 'status_var') and isinstance(self.status_var, tk.StringVar):
            self.status_var.set(message)
            self.root.after(3000, lambda: self.status_var.set("Listo"))

    def refresh_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for cat in self.data.get('categories', []):
            # Insert Category as a parent node
            theme = cat.get('theme', 'gold')
            cat_node = self.tree.insert('', 'end', iid=f"cat_{cat['id']}", values=(cat['id'], cat['name'], theme, '', '--- CATEGORÍA ---'))
            # Subcategorías
            for sub in cat.get('subcategories', []):
                sub_node = self.tree.insert(cat_node, 'end', iid=f"subcat_{cat['id']}_{sub['id']}", values=(sub['id'], sub.get('name', ''), '', '', '--- SUBCATEGORÍA ---'))
                for item in sub.get('items', []):
                    self.tree.insert(sub_node, 'end', iid=f"item_{cat['id']}_{item['id']}", values=(item['id'], item['name'], '', f"{item['price']:.2f}", item.get('description', '')))
            # Items sin subcategoría
            for item in cat.get('items', []):
                self.tree.insert(cat_node, 'end', iid=f"item_{cat['id']}_{item['id']}", values=(item['id'], item['name'], '', f"{item['price']:.2f}", item.get('description', '')))
                
        for item in self.tree.get_children():
            self.tree.item(item, open=True)

    def show_custom_dialog(self, title, fields, default_values=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()

        field_height = 70
        dialog_height = min(150 + (len(fields) * field_height), 650)
        dialog_width = 550
        dialog.geometry(f"{dialog_width}x{dialog_height}")

        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog_width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog_height // 2)
        dialog.geometry(f"+{x}+{y}")

        canvas = tk.Canvas(dialog, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Surface.TFrame", padding="20")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=dialog_width-60)
        canvas.configure(yscrollcommand=scrollbar.set)

        entries = {}
        for label_text, key, widget_type, options in fields:
            ttk.Label(scrollable_frame, text=label_text).pack(anchor="w", pady=(10, 5))
            if widget_type == 'entry':
                if key == 'image':
                    row = ttk.Frame(scrollable_frame, style="Surface.TFrame")
                    row.pack(fill=tk.X)
                    entry = ttk.Entry(row)
                    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    if default_values and key in default_values:
                        entry.insert(0, str(default_values[key]))
                    def _select_file(e=entry):
                        path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.gif;*.webp"), ("Todos", "*.*")])
                        if path:
                            e.delete(0, tk.END)
                            e.insert(0, path)
                    def _paste_clipboard(e=entry):
                        try:
                            text = self.root.clipboard_get()
                            if text:
                                e.delete(0, tk.END)
                                e.insert(0, text)
                        except Exception:
                            pass
                    ttk.Button(row, text="Seleccionar…", command=_select_file).pack(side=tk.LEFT, padx=6)
                    ttk.Button(row, text="Pegar", command=_paste_clipboard).pack(side=tk.LEFT)
                    entries[key] = entry
                else:
                    entry = ttk.Entry(scrollable_frame)
                    entry.pack(fill=tk.X)
                    if default_values and key in default_values:
                        entry.insert(0, str(default_values[key]))
                    entries[key] = entry
            elif widget_type == 'combo':
                combo = ttk.Combobox(scrollable_frame, values=options, state="readonly")
                combo.pack(fill=tk.X)
                if default_values and key in default_values:
                    try:
                        combo.current(options.index(default_values[key]))
                    except (ValueError, IndexError):
                        if options:
                            combo.current(0)
                elif options:
                    combo.current(0)
                entries[key] = combo

        def on_submit():
            result = {}
            for key, widget in entries.items():
                if isinstance(widget, ttk.Combobox):
                    result[key] = (widget.current(), widget.get())
                else:
                    result[key] = widget.get().strip()
            dialog.result = result
            dialog.destroy()

        ttk.Button(scrollable_frame, text="💾 Guardar", command=on_submit).pack(pady=20, fill=tk.X)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        scrollbar.pack(side="right", fill="y", pady=20, padx=(0, 20))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        canvas.bind('<Enter>', _bind_mousewheel)
        canvas.bind('<Leave>', _unbind_mousewheel)

        self.root.wait_window(dialog)
        return getattr(dialog, 'result', None)

    def add_category(self):
        themes = ["gold", "ocean", "sunset", "forest", "lavender"]
        fields = [
            ("ID de la categoría (ej: postres)", "id", "entry", None),
            ("Nombre visible (ej: Postres)", "name", "entry", None),
            ("Tema de color", "theme", "combo", themes),
            ("Descripción (Opcional)", "description", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        result = self.show_custom_dialog("Nueva Categoría", fields)
        if result:
            cat_id = result['id']
            name = result['name']
            _, theme = result['theme']
            image = result.get('image', '')
            if not cat_id or not name:
                messagebox.showwarning("Aviso", "Todos los campos son obligatorios.")
                return
            if any(c['id'] == cat_id for c in self.data['categories']):
                messagebox.showerror("Error", "Ya existe una categoría con ese ID.")
                return
            new_cat = {"id": cat_id, "name": name, "theme": theme, "items": [], "subcategories": []}
            if result.get('description'):
                new_cat["description"] = result['description']
            if image:
                new_cat["image"] = image
            self.data['categories'].append(new_cat)
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Categoría '{name}' añadida.")

    def add_item(self):
        if not self.data['categories']:
            messagebox.showwarning("Aviso", "Primero crea una categoría.")
            return
        cat_names = [c['name'] for c in self.data['categories']]
        step1 = self.show_custom_dialog("Seleccionar categoría", [("Categoría", "cat_idx", "combo", cat_names)])
        if not step1:
            return
        cat_idx, _ = step1['cat_idx']
        if cat_idx == -1:
            return
        cat = self.data['categories'][cat_idx]
        sub_names = ["Sin subcategoría"] + [s['name'] for s in cat.get('subcategories', [])]
        fields = [
            ("Subcategoría (Opcional)", "sub_idx", "combo", sub_names),
            ("ID Producto (ej: bravas)", "id", "entry", None),
            ("Nombre del producto", "name", "entry", None),
            ("Precio (ej: 10.50)", "price", "entry", None),
            ("Descripción", "desc", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        result = self.show_custom_dialog("Añadir Producto", fields)
        if result:
            item_id = result['id']
            name = result['name']
            desc = result['desc']
            image = result.get('image', '')
            sub_idx, _ = result['sub_idx'] if isinstance(result.get('sub_idx'), tuple) else (-1, "")
            try:
                price = float(result['price'])
            except ValueError:
                messagebox.showerror("Error", "Precio inválido.")
                return
            if not item_id or not name:
                messagebox.showerror("Error", "ID y Nombre son obligatorios.")
                return
            # Duplicados en categoría y subcategorías
            if any(i['id'] == item_id for i in cat.get('items', [])):
                messagebox.showerror("Error", "ID de producto duplicado en esta categoría.")
                return
            for s in cat.get('subcategories', []):
                if any(i['id'] == item_id for i in s.get('items', [])):
                    messagebox.showerror("Error", "ID de producto duplicado en esta categoría.")
                    return
            new_item = {"id": item_id, "name": name, "description": desc, "price": price}
            if image:
                processed = self.process_image(image, f"item_{cat['id']}_{item_id}")
                if processed:
                    new_item["image"] = processed
            if sub_idx <= 0:
                cat.setdefault('items', []).append(new_item)
            else:
                sub = cat.get('subcategories', [])[sub_idx-1]
                sub.setdefault('items', []).append(new_item)
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Producto '{name}' añadido.")

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona algo para editar.")
            return
            
        item_iid = selected[0]
        
        if item_iid.startswith("cat_"):
            self.edit_category(item_iid)
        elif item_iid.startswith("subcat_"):
            self.edit_subcategory(item_iid)
        elif item_iid.startswith("item_"):
            self.edit_item(item_iid)

    def add_subcategory(self):
        if not self.data['categories']:
            messagebox.showwarning("Aviso", "Primero crea una categoría.")
            return
        cat_names = [c['name'] for c in self.data['categories']]
        step1 = self.show_custom_dialog("Seleccionar categoría", [("Categoría", "cat_idx", "combo", cat_names)])
        if not step1:
            return
        cat_idx, _ = step1['cat_idx']
        if cat_idx == -1:
            return
        cat = self.data['categories'][cat_idx]
        fields = [
            ("ID Subcategoría", "id", "entry", None),
            ("Nombre", "name", "entry", None),
            ("Descripción (Opcional)", "description", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        result = self.show_custom_dialog("Añadir Subcategoría", fields)
        if result:
            sub_id = result['id']
            name = result['name']
            if not sub_id or not name:
                messagebox.showwarning("Aviso", "ID y Nombre son obligatorios.")
                return
            if any(s['id'] == sub_id for s in cat.get('subcategories', [])):
                messagebox.showerror("Error", "ID de subcategoría duplicado en esta categoría.")
                return
            new_sub = {"id": sub_id, "name": name, "items": []}
            if result.get('description'):
                new_sub['description'] = result['description']
            if result.get('image'):
                processed = self.process_image(result['image'], f"subcat_{cat['id']}_{sub_id}")
                if processed:
                    new_sub['image'] = processed
            cat.setdefault('subcategories', []).append(new_sub)
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Subcategoría '{name}' añadida.")

    def edit_subcategory(self, item_iid):
        _, cat_id, sub_id = item_iid.split("_", 2)
        category = next((c for c in self.data['categories'] if c['id'] == cat_id), None)
        if not category:
            messagebox.showerror("Error", "Categoría no encontrada.")
            return
        sub = next((s for s in category.get('subcategories', []) if s['id'] == sub_id), None)
        if not sub:
            messagebox.showerror("Error", "Subcategoría no encontrada.")
            return
        fields = [
            ("Nombre", "name", "entry", None),
            ("Descripción (Opcional)", "description", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        default_values = {
            'name': sub.get('name', ''),
            'description': sub.get('description', ''),
            'image': sub.get('image', '')
        }
        result = self.show_custom_dialog(f"Editar Subcategoría: {sub_id}", fields, default_values)
        if result:
            name = result['name']
            if not name:
                messagebox.showwarning("Aviso", "El nombre es obligatorio.")
                return
            sub['name'] = name
            if result.get('description'):
                sub['description'] = result['description']
            elif 'description' in sub:
                del sub['description']
            if result.get('image'):
                processed = self.process_image(result['image'], f"subcat_{cat_id}_{sub_id}")
                if processed:
                    sub['image'] = processed
            elif 'image' in sub:
                del sub['image']
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Subcategoría '{name}' actualizada.")
    
    def edit_category(self, item_iid):
        cat_id = item_iid.split("_", 1)[1]
        category = next((c for c in self.data['categories'] if c['id'] == cat_id), None)
        
        if not category:
            messagebox.showerror("Error", "Categoría no encontrada.")
            return
        
        themes = ["gold", "ocean", "sunset", "forest", "lavender"]
        
        fields = [
            ("Nombre visible", "name", "entry", None),
            ("Tema de color", "theme", "combo", themes),
            ("Descripción (Opcional)", "description", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        
        # Prepare default values
        default_values = {
            'name': category.get('name', ''),
            'theme': category.get('theme', 'gold'),
            'description': category.get('description', ''),
            'image': category.get('image', '')
        }
        
        result = self.show_custom_dialog(f"Editar Categoría: {cat_id}", fields, default_values)
        
        if result:
            name = result['name']
            _, theme = result['theme']
            
            if not name:
                messagebox.showwarning("Aviso", "El nombre es obligatorio.")
                return
            
            category['name'] = name
            category['theme'] = theme
            
            if result['description']:
                category['description'] = result['description']
            elif 'description' in category:
                del category['description']
            
            if result['image']:
                processed = self.process_image(result['image'], f"cat_{cat_id}")
                if processed:
                    category['image'] = processed
            elif 'image' in category:
                del category['image']
            
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Categoría '{name}' actualizada.")
    
    def edit_item(self, item_iid):
        _, cat_id, item_id = item_iid.split("_", 2)

        category = next((c for c in self.data['categories'] if c['id'] == cat_id), None)
        if not category:
            messagebox.showerror("Error", "Categoría no encontrada.")
            return

        item = next((i for i in category.get('items', []) if i['id'] == item_id), None)
        if not item:
            for sub in category.get('subcategories', []):
                item = next((i for i in sub.get('items', []) if i['id'] == item_id), None)
                if item:
                    break
        if not item:
            messagebox.showerror("Error", "Producto no encontrado.")
            return
        
        fields = [
            ("Nombre del producto", "name", "entry", None),
            ("Precio (ej: 10.50)", "price", "entry", None),
            ("Descripción", "desc", "entry", None),
            ("URL Imagen (Opcional)", "image", "entry", None)
        ]
        
        # Prepare default values
        default_values = {
            'name': item.get('name', ''),
            'price': str(item.get('price', '')),
            'desc': item.get('description', ''),
            'image': item.get('image', '')
        }
        
        result = self.show_custom_dialog(f"Editar Producto: {item_id}", fields, default_values)
        
        if result:
            name = result['name']
            desc = result['desc']
            image = result['image']
            
            try:
                price = float(result['price'])
            except ValueError:
                messagebox.showerror("Error", "Precio inválido.")
                return
            
            if not name:
                messagebox.showerror("Error", "El nombre es obligatorio.")
                return
            
            item['name'] = name
            item['description'] = desc
            item['price'] = price
            
            if image:
                processed = self.process_image(image, f"item_{cat_id}_{item_id}")
                if processed:
                    item['image'] = processed
            elif 'image' in item:
                del item['image']
            
            self.save_menu()
            self.refresh_tree()
            self.set_status(f"Producto '{name}' actualizado.")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona algo para borrar.")
            return
            
        item_iid = selected[0]
        
        if item_iid.startswith("cat_"):
            cat_id = item_iid.split("_", 1)[1]
            if messagebox.askyesno("Confirmar", f"¿Borrar categoría '{cat_id}' y todos sus productos?"):
                self.data['categories'] = [c for c in self.data['categories'] if c['id'] != cat_id]
                self.save_menu()
                self.refresh_tree()
                self.set_status(f"Categoría '{cat_id}' eliminada.")
        elif item_iid.startswith("subcat_"):
            _, cat_id, sub_id = item_iid.split("_", 2)
            if messagebox.askyesno("Confirmar", f"¿Borrar subcategoría '{sub_id}' y sus productos?"):
                for cat in self.data['categories']:
                    if cat['id'] == cat_id:
                        cat['subcategories'] = [s for s in cat.get('subcategories', []) if s['id'] != sub_id]
                        break
                self.save_menu()
                self.refresh_tree()
                self.set_status(f"Subcategoría '{sub_id}' eliminada.")
        elif item_iid.startswith("item_"):
            _, cat_id, item_id = item_iid.split("_", 2)
            if messagebox.askyesno("Confirmar", f"¿Borrar producto '{item_id}'?"):
                for cat in self.data['categories']:
                    if cat['id'] == cat_id:
                        for sub in cat.get('subcategories', []):
                            sub['items'] = [i for i in sub.get('items', []) if i['id'] != item_id]
                        cat['items'] = [i for i in cat.get('items', []) if i['id'] != item_id]
                        break
                self.save_menu()
                self.refresh_tree()
                self.set_status(f"Producto '{item_id}' eliminado.")

    def open_products_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Listado de Productos")
        dialog.configure(bg=COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        width, height = 900, 550
        dialog.geometry(f"{width}x{height}")
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

        content = ttk.Frame(dialog, padding="20", style="Surface.TFrame")
        content.pack(fill=tk.BOTH, expand=True)

        filters = ttk.Frame(content, padding="0", style="Surface.TFrame")
        filters.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(filters, text="Categoría").pack(side=tk.LEFT)
        cat_names = ["Todas"] + [c['name'] for c in self.data.get('categories', [])]
        category_combo = ttk.Combobox(filters, values=cat_names, state="readonly")
        if cat_names:
            category_combo.current(0)
        category_combo.pack(side=tk.LEFT, padx=10)
        ttk.Label(filters, text="Buscar").pack(side=tk.LEFT)
        search_entry = ttk.Entry(filters)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        columns = ('cat_id', 'cat_name', 'item_id', 'name', 'price', 'description')
        tree = ttk.Treeview(content, columns=columns, show='headings', selectmode='browse')
        tree.heading('cat_id', text='Cat ID')
        tree.heading('cat_name', text='Categoría')
        tree.heading('item_id', text='ID Producto')
        tree.heading('name', text='Nombre')
        tree.heading('price', text='Precio (€)')
        tree.heading('description', text='Descripción')
        tree.column('cat_id', width=120, anchor='center')
        tree.column('cat_name', width=180)
        tree.column('item_id', width=120, anchor='center')
        tree.column('name', width=220)
        tree.column('price', width=100, anchor='e')
        tree.column('description', width=300)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(content, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_dialog_tree():
            for iid in tree.get_children():
                tree.delete(iid)
            selected_cat = category_combo.get()
            query = search_entry.get().lower().strip()
            for cat in self.data.get('categories', []):
                if selected_cat and selected_cat != "Todas" and cat.get('name') != selected_cat:
                    continue
                # Items sin subcategoría
                for item in cat.get('items', []):
                    name = item.get('name', '')
                    desc = item.get('description', '')
                    if query and (query not in name.lower()) and (query not in desc.lower()):
                        continue
                    tree.insert('', 'end', iid=f"all_{cat['id']}_{item['id']}", values=(cat['id'], cat['name'], item['id'], name, f"{item.get('price', 0):.2f}", desc))
                # Items en subcategorías
                for sub in cat.get('subcategories', []):
                    for item in sub.get('items', []):
                        name = item.get('name', '')
                        desc = item.get('description', '')
                        if query and (query not in name.lower()) and (query not in desc.lower()):
                            continue
                        tree.insert('', 'end', iid=f"all_{cat['id']}_{item['id']}", values=(cat['id'], cat['name'], item['id'], name, f"{item.get('price', 0):.2f}", desc))

        def get_selected_ids():
            sel = tree.selection()
            if not sel:
                return None, None
            iid = sel[0]
            try:
                _, cat_id, item_id = iid.split('_', 2)
                return cat_id, item_id
            except Exception:
                return None, None

        def on_edit():
            cat_id, item_id = get_selected_ids()
            if not cat_id:
                messagebox.showwarning("Aviso", "Selecciona un producto.")
                return
            self.edit_item(f"item_{cat_id}_{item_id}")
            refresh_dialog_tree()

        def on_delete():
            cat_id, item_id = get_selected_ids()
            if not cat_id:
                messagebox.showwarning("Aviso", "Selecciona un producto.")
                return
            if messagebox.askyesno("Confirmar", f"¿Borrar producto '{item_id}'?"):
                for cat in self.data['categories']:
                    if cat['id'] == cat_id:
                        for sub in cat.get('subcategories', []):
                            sub['items'] = [i for i in sub.get('items', []) if i['id'] == item_id]
                        cat['items'] = [i for i in cat.get('items', []) if i['id'] != item_id]
                        break
                self.save_menu()
                self.refresh_tree()
                refresh_dialog_tree()
                self.set_status(f"Producto '{item_id}' eliminado.")

        tree.bind("<Double-Button-1>", lambda e: on_edit())
        category_combo.bind('<<ComboboxSelected>>', lambda e: refresh_dialog_tree())
        search_entry.bind('<KeyRelease>', lambda e: refresh_dialog_tree())

        actions = ttk.Frame(dialog, padding="10", style="Surface.TFrame")
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="✏️ Editar", command=on_edit).pack(side=tk.LEFT)
        ttk.Button(actions, text="🗑️ Eliminar", command=on_delete).pack(side=tk.LEFT, padx=10)
        ttk.Button(actions, text="Cerrar", command=dialog.destroy).pack(side=tk.RIGHT)

        refresh_dialog_tree()

if __name__ == "__main__":
    root = tk.Tk()
    app = MenuManagerApp(root)
    root.mainloop()
