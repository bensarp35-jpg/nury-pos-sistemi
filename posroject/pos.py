from datetime import datetime, timedelta
import random
import sqlite3
import requests
import streamlit as st

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
    if response.status_code == 200:
      st.success(
          f"Pesan templat WhatsApp terkirim ke {phone_number}! (OTP Uji Coba:"
          f" {otp_code})"
      )
    else:
      st.warning(f"Percobaan pengiriman pesan telah dilakukan: {response.text}")
  except Exception as e:
    st.error(f"Terjadi kesalahan koneksi: {e}")


# --- VERİTABANI BAŞLANGICI ---


def init_db():
  conn = sqlite3.connect("pos_system_id.db", check_same_thread=False)
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

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(
    page_title="Sistem POS & Back Office Pintar", layout="wide"
)

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
  st.session_state.username = ""
  st.session_state.role = ""
  st.session_state.otp_verified = False

# GİRİŞ EKRANI
if not st.session_state.logged_in:
  st.title("🔐 Sistem Girişi (Login)")
  username = st.text_input("Kullanıcı Adı (Username)")
  password = st.text_input("Şifre (Password)", type="password")

  if st.button("Giriş Yap"):
    conn = sqlite3.connect("pos_system_id.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role FROM users WHERE username = ? AND password = ?",
        (username, password),
    )
    user = cursor.fetchone()
    conn.close()

    if user:
      st.session_state.username = username
      st.session_state.role = user[0]
      if user[0] == "admin":
        otp_code = random.randint(1000, 9999)
        st.session_state.otp_code = otp_code
        send_real_whatsapp_otp("+905063626244", otp_code)
        st.session_state.logged_in = True
        st.rerun()
      else:
        st.session_state.logged_in = True
        st.session_state.otp_verified = True
        st.rerun()
    else:
      st.error("Kullanıcı adı veya şifre hatalı!")

# Admin OTP Doğrulama Adımı
elif (
    st.session_state.role == "admin" and not st.session_state.otp_verified
):
  st.title("📲 WhatsApp 2FA Doğrulama")
  st.info(
      "WhatsApp'a gönderilen 4 haneli doğrulama kodunu girin. (Test OTP kodunuz:"
      f" {st.session_state.otp_code})"
  )
  entered_otp = st.text_input("OTP Kodu")

  if st.button("Kodu Doğrula"):
    if entered_otp == str(st.session_state.otp_code):
      st.session_state.otp_verified = True
      st.success("Doğrulama Başarılı!")
      st.rerun()
    else:
      st.error("Hatalı OTP kodu!")

# ----------------- KASİR & ADMIN PANELİ -----------------
else:
  st.sidebar.title(
      f"Hoş Geldiniz, {st.session_state.username} ({st.session_state.role})"
  )

  if st.sidebar.button("Çıkış Yap"):
    st.session_state.logged_in = False
    st.session_state.otp_verified = False
    st.rerun()

  conn = sqlite3.connect("pos_system_id.db", check_same_thread=False)

  if st.session_state.role == "cashier":
    st.header("🛒 Kasa & Satış Ekranı")

    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM products")
    products = cursor.fetchall()

    st.subheader("Ürün Kataloğu")
    selected_prod_id = st.selectbox(
        "Ürün Seçin",
        options=[p[0] for p in products],
        format_func=lambda x: f"{next(p[1] for p in products if p[0] == x)} (Stok: {next(p[3] for p in products if p[0] == x)} - Rp {next(p[2] for p in products if p[0] == x):,.0f})",
    )

    qty = st.number_input("Adet", min_value=1, value=1)

    if st.button("Sepete Ekle"):
      cursor.execute(
          "SELECT name, price, stock FROM products WHERE id = ?",
          (selected_prod_id,),
      )
      p_data = cursor.fetchone()
      if qty > p_data[2]:
        st.error("Stok yetersiz!")
      else:
        if "cart" not in st.session_state:
          st.session_state.cart = []
        st.session_state.cart.append(
            (selected_prod_id, p_data[0], p_data[1], qty)
        )
        st.success(f"{qty}x {p_data[0]} sepete eklendi.")

    if "cart" in st.session_state and st.session_state.cart:
      st.subheader("Sepetiniz")
      total_val = sum([item[2] * item[3] for item in st.session_state.cart])
      for idx, item in enumerate(st.session_state.cart):
        st.write(f"- {item[1]} | {item[3]} Adet | Rp {item[2]*item[3]:,.0f}")

      st.write(f"**Toplam Tutar: Rp {total_val:,.0f}**")

      if st.button("Ödemeyi Tamamla (Checkout)"):
        sale_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO sales (date_time, total_amount, cashier) VALUES (?,"
            " ?, ?)",
            (sale_time, total_val, st.session_state.username),
        )
        sale_id = cursor.lastrowid

        for item in st.session_state.cart:
          cursor.execute(
              "INSERT INTO sale_items (sale_id, product_id, quantity) VALUES"
              " (?, ?, ?)",
              (sale_id, item[0], item[3]),
          )
          cursor.execute(
              "UPDATE products SET stock = stock - ? WHERE id = ?",
              (item[3], item[0]),
          )
        conn.commit()
        st.session_state.cart = []
        st.success(
            f"Satış başarıyla tamamlandı! İşlem/Struk ID: #{sale_id}"
        )
        st.rerun()

  elif st.session_state.role == "admin":
    st.header("📊 Yönetici Back Office Paneli")
    menu = st.sidebar.selectbox(
        "Yönetim Menüsü",
        [
            "Ürünler & Stok",
            "Yeni Ürün Ekle",
            "Omset Raporu",
            "Kargo Takibi",
            "Faturalar",
        ],
    )

    if menu == "Ürünler & Stok":
      st.subheader("Ürün Listesi")
      cursor = conn.cursor()
      cursor.execute("SELECT id, name, price, stock FROM products")
      for row in cursor.fetchall():
        st.write(
            f"ID: {row[0]} | **{row[1]}** | Fiyat: Rp {row[2]:,.0f} | Stok:"
            f" {row[3]}"
        )

    elif menu == "Yeni Ürün Ekle":
      st.subheader("Yeni Ürün Kaydı")
      p_id = st.number_input("Ürün ID", min_value=1, step=1)
      p_name = st.text_input("Ürün Adı")
      p_price = st.number_input("Fiyat (IDR)", min_value=0.0)
      p_stock = st.number_input("Stok Miktarı", min_value=0, step=1)

      if st.button("Kaydet"):
        try:
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO products (id, name, price, stock) VALUES (?, ?,"
              " ?, ?)",
              (p_id, p_name, p_price, p_stock),
          )
          conn.commit()
          st.success("Ürün başarıyla eklendi!")
        except Exception as e:
          st.error(f"Hata: {e}")

    elif menu == "Omset Raporu":
      st.subheader("Ciro ve Satış Raporları")
      cursor = conn.cursor()
      cursor.execute("SELECT SUM(total_amount) FROM sales")
      total_sales = cursor.fetchone()[0] or 0
      st.metric(label="Toplam Ciro", value=f"Rp {total_sales:,.0f}")

    elif menu == "Kargo Takibi":
      st.subheader("Kargo Listesi")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT tracking_no, customer_name, address, status, shipping_type"
          " FROM shipments"
      )
      for row in cursor.fetchall():
        st.write(
            f"Resi: {row[0]} | Müşteri: {row[1]} | Durum: {row[3]} ({row[4]})"
        )

    elif menu == "Faturalar":
      st.subheader("Toptancı Faturaları")
      cursor = conn.cursor()
      cursor.execute(
          "SELECT invoice_no, supplier_name, total_amount, date_time FROM"
          " wholesale_invoices"
      )
      for row in cursor.fetchall():
        st.write(
            f"Fatura No: {row[0]} | Tedarikçi: {row[1]} | Tutar: Rp"
            f" {row[2]:,.0f} | Tarih: {row[3]}"
        )

  conn.close()
