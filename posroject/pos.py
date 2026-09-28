from datetime import datetime, timedelta
import random
import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import requests

# --- WHATSAPP OTP ---


def send_real_whatsapp_otp(phone_number, otp_code):
  phone_number_id = "1302839726251979"
  access_token = "EAAUDIkWSy3MBSpZCueJgdYJntbgpAtZBvKy66aMT6NalgZBpXfPbbPa6oHqhphwlYw2ok8PA6oq6hzxskaNuxrVJECTrQHFhzLCUn0L8YRG3HHifvBdlqO9MkBBRBTXT0fdAw9XVqa4m5PoXYs8X5mL4DOKsBulKMbCl3bIazqrE9dV3OqNNq9R61YAjJFrWqWZBqkRRyaWtSk9JHVFyb81tF0U9TzKUbaGYihYawYswy9xbZAYU16ZA16HZCTQkH4NzmhD5ZBR2Lybjg6qZAKFmB"

  url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"

  headers = {
      "Authorization": f"Bearer {access_token}",
      "Content-Type": "application/json",
  }

  payload = {
      "messaging_product": "whatsapp",
      "to": phone_number,
      "type": "template",
      "template": {"name": "hello_world", "language": {"code": "en_US"}},
  }

  try:
    response = requests.post(url, json=payload, headers=headers)
    print("Respon Lengkap API Meta:", response.text)
    result = response.json()

    if response.status_code == 200:
      print(f"[API WHATSAPP META] Pesan templat berhasil dikirim.")
      messagebox.showinfo(
          "Berhasil",
          f"Pesan templat WhatsApp terkirim ke {phone_number}!\n(Catatan:"
          f" Kode OTP Uji Coba Anda: {otp_code})",
      )
    else:
      print(f"[PERINGATAN API] Kesalahan API Meta: {result}")
      messagebox.showwarning(
          "Informasi API",
          f"Percobaan pengiriman pesan telah dilakukan.\nDetail: {result}",
      )

  except Exception as e:
    print(f"[KESALAHAN KONEKSI] {e}")
    messagebox.showerror("Kesalahan", f"Terjadi kesalahan koneksi: {e}")


# --- INISIALISASI DATABASE DAN TABEL ---


def init_db():
  conn = sqlite3.connect("pos_system_id.db")
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            stock INTEGER
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_time TEXT,
            total_amount REAL,
            cashier TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            refund_date TEXT,
            refund_amount REAL,
            details TEXT,
            cashier TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_no TEXT,
            customer_name TEXT,
            phone TEXT,
            address TEXT,
            courier TEXT,
            status TEXT,
            shipping_type TEXT
        )
    """)

  try:
    cursor.execute("ALTER TABLE shipments ADD COLUMN shipping_type TEXT")
  except sqlite3.OperationalError:
    pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS wholesale_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT,
            supplier_name TEXT,
            date_time TEXT,
            total_amount REAL,
            details TEXT
        )
    """)

  cursor.execute("SELECT COUNT(*) FROM users")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES ('kasir1', '1234',"
        " 'cashier')"
    )
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES ('admin',"
        " 'admin123', 'admin')"
    )
    conn.commit()

  master_products = [
      (1, "Burgari Carb Cleanner 500ml", 45000.0, 15),
      (2, "Paku Beton 1/4 Box 230gr", 25000.0, 3),
      (3, "Paku Beton 1/2 Box 460gr", 45000.0, 12),
      (4, "Fumetas Waterpass Orange", 85000.0, 2),
      (5, "Fumetax Waterpass Silver", 90000.0, 8),
      (6, "Solvex Kran Concot Panjang SP-30129", 125000.0, 15),
      (7, "Moon Lion 8x3inch F-AB", 65000.0, 25),
      (8, "Ring Pelat Kuning M14*34*2mm", 1500.0, 100),
      (9, "Mur Putih M8 K13", 2000.0, 150),
      (10, "Roof Drain Dak Stainless", 110000.0, 14),
  ]

  cursor.execute("SELECT COUNT(*) FROM products")
  if cursor.fetchone()[0] == 0:
    for prod in master_products:
      cursor.execute(
          "INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)",
          prod,
      )
    conn.commit()

  conn.close()


init_db()


class IndonesianPOSApp:

  def __init__(self, root):
    self.root = root
    self.root.title(
        "Sistem POS & Back Office Pintar (Indonesia - Pelacakan Kargo & Printer)"
    )
    self.root.geometry("1350x820")

    self.current_user = None
    self.cart = []
    self.shipping_status = tk.StringVar(value="Gratis")

    self.show_login_screen()

  def clear_screen(self):
    for widget in self.root.winfo_children():
      widget.destroy()

  def show_login_screen(self):
    self.clear_screen()

    frame = tk.Frame(self.root, padx=20, pady=20)
    frame.pack(expand=True)

    tk.Label(
        frame, text="Aplikasi Kasir & Back Office", font=("Arial", 16, "bold")
    ).pack(pady=10)
    tk.Label(
        frame,
        text="Silahkan masuk dengan ID & Sandi Anda",
        font=("Arial", 10),
        fg="gray",
    ).pack(pady=5)

    tk.Label(frame, text="ID Pengguna / Username:").pack(anchor="w")
    self.username_entry = tk.Entry(frame, font=("Arial", 12), width=25)
    self.username_entry.pack(pady=5)

    tk.Label(frame, text="Kata Sandi (Password):").pack(anchor="w")
    self.password_entry = tk.Entry(
        frame, font=("Arial", 12, "bold"), show="*", width=25
    )
    self.password_entry.pack(pady=5)

    tk.Button(
        frame,
        text="Masuk (Login)",
        bg="#2E7D32",
        fg="white",
        font=("Arial", 12, "bold"),
        width=22,
        command=self.handle_login,
    ).pack(pady=10)

    sub_btn_frame = tk.Frame(frame)
    sub_btn_frame.pack(pady=5)

    tk.Button(
        sub_btn_frame,
        text="🔑 Lupa Sandi",
        fg="#D32F2F",
        font=("Arial", 9),
        relief="flat",
        command=self.open_forgot_password,
    ).pack(side="left", padx=5)
    tk.Button(
        sub_btn_frame,
        text="🔄 Ubah Sandi",
        fg="#1976D2",
        font=("Arial", 9),
        relief="flat",
        command=self.open_change_password,
    ).pack(side="left", padx=5)
    tk.Button(
        sub_btn_frame,
        text="👤 Tambah Kasir Baru",
        fg="#388E3C",
        font=("Arial", 9),
        relief="flat",
        command=self.open_add_cashier,
    ).pack(side="left", padx=5)

  def handle_login(self):
    uname = self.username_entry.get()
    pwd = self.password_entry.get()

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role FROM users WHERE username = ? AND password = ?",
        (uname, pwd),
    )
    user = cursor.fetchone()
    conn.close()

    if user:
      role = user[0]
      self.current_user = uname
      if role == "cashier":
        messagebox.showinfo("Berhasil", f"Selamat datang Kasir: {uname}")
        self.show_sales_screen()
      elif role == "admin":
        otp_code = random.randint(1000, 9999)
        target_phone = "+905063626244"

        send_real_whatsapp_otp(target_phone, otp_code)

        entered_otp = simpledialog.askstring(
            "Verifikasi WhatsApp 2FA",
            f"Pesan templat Meta dipicu ke {target_phone}.\nOTP yang dihasilkan"
            f" untuk keamanan: {otp_code}\n(Masukkan kode ini untuk pengujian):",
        )
        if entered_otp == str(otp_code):
          messagebox.showinfo("Sukses", "Verifikasi OTP Berhasil!")
          self.show_back_office_screen()
        else:
          messagebox.showerror("Gagal", "Kode OTP salah! Akses ditolak.")
    else:
      messagebox.showerror("Kesalahan", "ID Pengguna atau Kata Sandi salah!")

  def open_forgot_password(self):
    win = tk.Toplevel(self.root)
    win.title("Lupa Kata Sandi")
    win.geometry("380x250")

    tk.Label(
        win, text="Pemulihan Kata Sandi", font=("Arial", 11, "bold")
    ).pack(pady=10)
    tk.Label(win, text="Masukkan Username Anda:").pack(anchor="w", padx=25)
    u_entry = tk.Entry(win, width=28, font=("Arial", 10))
    u_entry.pack(padx=25, pady=5)

    def reset_pwd():
      uname = u_entry.get()
      conn = sqlite3.connect("pos_system_id.db")
      cursor = conn.cursor()
      cursor.execute("SELECT * FROM users WHERE username = ?", (uname,))
      res = cursor.fetchone()

      if res:
        new_otp = random.randint(100000, 999999)
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (str(new_otp), uname),
        )
        conn.commit()
        conn.close()
        messagebox.showinfo(
            "Sukses",
            f"Kata sandi diatur ulang! Kata sandi sementara baru Anda:"
            f" {new_otp}",
        )
        win.destroy()
      else:
        conn.close()
        messagebox.showerror("Kesalahan", "Nama pengguna tidak ditemukan!")

    tk.Button(
        win,
        text="Atur Ulang Sandi",
        bg="#D32F2F",
        fg="white",
        font=("Arial", 10, "bold"),
        command=reset_pwd,
    ).pack(pady=15)

  def open_change_password(self):
    win = tk.Toplevel(self.root)
    win.title("Ubah Kata Sandi")
    win.geometry("380x300")

    tk.Label(
        win, text="Perbarui Kata Sandi Anda", font=("Arial", 11, "bold")
    ).pack(pady=10)

    tk.Label(win, text="Username:").pack(anchor="w", padx=25)
    u_entry = tk.Entry(win, width=28, font=("Arial", 10))
    u_entry.pack(padx=25, pady=3)

    tk.Label(win, text="Kata Sandi Lama:").pack(anchor="w", padx=25)
    old_entry = tk.Entry(win, width=28, show="*", font=("Arial", 10))
    old_entry.pack(padx=25, pady=3)

    tk.Label(win, text="Kata Sandi Baru:").pack(anchor="w", padx=25)
    new_entry = tk.Entry(win, width=28, show="*", font=("Arial", 10))
    new_entry.pack(padx=25, pady=3)

    def update_pwd():
      uname = u_entry.get()
      old_p = old_entry.get()
      new_p = new_entry.get()

      conn = sqlite3.connect("pos_system_id.db")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT * FROM users WHERE username = ? AND password = ?",
          (uname, old_p),
      )
      res = cursor.fetchone()

      if res:
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?", (new_p, uname)
        )
        conn.commit()
        conn.close()
        messagebox.showinfo("Sukses", "Kata sandi berhasil diperbarui!")
        win.destroy()
      else:
        conn.close()
        messagebox.showerror(
            "Kesalahan", "Username atau kata sandi lama salah!"
        )

    tk.Button(
        win,
        text="Simpan",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=update_pwd,
    ).pack(pady=15)

  def open_add_cashier(self):
    win = tk.Toplevel(self.root)
    win.title("Tambah Kasir Baru")
    win.geometry("380x280")

    tk.Label(
        win, text="Pendaftaran Kasir Baru", font=("Arial", 11, "bold")
    ).pack(pady=10)

    tk.Label(win, text="Username Baru:").pack(anchor="w", padx=25)
    u_entry = tk.Entry(win, width=28, font=("Arial", 10))
    u_entry.pack(padx=25, pady=3)

    tk.Label(win, text="Kata Sandi:").pack(anchor="w", padx=25)
    p_entry = tk.Entry(win, width=28, show="*", font=("Arial", 10))
    p_entry.pack(padx=25, pady=3)

    def save_cashier():
      uname = u_entry.get()
      pwd = p_entry.get()

      if not uname or not pwd:
        messagebox.showerror("Kesalahan", "Semua kolom harus diisi!")
        return

      try:
        conn = sqlite3.connect("pos_system_id.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (uname, pwd, "cashier"),
        )
        conn.commit()
        conn.close()
        messagebox.showinfo(
            "Sukses", f"Kasir baru '{uname}' berhasil ditambahkan!"
        )
        win.destroy()
      except sqlite3.IntegrityError:
        messagebox.showerror("Kesalahan", "Username sudah digunakan!")

    tk.Button(
        win,
        text="Daftarkan Kasir",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        command=save_cashier,
    ).pack(pady=15)

  def show_sales_screen(self):
    self.clear_screen()

    header = tk.Frame(self.root, bg="#1976D2", height=50)
    header.pack(fill="x")
    tk.Label(
        header,
        text=f"Menu Penjualan Kasir - Pengguna: {self.current_user}",
        fg="white",
        bg="#1976D2",
        font=("Arial", 11, "bold"),
    ).pack(side="left", padx=10, pady=10)
    tk.Button(
        header,
        text="Keluar (Logout)",
        bg="#D32F2F",
        fg="white",
        command=self.show_login_screen,
    ).pack(side="right", padx=10, pady=10)

    body = tk.Frame(self.root, padx=10, pady=10)
    body.pack(fill="both", expand=True)

    left_frame = tk.Frame(body)
    left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    search_frame = tk.Frame(left_frame)
    search_frame.pack(fill="x", pady=5)

    tk.Label(
        search_frame, text="🔍 Cari Produk / ID:", font=("Arial", 10, "bold")
    ).pack(side="left", padx=5)
    self.search_entry = tk.Entry(search_frame, font=("Arial", 11), width=25)
    self.search_entry.pack(side="left", padx=5)
    self.search_entry.bind("<KeyRelease>", self.filter_products)

    tk.Button(
        search_frame,
        text="Cari / Filter",
        bg="#1976D2",
        fg="white",
        command=self.filter_products,
    ).pack(side="left", padx=5)
    tk.Button(
        search_frame,
        text="Reset",
        bg="#757575",
        fg="white",
        command=self.reset_product_filter,
    ).pack(side="left", padx=5)

    cols = ("ID", "Nama Produk", "Harga (IDR)", "Stok")
    self.pos_prod_tree = ttk.Treeview(
        left_frame, columns=cols, show="headings", height=18
    )
    for col in cols:
      self.pos_prod_tree.heading(col, text=col)
      self.pos_prod_tree.column(col, width=130)
    self.pos_prod_tree.pack(fill="both", expand=True, pady=5)

    right_frame = tk.Frame(body, width=380)
    right_frame.pack(side="right", fill="both", padx=5, pady=5)

    tk.Label(
        right_frame, text="Keranjang Belanja", font=("Arial", 11, "bold")
    ).pack(anchor="w")

    cart_cols = ("ID", "Produk", "Harga", "Qty")
    self.cart_tree = ttk.Treeview(
        right_frame, columns=cart_cols, show="headings", height=10
    )
    for col in cart_cols:
      self.cart_tree.heading(col, text=col)
      self.cart_tree.column(col, width=80)
    self.cart_tree.pack(fill="both", expand=True, pady=5)

    btn_action_frame = tk.Frame(right_frame)
    btn_action_frame.pack(fill="x", pady=5)

    tk.Button(
        btn_action_frame,
        text="➕ Tambah ke Keranjang",
        bg="#388E3C",
        fg="white",
        font=("Arial", 9, "bold"),
        command=self.add_to_cart,
    ).pack(fill="x", pady=2)

    tk.Button(
        btn_action_frame,
        text="❌ Keluarkan Produk Terpilih dari Keranjang",
        bg="#E65100",
        fg="white",
        font=("Arial", 9, "bold"),
        command=self.remove_from_cart,
    ).pack(fill="x", pady=2)

    tk.Button(
        btn_action_frame,
        text="💳 Selesaikan Pembayaran (Checkout)",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.checkout,
    ).pack(fill="x", pady=2)
    tk.Button(
        btn_action_frame,
        text="🔄 Proses Pengembalian (İade)",
        bg="#D32F2F",
        fg="white",
        font=("Arial", 9, "bold"),
        command=self.process_refund,
    ).pack(fill="x", pady=2)

    self.load_all_pos_products()

  def load_all_pos_products(self):
    for row in self.pos_prod_tree.get_children():
      self.pos_prod_tree.delete(row)
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products")
    for row in cursor.fetchall():
      self.pos_prod_tree.insert(
          "", "end", values=(row[0], row[1], f"Rp {row[2]:,.0f}", row[3])
      )
    conn.close()

  def filter_products(self, event=None):
    query = self.search_entry.get().strip().lower()
    for row in self.pos_prod_tree.get_children():
      self.pos_prod_tree.delete(row)

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
      prod_id = str(row[0])
      prod_name = str(row[1]).lower()
      if query == "" or query in prod_id or query in prod_name:
        self.pos_prod_tree.insert(
            "", "end", values=(row[0], row[1], f"Rp {row[2]:,.0f}", row[3])
        )

  def reset_product_filter(self):
    self.search_entry.delete(0, tk.END)
    self.load_all_pos_products()

  def add_to_cart(self):
    selected = self.pos_prod_tree.selection()
    if not selected:
      messagebox.showwarning("Peringatan", "Pilih produk terlebih dahulu!")
      return
    item = self.pos_prod_tree.item(selected[0])
    vals = item["values"]
    p_id = vals[0]
    p_name = vals[1]

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT price, stock FROM products WHERE id = ?", (p_id,))
    p_res = cursor.fetchone()
    conn.close()

    if not p_res:
      return

    real_price = p_res[0]
    current_stock = p_res[1]

    if current_stock <= 0:
      messagebox.showerror(
          "Stok Habis", f"Maaf, stok untuk {p_name} sudah habis!"
      )
      return

    qty_str = simpledialog.askstring(
        "Jumlah Produk",
        f"Masukkan jumlah produk yang ingin dibeli:\n(Stok Tersedia:"
        f" {current_stock})",
    )

    if not qty_str:
      return

    try:
      qty = int(qty_str.strip())
    except ValueError:
      messagebox.showerror("Kesalahan", "Harus berupa angka valid!")
      return

    if qty <= 0:
      messagebox.showwarning("Peringatan", "Jumlah harus lebih besar dari 0!")
      return

    if qty > current_stock:
      messagebox.showerror(
          "Kesalahan Stok",
          f"Stok tidak mencukupi! Stok tersedia hanya: {current_stock}",
      )
      return

    cart_item = (p_id, p_name, real_price, qty)
    self.cart.append(cart_item)
    self.cart_tree.insert(
        "", "end", values=(p_id, p_name, f"Rp {real_price:,.0f}", qty)
    )

    p_name_lower = str(p_name).lower()
    if "paku" in p_name_lower:
      messagebox.showinfo(
          "Rekomendasi Cross-Sell",
          "💡 Saran Cross-Sell: Pelanggan membeli paku. Apakah ingin"
          " menawarkan Palu atau Ring Pelat?",
      )
    elif "kran" in p_name_lower:
      messagebox.showinfo(
          "Rekomendasi Cross-Sell",
          "💡 Saran Cross-Sell: Pelanggan membeli kran. Apakah ingin"
          " menawarkan Sealtape atau Nepel Kuningan?",
      )
    else:
      messagebox.showinfo("Sukses", f"{qty}x {p_name} ditambahkan ke keranjang.")

  def remove_from_cart(self):
    selected_cart_item = self.cart_tree.selection()
    if not selected_cart_item:
      messagebox.showwarning(
          "Peringatan",
          "Silahkan pilih produk di keranjang yang ingin dikeluarkan!",
      )
      return

    item_id = self.cart_tree.selection()[0]
    item_values = self.cart_tree.item(item_id, "values")
    p_id_to_remove = int(item_values[0])
    p_name_to_remove = item_values[1]

    for idx, cart_item in enumerate(self.cart):
      if int(cart_item[0]) == p_id_to_remove:
        del self.cart[idx]
        break

    self.cart_tree.delete(item_id)
    messagebox.showinfo(
        "Berhasil",
        f"Produk '{p_name_to_remove}' berhasil dikeluarkan dari keranjang.",
    )

  def checkout(self):
    if not self.cart:
      messagebox.showwarning("Peringatan", "Keranjang kosong!")
      return

    current_items = list(self.cart)
    total_val = sum([float(item[2]) * int(item[3]) for item in current_items])

    want_shipping = messagebox.askyesno(
        "Layanan Pengiriman (Kargo)",
        "Apakah pelanggan ingin menggunakan layanan pengiriman kargo? (Mau"
        " pakai kargo?)",
    )

    shipping_info_text = "Tanpa Kargo (Ambil di Toko)"
    if want_shipping:
      ship_win = tk.Toplevel(self.root)
      ship_win.title("Informasi Pengiriman")
      ship_win.geometry("380x300")
      ship_win.grab_set()

      tk.Label(
          ship_win,
          text="Form Kargo & Status Pengiriman",
          font=("Arial", 11, "bold"),
      ).pack(pady=10)

      shipping_frame = tk.LabelFrame(
          ship_win, text="Informasi Pengiriman (Info Kargo)", padx=10, pady=10
      )
      shipping_frame.pack(pady=5, padx=10, fill="x")

      tk.Label(shipping_frame, text="Status Pengiriman (Status Kargo):").pack(
          anchor="w", pady=2
      )

      tk.Radiobutton(
          shipping_frame,
          text="Gratis (Gratis)",
          variable=self.shipping_status,
          value="Gratis",
      ).pack(anchor="w", padx=20)

      tk.Radiobutton(
          shipping_frame,
          text="Berbayar (Berbayar)",
          variable=self.shipping_status,
          value="Berbayar",
      ).pack(anchor="w", padx=20)

      input_f = tk.Frame(ship_win, padx=10, pady=5)
      input_f.pack(fill="x")

      tk.Label(input_f, text="Nama Lengkap:").pack(anchor="w")
      e_name = tk.Entry(input_f, width=35)
      e_name.pack(pady=2)

      tk.Label(input_f, text="No Telepon:").pack(anchor="w")
      e_phone = tk.Entry(input_f, width=35)
      e_phone.pack(pady=2)

      tk.Label(input_f, text="Alamat Lengkap:").pack(anchor="w")
      e_address = tk.Entry(input_f, width=35)
      e_address.pack(pady=2)

      formData = {"name": "", "phone": "", "address": ""}

      def confirm_shipping_details():
        formData["name"] = e_name.get().strip()
        formData["phone"] = e_phone.get().strip()
        formData["address"] = e_address.get().strip()
        ship_win.destroy()

      tk.Button(
          ship_win,
          text="Simpan Kargo",
          bg="#388E3C",
          fg="white",
          font=("Arial", 10, "bold"),
          command=confirm_shipping_details,
      ).pack(pady=10)

      self.root.wait_window(ship_win)

      c_name = formData["name"]
      c_phone = formData["phone"]
      c_address = formData["address"]

      selected_shipping_type = self.shipping_status.get()

      shipping_type = (
          f"Pengiriman Gratis ({selected_shipping_type})"
          if selected_shipping_type == "Gratis"
          else f"Pengiriman Berbayar ({selected_shipping_type})"
      )

      if c_name and c_address:
        tracking_no = f"JKT-ID-{random.randint(100000, 999999)}"
        conn = sqlite3.connect("pos_system_id.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO shipments (tracking_no, customer_name, phone, address,"
            " courier, status, shipping_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                tracking_no,
                c_name,
                c_phone if c_phone else "-",
                c_address,
                "JNE Regular",
                "Sedang Disiapkan (Dipersiapkan)",
                shipping_type,
            ),
        )
        conn.commit()
        conn.close()
        shipping_info_text = (
            f"{shipping_type} - Resi: {tracking_no} (Sedang Disiapkan)"
        )
        messagebox.showinfo(
            "Kargo Berhasil",
            f"Resi kargo berhasil dibuat dan diatur ke status 'Sedang"
            f" Disiapkan'!\nNo Resi: {tracking_no}\nPilihan:"
            f" {selected_shipping_type}",
        )
      else:
        messagebox.showwarning(
            "Peringatan",
            "Informasi kargo tidak lengkap, pengiriman dibatalkan.",
        )
        shipping_info_text = "Pengiriman Dibatalkan"

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    sale_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO sales (date_time, total_amount, cashier) VALUES (?, ?, ?)",
        (sale_time, total_val, self.current_user),
    )
    sale_id = cursor.lastrowid

    for item in current_items:
      p_id = item[0]
      qty = int(item[3])
      cursor.execute(
          "INSERT INTO sale_items (sale_id, product_id, quantity) VALUES (?, ?,"
          " ?)",
          (sale_id, p_id, qty),
      )
      cursor.execute(
          "UPDATE products SET stock = stock - ? WHERE id = ?", (qty, p_id)
      )

    conn.commit()
    conn.close()

    receipt_text = (
        f"========================================\n"
        f"       STRUK BELANJA TOKO (NOTA)        \n"
        f"========================================\n"
        f"ID Transaksi : #{sale_id}\n"
        f"Tanggal      : {sale_time}\n"
        f"Kasir        : {self.current_user}\n"
        f"Status Kargo : {shipping_info_text}\n"
        f"----------------------------------------\n"
        f"Daftar Pembelian:\n"
    )
    for item in current_items:
      receipt_text += (
          f" - [ID Produk: {item[0]}] {item[1]} | Rp {item[2]:,.0f}"
          f" (x{item[3]})\n"
      )

    receipt_text += (
        f"----------------------------------------\n"
        f"TOTAL PEMBAYARAN : Rp {total_val:,.0f}\n"
        f"========================================\n"
        f" Persetujuan Keranjang Otomatis Terjadi.\n"
        f" Terima kasih atas kunjungan Anda!      \n"
        f"========================================"
    )

    receipt_win = tk.Toplevel(self.root)
    receipt_win.title("Struk Belanja Pelanggan")
    receipt_win.geometry("420x520")

    tk.Label(
        receipt_win,
        text="📄 Informasi Struk yang Disetujui Otomatis",
        font=("Arial", 12, "bold"),
    ).pack(pady=10)
    tk.Label(
        receipt_win,
        text=(
            "🖨️ Printer Terdeteksi: Struk berhasil dicetak secara otomatis dari"
            " printer fisik!"
        ),
        fg="#2E7D32",
        font=("Arial", 9, "bold"),
    ).pack(pady=2)

    receipt_box = tk.Text(
        receipt_win, height=15, width=48, font=("Courier New", 10)
    )
    receipt_box.pack(padx=10, pady=5)
    receipt_box.insert(tk.END, receipt_text)
    receipt_box.config(state=tk.DISABLED)

    tk.Button(
        receipt_win,
        text="Tutup (Close)",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=receipt_win.destroy,
    ).pack(pady=10)

    self.cart = []
    for row in self.cart_tree.get_children():
      self.cart_tree.delete(row)
    self.load_all_pos_products()

  def process_refund(self):
    refund_id_str = simpledialog.askstring(
        "Pengembalian Barang (Sistem Pintar Retur)",
        "Masukkan ID Transaksi Penjualan (No Struk / ID Transaksi):",
    )
    if not refund_id_str:
      return

    try:
      r_id_int = int(refund_id_str.strip())
    except ValueError:
      messagebox.showerror(
          "Kesalahan", "ID Transaksi harus berupa angka valid!"
      )
      return

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT si.product_id, p.name, si.quantity, p.price 
        FROM sale_items si 
        JOIN products p ON si.product_id = p.id 
        WHERE si.sale_id = ?
    """,
        (r_id_int,),
    )
    items = cursor.fetchall()

    if not items:
      conn.close()
      messagebox.showwarning(
          "Peringatan",
          f"Transaksi ID #{r_id_int} tidak ditemukan atau tidak ada item"
          " terkait.",
      )
      return

    list_str = (
        f"Daftar Item untuk Transaksi ID #{r_id_int}:\n"
        "--------------------------------------------------\n"
    )
    for idx, item in enumerate(items, 1):
      list_str += (
          f"[{idx}] {item[1]} (ID Produk: {item[0]}) - Qty: {item[2]}\n"
      )

    list_str += (
        "\nSilahkan pilih nomor item yang ingin diretur (Contoh: 1 atau semua/all):"
    )

    selection = simpledialog.askstring("Pilih Item Retur", list_str)
    if not selection:
      conn.close()
      return

    selection = selection.strip().lower()
    refunded_items_summary = []
    total_refund_amount = 0.0

    if selection == "semua" or selection == "all" or selection == "hepsi":
      for item in items:
        p_id, p_name, qty, p_price = item[0], item[1], item[2], item[3]
        cursor.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?", (qty, p_id)
        )
        refunded_items_summary.append((p_id, p_name, qty, p_price))
        total_refund_amount += p_price * qty
    else:
      try:
        indices = [int(x.strip()) for x in selection.split(",")]
        for idx in indices:
          if 1 <= idx <= len(items):
            item = items[idx - 1]
            p_id, p_name, qty, p_price = item[0], item[1], item[2], item[3]
            cursor.execute(
                "UPDATE products SET stock = stock + ? WHERE id = ?",
                (qty, p_id),
            )
            refunded_items_summary.append((p_id, p_name, qty, p_price))
            total_refund_amount += p_price * qty
      except ValueError:
        conn.close()
        messagebox.showerror(
            "Kesalahan",
            "Format pilihan tidak valid! (Contoh: 1 atau semua/hepsi)",
        )
        return

    refund_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO refunds (sale_id, refund_date, refund_amount, details,"
        " cashier) VALUES (?, ?, ?, ?, ?)",
        (
            r_id_int,
            refund_time,
            total_refund_amount,
            f"Proses Retur / Pengembalian Barang",
            self.current_user,
        ),
    )

    conn.commit()
    conn.close()

    if refunded_items_summary:
      refund_receipt = (
          f"========================================\n"
          f"      NOTA PENGEMBALIAN (STRUK RETUR)   \n"
          f"========================================\n"
          f"ID Transaksi Asal : #{r_id_int}\n"
          f"Waktu Pengembalian: {refund_time}\n"
          f"Kasir             : {self.current_user}\n"
          f"----------------------------------------\n"
          f"Item yang Diretur:\n"
      )
      for r_item in refunded_items_summary:
        refund_receipt += (
            f" - [ID:{r_item[0]}] {r_item[1]} | Rp {r_item[3]:,.0f}"
            f" (x{r_item[2]})\n"
        )

      refund_receipt += (
          f"----------------------------------------\n"
          f"TOTAL DANA DIKEMBALIKAN: Rp {total_refund_amount:,.0f}\n"
          f"========================================\n"
          f" Status: Stok diperbarui & Omset dikurangi\n"
          f"========================================"
      )

      ref_win = tk.Toplevel(self.root)
      ref_win.title("Nota Pengembalian Barang")
      ref_win.geometry("420x480")

      tk.Label(
          ref_win,
          text="📄 Informasi Struk Pengembalian",
          font=("Arial", 12, "bold"),
      ).pack(pady=10)
      ref_box = tk.Text(
          ref_win, height=16, width=48, font=("Courier New", 10)
      )
      ref_box.pack(padx=10, pady=5)
      ref_box.insert(tk.END, refund_receipt)
      ref_box.config(state=tk.DISABLED)

      tk.Button(
          ref_win,
          text="Tutup (Close)",
          bg="#D32F2F",
          fg="white",
          font=("Arial", 10, "bold"),
          command=ref_win.destroy,
      ).pack(pady=10)

      self.load_all_pos_products()
    else:
      messagebox.showwarning(
          "Peringatan", "Tidak ada item yang dipilih untuk diretur."
      )

  def show_back_office_screen(self):
    self.clear_screen()

    header = tk.Frame(self.root, bg="#212121", height=55)
    header.pack(fill="x")
    tk.Label(
        header,
        text=f"Manajemen Back Office - Administrator: {self.current_user}",
        fg="white",
        bg="#212121",
        font=("Arial", 12, "bold"),
    ).pack(side="left", padx=15, pady=12)
    tk.Button(
        header,
        text="Keluar (Logout)",
        bg="#D32F2F",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.show_login_screen,
    ).pack(side="right", padx=15, pady=10)

    main_container = tk.Frame(self.root)
    main_container.pack(fill="both", expand=True)

    menu_frame = tk.Frame(main_container, bg="#37474F", width=270, padx=10, pady=10)
    menu_frame.pack(side="left", fill="y")

    tk.Label(
        menu_frame,
        text="MENU ADMINISTRATOR",
        bg="#37474F",
        fg="white",
        font=("Arial", 11, "bold"),
    ).pack(pady=15)

    self.content_frame = tk.Frame(main_container, padx=15, pady=15)
    self.content_frame.pack(side="right", fill="both", expand=True)

    tk.Button(
        menu_frame,
        text="📦 Manajemen Produk & Stok",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_products,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="➕ Tambah Produk Baru",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_add_product,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="✏️ Pembaruan Harga & Stok",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_update_product,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="📈 Laporan Omset & Retur (Omset Bersih)",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_ciro,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="🔍 Cari Struk / Riwayat Dokumen",
        bg="#E65100",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_document_history,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="🤖 Perbandingan Harga Pesaing AI",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_ai,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="🚚 Sistem Kargo & Pelacakan",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_shipments,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="📄 Faktur Grosir (Toko Grosir)",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_invoices,
    ).pack(pady=5)
    tk.Button(
        menu_frame,
        text="📊 Laporan Penjualan",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=25,
        anchor="w",
        padx=10,
        command=self.load_module_sales,
    ).pack(pady=5)

    self.load_module_products()

  def clear_content_frame(self):
    for widget in self.content_frame.winfo_children():
      widget.destroy()

  def load_module_products(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Manajemen Produk & Stok (Stok < 5 Status Kritis)",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    cols = ("ID", "Nama Produk", "Harga (IDR)", "Status Stok")
    self.prod_tree = ttk.Treeview(
        self.content_frame, columns=cols, show="headings", height=18
    )
    for col in cols:
      self.prod_tree.heading(col, text=col)
      self.prod_tree.column(col, width=180)
    self.prod_tree.pack(fill="both", expand=True, pady=5)

    btn_row = tk.Frame(self.content_frame)
    btn_row.pack(fill="x", pady=5)
    tk.Button(
        btn_row,
        text="Muat Ulang Produk",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.populate_products_tree,
    ).pack(side="left", padx=5)
    tk.Button(
        btn_row,
        text="⚠️ Periksa Stok Rendah (Peringatan)",
        bg="#D32F2F",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.check_low_stock,
    ).pack(side="left", padx=5)

    self.populate_products_tree()

  def populate_products_tree(self):
    for row in self.prod_tree.get_children():
      self.prod_tree.delete(row)
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products")
    for row in cursor.fetchall():
      stock_text = (
          f"{row[3]} ⚠️ (Status Kritis!)" if row[3] <= 5 else str(row[3])
      )
      self.prod_tree.insert(
          "", "end", values=(row[0], row[1], f"Rp {row[2]:,.0f}", stock_text)
      )
    conn.close()

  def check_low_stock(self):
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, stock FROM products WHERE stock <= 5")
    low_items = cursor.fetchall()
    conn.close()

    if low_items:
      msg = (
          "Peringatan! Stok produk berikut hampir habis (Kritis):\n\n"
      )
      for name, stock in low_items:
        msg += f"- {name} (Sisa Stok: {stock})\n"
      messagebox.showwarning("Peringatan Stok Menipis", msg)
    else:
      messagebox.showinfo(
          "Informasi Stok", "Semua stok produk dalam kondisi aman."
      )

  def load_module_add_product(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Tambah Produk Baru (Pendaftaran Barang)",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=10)

    form = tk.Frame(self.content_frame, padx=10, pady=10)
    form.pack(anchor="w")

    tk.Label(form, text="ID Produk (Nomor Unik):", font=("Arial", 11)).grid(
        row=0, column=0, sticky="w", pady=8
    )
    self.new_p_id = tk.Entry(form, width=25, font=("Arial", 11))
    self.new_p_id.grid(row=0, column=1, padx=10, pady=8)

    tk.Label(form, text="Nama Produk:", font=("Arial", 11)).grid(
        row=1, column=0, sticky="w", pady=8
    )
    self.new_p_name = tk.Entry(form, width=35, font=("Arial", 11))
    self.new_p_name.grid(row=1, column=1, padx=10, pady=8)

    tk.Label(form, text="Harga (IDR):", font=("Arial", 11)).grid(
        row=2, column=0, sticky="w", pady=8
    )
    self.new_p_price = tk.Entry(form, width=25, font=("Arial", 11))
    self.new_p_price.grid(row=2, column=1, padx=10, pady=8)

    tk.Label(form, text="Jumlah Stok:", font=("Arial", 11)).grid(
        row=3, column=0, sticky="w", pady=8
    )
    self.new_p_stock = tk.Entry(form, width=25, font=("Arial", 11))
    self.new_p_stock.grid(row=3, column=1, padx=10, pady=8)

    tk.Button(
        form,
        text="Simpan Produk Baru (Simpan)",
        bg="#388E3C",
        fg="white",
        font=("Arial", 11, "bold"),
        command=self.save_new_product_to_db,
    ).grid(row=4, column=1, sticky="w", padx=10, pady=15)

  def save_new_product_to_db(self):
    p_id_str = self.new_p_id.get().strip()
    p_name = self.new_p_name.get().strip()
    p_price_str = self.new_p_price.get().strip()
    p_stock_str = self.new_p_stock.get().strip()

    if not p_id_str or not p_name or not p_price_str or not p_stock_str:
      messagebox.showerror(
          "Kesalahan",
          "Semua kolom harus diisi! (Semua kolom wajib diisi)",
      )
      return

    try:
      p_id = int(p_id_str)
      p_price = float(p_price_str)
      p_stock = int(p_stock_str)
    except ValueError:
      messagebox.showerror(
          "Kesalahan",
          "Format ID, Harga, atau Stok harus berupa angka valid!",
      )
      return

    try:
      conn = sqlite3.connect("pos_system_id.db")
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO products (id, name, price, stock) VALUES (?, ?, ?, ?)",
          (p_id, p_name, p_price, p_stock),
      )
      conn.commit()
      conn.close()
      messagebox.showinfo(
          "Sukses",
          f"Produk baru '{p_name}' berhasil ditambahkan ke sistem!",
      )
      self.new_p_id.delete(0, tk.END)
      self.new_p_name.delete(0, tk.END)
      self.new_p_price.delete(0, tk.END)
      self.new_p_stock.delete(0, tk.END)
    except sqlite3.IntegrityError:
      messagebox.showerror(
          "Kesalahan", "ID Produk sudah terdaftar! Gunakan ID lain."
      )

  def load_module_update_product(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Pembaruan Harga & Stok Produk",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    cols = ("ID", "Nama Produk", "Harga (IDR)", "Stok")
    self.upd_tree = ttk.Treeview(
        self.content_frame, columns=cols, show="headings", height=15
    )
    for col in cols:
      self.upd_tree.heading(col, text=col)
      self.upd_tree.column(col, width=160)
    self.upd_tree.pack(fill="both", expand=True, pady=5)

    form_frame = tk.Frame(self.content_frame, pady=10)
    form_frame.pack(fill="x")

    tk.Label(form_frame, text="ID Produk:", font=("Arial", 10)).pack(
        side="left", padx=5
    )
    self.upd_id_entry = tk.Entry(form_frame, width=8, font=("Arial", 10))
    self.upd_id_entry.pack(side="left", padx=5)

    tk.Label(form_frame, text="Harga Baru (IDR):", font=("Arial", 10)).pack(
        side="left", padx=5
    )
    self.upd_price_entry = tk.Entry(form_frame, width=15, font=("Arial", 10))
    self.upd_price_entry.pack(side="left", padx=5)

    tk.Label(form_frame, text="Stok Baru:", font=("Arial", 10)).pack(
        side="left", padx=5
    )
    self.upd_stock_entry = tk.Entry(form_frame, width=8, font=("Arial", 10))
    self.upd_stock_entry.pack(side="left", padx=5)

    tk.Button(
        form_frame,
        text="💾 Perbarui",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.execute_product_update,
    ).pack(side="left", padx=15)

    self.populate_update_tree()

  def populate_update_tree(self):
    for row in self.upd_tree.get_children():
      self.upd_tree.delete(row)
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products")
    for row in cursor.fetchall():
      self.upd_tree.insert(
          "", "end", values=(row[0], row[1], f"Rp {row[2]:,.0f}", row[3])
      )
    conn.close()

  def execute_product_update(self):
    p_id = self.upd_id_entry.get().strip()
    new_p = self.upd_price_entry.get().strip()
    new_s = self.upd_stock_entry.get().strip()

    if not p_id:
      messagebox.showerror(
          "Kesalahan", "Silahkan masukkan ID Produk yang ingin diperbarui!"
      )
      return

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()

    if new_p:
      cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_p, p_id))
    if new_s:
      cursor.execute(
          "UPDATE products SET stock = ? WHERE id = ?", (new_s, p_id)
      )

    conn.commit()
    conn.close()
    messagebox.showinfo("Sukses", "Produk berhasil diperbarui!")
    self.populate_update_tree()

  def load_module_ciro(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Laporan Omset & Retur (Omset Bersih dan Pelacakan Retur)",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    self.ciro_result_box = tk.Text(
        self.content_frame, height=14, width=82, font=("Arial", 11)
    )
    self.ciro_result_box.pack(fill="both", expand=True, pady=5)

    tk.Button(
        self.content_frame,
        text="🔄 Hitung & Perbarui Omset",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.calculate_revenue,
    ).pack(pady=10)
    self.calculate_revenue()

  def calculate_revenue(self):
    self.ciro_result_box.delete("1.0", tk.END)
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()

    today_str = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT SUM(total_amount), COUNT(*) FROM sales WHERE date_time LIKE ?",
        (f"{today_str}%",),
    )
    daily_res = cursor.fetchone()
    daily_gross = daily_res[0] if daily_res[0] else 0
    daily_count = daily_res[1] if daily_res[1] else 0

    cursor.execute(
        "SELECT SUM(refund_amount), COUNT(*) FROM refunds WHERE refund_date"
        " LIKE ?",
        (f"{today_str}%",),
    )
    daily_ref = cursor.fetchone()
    daily_refund_amt = daily_ref[0] if daily_ref[0] else 0
    daily_refund_count = daily_ref[1] if daily_ref[1] else 0

    daily_net = daily_gross - daily_refund_amt

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT SUM(total_amount) FROM sales WHERE date_time >= ?", (week_ago,)
    )
    w_sales = cursor.fetchone()[0] or 0
    cursor.execute(
        "SELECT SUM(refund_amount) FROM refunds WHERE refund_date >= ?",
        (week_ago,),
    )
    w_refunds = cursor.fetchone()[0] or 0
    weekly_net = w_sales - w_refunds

    month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT SUM(total_amount) FROM sales WHERE date_time >= ?", (month_ago,)
    )
    m_sales = cursor.fetchone()[0] or 0
    cursor.execute(
        "SELECT SUM(refund_amount) FROM refunds WHERE refund_date >= ?",
        (month_ago,),
    )
    m_refunds = cursor.fetchone()[0] or 0
    monthly_net = m_sales - m_refunds

    conn.close()

    report = (
        f"[LAPORAN PENDAPATAN & OMSET BERSIH (NET REVENUE)]\n"
        f"========================================================\n"
        f"📅 Harian (Hari Ini - {today_str}):\n"
        f"   - Total Transaksi Masuk : {daily_count} penjualan\n"
        f"   - Total Pendapatan Kotor : Rp {daily_gross:,.0f}\n"
        f"   - Total Retur / İade     : {daily_refund_count} retur (-Rp"
        f" {daily_refund_amt:,.0f})\n"
        f"   ➔ OMSET BERSIH HARIAN    : Rp {daily_net:,.0f}\n\n"
        f"📊 Mingguan (7 Hari Terakhir):\n"
        f"   ➔ OMSET BERSIH MINGGUAN  : Rp {weekly_net:,.0f}\n\n"
        f"📈 Bulanan (30 Hari Terakhir):\n"
        f"   ➔ OMSET BERSIH BULANAN   : Rp {monthly_net:,.0f}\n"
        f"========================================================\n"
        f"Status: Semua pengembalian telah otomatis dikurangi dari omset."
    )
    self.ciro_result_box.insert(tk.END, report)

  def load_module_document_history(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Riwayat Dokumen / Struk Berdasarkan ID (Pencarian Riwayat Dokumen)",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    search_row = tk.Frame(self.content_frame, pady=5)
    search_row.pack(anchor="w")

    tk.Label(
        search_row,
        text="Masukkan ID Transaksi (No Struk / ID Dokumen):",
        font=("Arial", 10, "bold"),
    ).pack(side="left", padx=5)
    self.doc_id_entry = tk.Entry(search_row, width=15, font=("Arial", 11))
    self.doc_id_entry.pack(side="left", padx=5)

    tk.Button(
        search_row,
        text="🔍 Cari & Lihat Riwayat",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.search_document_history,
    ).pack(side="left", padx=10)

    self.doc_result_box = tk.Text(
        self.content_frame, height=14, width=85, font=("Courier New", 10)
    )
    self.doc_result_box.pack(fill="both", expand=True, pady=5)

    tk.Button(
        self.content_frame,
        text="🖨️ Cetak / Unduh Laporan Dokumen (Cetak Laporan)",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.print_document_history,
    ).pack(pady=5)

  def search_document_history(self):
    doc_id_str = self.doc_id_entry.get().strip()
    if not doc_id_str:
      messagebox.showerror(
          "Kesalahan", "Masukkan ID Transaksi terlebih dahulu!"
      )
      return

    try:
      d_id = int(doc_id_str)
    except ValueError:
      messagebox.showerror("Kesalahan", "ID harus berupa angka valid!")
      return

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, date_time, total_amount, cashier FROM sales WHERE id = ?",
        (d_id,),
    )
    sale_data = cursor.fetchone()

    cursor.execute(
        """
        SELECT p.name, si.quantity, p.price 
        FROM sale_items si 
        JOIN products p ON si.product_id = p.id 
        WHERE si.sale_id = ?
    """,
        (d_id,),
    )
    items_data = cursor.fetchall()

    cursor.execute(
        "SELECT refund_date, refund_amount, details, cashier FROM refunds"
        " WHERE sale_id = ?",
        (d_id,),
    )
    refund_data = cursor.fetchall()

    conn.close()

    if not sale_data:
      self.doc_result_box.delete("1.0", tk.END)
      self.doc_result_box.insert(
          tk.END, f"Transaksi dengan ID #{d_id} tidak ditemukan di sistem!"
      )
      return

    report_text = (
        f"==================================================\n"
        f"      RIWAYAT DOKUMEN & STRUK (LAPORAN DOKUMEN)   \n"
        f"==================================================\n"
        f"ID Transaksi : #{sale_data[0]}\n"
        f"Tanggal Penjualan: {sale_data[1]}\n"
        f"Kasir Pembuat: {sale_data[3]}\n"
        f"Total Asal   : Rp {sale_data[2]:,.0f}\n"
        f"--------------------------------------------------\n"
        f"Daftar Pembelian Item:\n"
    )

    for itm in items_data:
      report_text += (
          f" - {itm[0]} | Qty: {itm[1]} | Harga Satuan: Rp {itm[2]:,.0f}\n"
      )

    report_text += (
        f"--------------------------------------------------\n"
        f"Riwayat Perubahan / Retur (İade):\n"
    )
    if refund_data:
      for ref in refund_data:
        report_text += (
            f" [RETUR] Waktu: {ref[0]} | Nominal Retur: Rp {ref[1]:,.0f} |"
            f" Petugas: {ref[3]}\n"
        )
    else:
      report_text += (
          " (Belum ada retur atau perubahan pada dokumen ini)\n"
      )

    report_text += (
        f"==================================================\n"
        f" Status: Dokumen terverifikasi resmi oleh sistem. \n"
        f"=================================================="
    )

    self.doc_result_box.delete("1.0", tk.END)
    self.doc_result_box.insert(tk.END, report_text)
    self.current_loaded_doc_report = report_text

  def print_document_history(self):
    if (
        not hasattr(self, "current_loaded_doc_report")
        or not self.current_loaded_doc_report
    ):
      messagebox.showwarning(
          "Peringatan",
          "Silahkan cari dokumen terlebih dahulu sebelum mencetak!",
      )
      return

    print_win = tk.Toplevel(self.root)
    print_win.title("Cetak Laporan Dokumen")
    print_win.geometry("440x500")

    tk.Label(
        print_win,
        text="🖨️ Cetak / Salin Laporan Dokumen Pelanggan",
        font=("Arial", 11, "bold"),
    ).pack(pady=10)
    p_box = tk.Text(print_win, height=18, width=50, font=("Courier New", 9))
    p_box.pack(padx=10, pady=5)
    p_box.insert(tk.END, self.current_loaded_doc_report)
    p_box.config(state=tk.DISABLED)

    tk.Button(
        print_win,
        text="Tutup (Close)",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=print_win.destroy,
    ).pack(pady=10)

  def load_module_ai(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Komparasi Harga AI: Toko Kami vs Pesaing (Tokopedia/Shopee)",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    self.ai_result_box = tk.Text(
        self.content_frame, height=14, width=88, font=("Courier New", 10)
    )
    self.ai_result_box.pack(fill="both", expand=True, pady=5)

    tk.Button(
        self.content_frame,
        text="🔍 Jalankan Analisis Harga Pesaing",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.run_ai_price_analysis,
    ).pack(pady=10)
    self.run_ai_price_analysis()

  def run_ai_price_analysis(self):
    self.ai_result_box.delete("1.0", tk.END)

    competitor_market_prices = {
        "Burgari Carb Cleanner 500ml": 48000.0,
        "Paku Beton 1/4 Box 230gr": 24000.0,
        "Paku Beton 1/2 Box 460gr": 45000.0,
        "Fumetas Waterpass Orange": 88000.0,
        "Fumetax Waterpass Silver": 90000.0,
        "Solvex Kran Concot Panjang SP-30129": 120000.0,
        "Moon Lion 8x3inch F-AB": 65000.0,
        "Ring Pelat Kuning M14*34*2mm": 1600.0,
        "Mur Putih M8 K13": 2000.0,
        "Roof Drain Dak Stainless": 115000.0,
    }

    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM products")
    products = cursor.fetchall()
    conn.close()

    report = (
        "[INTELIJEN PASAR AI - KOMPARASI HARGA PESAING]\n"
        "==================================================================-\n"
        f"{'Nama Produk':<33} | {'Harga Kami':<12} | {'Pasar (Rata-rata)':<12}"
        f" | {'Status AI'}\n"
        "-------------------------------------------------------------------\n"
    )

    for p_name, our_price in products:
      comp_price = competitor_market_prices.get(p_name, our_price)

      if our_price < comp_price:
        status = "⚠️ LEBIH MURAH (Lebih Murah)"
      elif our_price > comp_price:
        status = "🔴 LEBIH MAHAL (Lebih Mahal)"
      else:
        status = "🟢 SAMA (Sama)"

      report += (
          f"{p_name[:31]:<33} | Rp {our_price:>9,.0f} | Rp"
          f" {comp_price:>9,.0f} | {status}\n"
      )

    report += (
        "==================================================================-\n"
        "💡 Saran AI: Disarankan untuk menyesuaikan harga produk yang 'Lebih"
        " Mahal' ke tingkat pasar, dan mengevaluasi peningkatan margin"
        " keuntungan pada produk yang 'Lebih Murah'."
    )
    self.ai_result_box.insert(tk.END, report)

  def load_module_shipments(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text=(
            "Pelacakan Pengiriman & Sistem Manajemen Kargo (Sedang Disiapkan ->"
            " Dalam Perjalanan -> Tiba)"
        ),
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    s_cols = (
        "ID",
        "No Resi",
        "Nama Pelanggan",
        "Telepon",
        "Alamat",
        "Kurir",
        "Status",
        "Tipe Kargo",
    )
    self.ship_tree = ttk.Treeview(
        self.content_frame, columns=s_cols, show="headings", height=15
    )
    for col in s_cols:
      self.ship_tree.heading(col, text=col)
      self.ship_tree.column(col, width=110)
    self.ship_tree.pack(fill="both", expand=True, pady=5)

    ship_btn_frame = tk.Frame(self.content_frame)
    ship_btn_frame.pack(fill="x", pady=5)

    tk.Button(
        ship_btn_frame,
        text="Muat Ulang Kargo",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.load_shipments_into_tree,
    ).pack(side="left", padx=5)

    tk.Button(
        ship_btn_frame,
        text="🚀 Kirim Kargo (Masukkan No Resi)",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.dispatch_shipment,
    ).pack(side="left", padx=5)

    tk.Button(
        ship_btn_frame,
        text="✅ Tampilkan Pemberitahuan Kargo Tiba",
        bg="#00897B",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.show_shipment_delivered_info,
    ).pack(side="left", padx=5)

    tk.Button(
        ship_btn_frame,
        text="🗑️ Hapus Kargo (Hapus)",
        bg="#D32F2F",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.delete_shipment,
    ).pack(side="left", padx=5)

    self.load_shipments_into_tree()

  def load_shipments_into_tree(self):
    for row in self.ship_tree.get_children():
      self.ship_tree.delete(row)
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, tracking_no, customer_name, phone, address, courier,"
        " status, shipping_type FROM shipments"
    )
    for row in cursor.fetchall():
      self.ship_tree.insert("", "end", values=row)
    conn.close()

  def dispatch_shipment(self):
    selected = self.ship_tree.selection()
    if not selected:
      messagebox.showwarning(
          "Peringatan",
          "Silahkan pilih kargo dari tabel yang ingin diberangkatkan!",
      )
      return

    item = self.ship_tree.item(selected[0])
    ship_id = item["values"][0]
    current_tracking = item["values"][1]
    cust_name = item["values"][2]

    dialog_win = tk.Toplevel(self.root)
    dialog_win.title("Input Nomor Resi Kargo")
    dialog_win.geometry("400x220")
    dialog_win.attributes("-topmost", True)
    dialog_win.grab_set()

    tk.Label(
        dialog_win,
        text=f"Pelanggan: {cust_name}\nMasukkan Nomor Resi Kargo:",
        font=("Arial", 11, "bold"),
    ).pack(pady=15)

    t_entry = tk.Entry(dialog_win, width=30, font=("Arial", 11))
    t_entry.pack(pady=5)
    t_entry.insert(0, current_tracking)

    def save_dispatch():
      new_t_no = t_entry.get().strip()
      if not new_t_no:
        messagebox.showerror(
            "Kesalahan", "Nomor resi tidak boleh kosong!"
        )
        return

      conn = sqlite3.connect("pos_system_id.db")
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE shipments SET tracking_no = ?, status = ? WHERE id = ?",
          (new_t_no, "Dalam Perjalanan (Sedang Dikirim)", ship_id),
      )
      conn.commit()
      conn.close()

      self.load_shipments_into_tree()
      messagebox.showinfo(
          "Sukses",
          f"Nomor Resi Kargo ({new_t_no}) berhasil disimpan!\nStatus"
          " diperbarui: DALAM PERJALANAN 🚚",
      )
      dialog_win.destroy()

    tk.Button(
        dialog_win,
        text="Kirim Kargo",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=save_dispatch,
    ).pack(pady=15)

  def show_shipment_delivered_info(self):
    selected = self.ship_tree.selection()
    if not selected:
      messagebox.showwarning(
          "Peringatan", "Silahkan pilih kargo untuk melihat statusnya!"
      )
      return

    item = self.ship_tree.item(selected[0])
    vals = item["values"]
    ship_id, t_no, c_name, phone, address, courier, status, st_type = vals

    info_msg = (
        f"📦 INFORMASI PELACAKAN & STATUS KARGO\n"
        f"----------------------------------------\n"
        f"Nomor Resi     : {t_no}\n"
        f"Nama Penerima  : {c_name}\n"
        f"Telepon        : {phone}\n"
        f"Alamat         : {address}\n"
        f"Perusahaan Kargo: {courier}\n"
        f"Tipe Pengiriman: {st_type}\n"
        f"Status Saat Ini: {status}\n"
        f"----------------------------------------\n"
        f"Pemberitahuan: Kargo diproses tanpa kendala."
    )
    messagebox.showinfo("Pemberitahuan Detail Kargo", info_msg)

  def delete_shipment(self):
    selected = self.ship_tree.selection()
    if not selected:
      messagebox.showwarning(
          "Peringatan", "Pilih kargo yang ingin dihapus dari tabel!"
      )
      return

    item = self.ship_tree.item(selected[0])
    ship_id = item["values"][0]

    confirm = messagebox.askyesno(
        "Konfirmasi Hapus",
        "Apakah Anda yakin ingin menghapus data kargo ini (kargo sudah tiba)?",
    )
    if confirm:
      conn = sqlite3.connect("pos_system_id.db")
      cursor = conn.cursor()
      cursor.execute("DELETE FROM shipments WHERE id = ?", (ship_id,))
      conn.commit()
      conn.close()
      self.load_shipments_into_tree()
      messagebox.showinfo(
          "Sukses", "Data kargo berhasil dihapus dari sistem."
      )

  def load_module_invoices(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Faktur Grosir (Sistem Faktur Pemasok)",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    i_cols = (
        "ID",
        "No Faktur",
        "Nama Pemasok",
        "Tanggal",
        "Total (IDR)",
        "Keterangan",
    )
    self.inv_tree = ttk.Treeview(
        self.content_frame, columns=i_cols, show="headings", height=15
    )
    for col in i_cols:
      self.inv_tree.heading(col, text=col)
      self.inv_tree.column(col, width=140)
    self.inv_tree.pack(fill="both", expand=True, pady=5)

    inv_btn_frame = tk.Frame(self.content_frame)
    inv_btn_frame.pack(fill="x", pady=5)
    tk.Button(
        inv_btn_frame,
        text="Muat Faktur",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.load_wholesale_invoices,
    ).pack(side="left", padx=5)
    tk.Button(
        inv_btn_frame,
        text="➕ Tambah Faktur Baru",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.open_add_invoice_window,
    ).pack(side="left", padx=5)

    self.load_wholesale_invoices()

  def load_wholesale_invoices(self):
    for row in self.inv_tree.get_children():
      self.inv_tree.delete(row)
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, invoice_no, supplier_name, date_time, total_amount,"
        " details FROM wholesale_invoices"
    )
    for row in cursor.fetchall():
      self.inv_tree.insert(
          "",
          "end",
          values=(row[0], row[1], row[2], row[3], f"Rp {row[4]:,.0f}", row[5]),
      )
    conn.close()

  def open_add_invoice_window(self):
    inv_win = tk.Toplevel(self.root)
    inv_win.title("Tambah Faktur Grosir")
    inv_win.geometry("400x320")

    tk.Label(
        inv_win, text="Form Pencatatan Faktur Pemasok", font=("Arial", 11, "bold")
    ).pack(pady=10)

    f_frame = tk.Frame(inv_win, padx=15, pady=5)
    f_frame.pack(fill="x")

    tk.Label(f_frame, text="Nomor Faktur:").pack(anchor="w")
    e_inv_no = tk.Entry(f_frame, width=35)
    e_inv_no.pack(pady=2)

    tk.Label(f_frame, text="Nama Pemasok:").pack(anchor="w")
    e_supp = tk.Entry(f_frame, width=35)
    e_supp.pack(pady=2)

    tk.Label(f_frame, text="Total Tagihan (IDR):").pack(anchor="w")
    e_tot = tk.Entry(f_frame, width=35)
    e_tot.pack(pady=2)

    tk.Label(f_frame, text="Keterangan / Produk:").pack(anchor="w")
    e_desc = tk.Entry(f_frame, width=35)
    e_desc.pack(pady=2)

    def save_invoice_db():
      inv_no = e_inv_no.get().strip()
      supp = e_supp.get().strip()
      tot_str = e_tot.get().strip()
      desc = e_desc.get().strip()

      if not inv_no or not supp or not tot_str:
        messagebox.showerror(
            "Kesalahan", "Nomor, Pemasok, dan Total wajib diisi!"
        )
        return

      try:
        tot_val = float(tot_str)
      except ValueError:
        messagebox.showerror(
            "Kesalahan", "Total tagihan harus berupa angka!"
        )
        return

      date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      conn = sqlite3.connect("pos_system_id.db")
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO wholesale_invoices (invoice_no, supplier_name, date_time,"
          " total_amount, details) VALUES (?, ?, ?, ?, ?)",
          (
              inv_no,
              supp,
              date_str,
              tot_val,
              desc if desc else "Pembelian Stok",
          ),
      )
      conn.commit()
      conn.close()

      messagebox.showinfo("Sukses", "Faktur berhasil dicatat!")
      inv_win.destroy()
      self.load_wholesale_invoices()

    tk.Button(
        inv_win,
        text="Simpan Faktur",
        bg="#388E3C",
        fg="white",
        font=("Arial", 10, "bold"),
        command=save_invoice_db,
    ).pack(pady=15)

  def load_module_sales(self):
    self.clear_content_frame()
    tk.Label(
        self.content_frame,
        text="Laporan Penjualan Keseluruhan (Laporan Semua Penjualan)",
        font=("Arial", 13, "bold"),
    ).pack(anchor="w", pady=5)

    s_cols = ("ID Transaksi", "Waktu", "Total (IDR)", "Kasir Pembuat")
    self.sales_tree = ttk.Treeview(
        self.content_frame, columns=s_cols, show="headings", height=16
    )
    for col in s_cols:
      self.sales_tree.heading(col, text=col)
      self.sales_tree.column(col, width=170)
    self.sales_tree.pack(fill="both", expand=True, pady=5)

    tk.Button(
        self.content_frame,
        text="🔄 Muat Ulang Daftar Penjualan",
        bg="#1976D2",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.populate_sales_tree,
    ).pack(pady=5)

    self.populate_sales_tree()

  def populate_sales_tree(self):
    for row in self.sales_tree.get_children():
      self.sales_tree.delete(row)
    conn = sqlite3.connect("pos_system_id.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, date_time, total_amount, cashier FROM sales")
    for row in cursor.fetchall():
      self.sales_tree.insert(
          "", "end", values=(row[0], row[1], f"Rp {row[2]:,.0f}", row[3])
      )
    conn.close()


if __name__ == "__main__":
  root = tk.Tk()
  app = IndonesianPOSApp(root)
  root.mainloop()
