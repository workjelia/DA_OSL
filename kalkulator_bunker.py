import io
import numpy as np
import pandas as pd
import streamlit as st

# Konfigurasi Halaman & Tema Serba Pink
st.set_page_config(page_title="Kalkulator Bunker", page_icon="", layout="wide")

# Custom CSS untuk tema serba pink + Watermark
st.markdown(
    """
    <style>
    /* Background utama */
    .stApp {
        background-color: #fff0f5;
    }
    /* Warna Header */
    h1, h2, h3 {
        color: #d81b60 !important;
    }
    /* Tombol Utama */
    .stButton>button {
        background-color: #ff69b4;
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #ff1493;
        color: white;
    }
    /* Sidebar / Kotak Login */
    div[data-testid="stForm"] {
        background-color: #ffe4e1;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #ffb6c1;
    }
    /* Styling */
    .watermark {
        position: fixed;
        bottom: 10px;
        right: 15px;
        font-size: 15px;
        color: #d81b60;
        opacity: 0.6;
        font-weight: bold;
        z-index: 999;
    }
    </style>
    
    <!-- Elemen Watermark -->
    <div class="watermark">By: Angelia</div>
""",
    unsafe_allow_html=True,
)

# --- SISTEM LOGIN ---
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False

if not st.session_state.logged_in:
  st.title("Login Terlebih Dahulu Ya!")
  with st.form("login_form"):
    password_input = st.text_input("Masukkan Password:", type="password")
    submit_login = st.form_submit_button("Login")

    if submit_login:
      if password_input == "&jel":
        st.session_state.logged_in = True
        st.rerun()
      else:
        st.error("Password salah!")
  st.stop()

# --- APLIKASI UTAMA (SETELAH LOGIN) ---
st.title("Kalkulator Bunker")

# Tombol Logout di sidebar
with st.sidebar:
  st.write("Menu Navigasi")
  if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Pilihan Kapal
pilihan_kapal = st.selectbox(
    "Pilih Vessel:",
    [
        "MPMT XII / MPMT XV",
        "FALCON 19",
        "SEAGULL 201",
        "SEAGULL 202",
        "SEAGULL 351",
    ],
)

# Pilihan Metode Input
metode_input = st.radio(
    "Pilih Metode Input Data:",
    ["Upload File Excel (.xlsx)", "Input Manual (Tabel Excel-like)"],
)

df_clean = None

if metode_input == "Upload File Excel (.xlsx)":
  uploaded_file = st.file_uploader("Upload File (NO SUMMARY)", type=["xlsx"])

  if uploaded_file is not None:
    try:
      df = pd.read_excel(uploaded_file, header=None)
      if pilihan_kapal == "FALCON 19":
        start_row = 4
      else:
        start_row = 5
      df_data = df.iloc[start_row:].copy()

      df_clean = pd.DataFrame()
      df_clean["Datetime"] = pd.to_datetime(
          df_data.iloc[:, 2].astype(str) + " " + df_data.iloc[:, 3].astype(str),
          errors="coerce",
      )

      # Penanganan khusus Falcon 19 (1 RPM) vs Kapal Lainnya (2 RPM)
      if pilihan_kapal == "FALCON 19":
        df_clean["RPM"] = pd.to_numeric(df_data.iloc[:, 6], errors="coerce")
      else:
        df_clean["RPM_Port"] = pd.to_numeric(df_data.iloc[:, 5], errors="coerce")
        df_clean["RPM_Stbd"] = pd.to_numeric(df_data.iloc[:, 6], errors="coerce")

      df_clean = df_clean.dropna(subset=["Datetime"]).reset_index(drop=True)
    except Exception as e:
      st.error(f"Terjadi kesalahan saat memproses file: {e}")

else:
  st.subheader("Input Data Manual (Waktu & RPM)")
  st.info(
      "Silakan isi tanggal/waktu (format: YYYY-MM-DD HH:MM:SS) serta nilai RPM"
      " pada tabel di bawah ini:"
  )

  # Template default untuk input manual berdasarkan pilihan kapal
  if pilihan_kapal == "FALCON 19":
    default_data = pd.DataFrame({
        "Datetime": [
            pd.Timestamp("2026-10-01 00:00:00"),
            pd.Timestamp("2026-10-01 04:00:00"),
        ],
        "RPM": [0, 0],
    })
  else:
    default_data = pd.DataFrame({
        "Datetime": [
            pd.Timestamp("2026-10-01 00:00:00"),
            pd.Timestamp("2026-10-01 04:00:00"),
        ],
        "RPM_Port": [0, 0],
        "RPM_Stbd": [0, 0],
    })

  edited_df = st.data_editor(
      default_data, num_rows="dynamic", use_container_width=True
  )

  if not edited_df.empty:
    df_clean = edited_df.copy()
    df_clean["Datetime"] = pd.to_datetime(df_clean["Datetime"], errors="coerce")
    if pilihan_kapal == "FALCON 19":
      df_clean["RPM"] = pd.to_numeric(df_clean["RPM"], errors="coerce")
    else:
      df_clean["RPM_Port"] = pd.to_numeric(df_clean["RPM_Port"], errors="coerce")
      df_clean["RPM_Stbd"] = pd.to_numeric(df_clean["RPM_Stbd"], errors="coerce")

# Proses Perhitungan jika data sudah tersedia
if df_clean is not None and not df_clean.empty:
  if st.button("Jalankan Perhitungan"):
    try:
      # Hitung Durasi (dalam hari) antar baris waktu
      df_clean["Duration_Days"] = (
          df_clean["Datetime"].diff().dt.total_seconds() / 86400
      )
      df_clean.loc[0, "Duration_Days"] = 0.0

      steaming_time = df_clean["Duration_Days"].sum()

      if pilihan_kapal == "MPMT XII / MPMT XV":
        c1, c2 = 0.334336, 3.92556
        df_clean["ME"] = (
            (c1 / 2)
            * (
                np.exp(c2 * (df_clean["RPM_Port"] / 1000))
                + np.exp(c2 * (df_clean["RPM_Stbd"] / 1000))
            )
            * df_clean["Duration_Days"]
        )
        total_me = round(df_clean["ME"].sum(), 3)
        total_ae = round(steaming_time * 0.575, 3)
        total_me_ae = round(total_me + total_ae, 3)
        st.success(
            f"**Total ME:** {total_me:.3f} | **Total AE:** {total_ae:.3f} |"
            f" **Total ME + AE:** {total_me_ae:.3f}"
        )

      elif pilihan_kapal == "SEAGULL 201":
        c1, c2 = 0.26384, 2.028009
        df_clean["ME_DAN_AE"] = (
            (c1 / 2)
            * (
                np.exp(c2 * (df_clean["RPM_Port"] / 1000))
                + np.exp(c2 * (df_clean["RPM_Stbd"] / 1000))
            )
            * df_clean["Duration_Days"]
        )
        total_me_ae = round(df_clean["ME_DAN_AE"].sum(), 3)
        st.success(f"**Total ME DAN AE:** {total_me_ae:.3f}")

      elif pilihan_kapal == "SEAGULL 202":
        c1, c2 = 0.609554, 1.223332
        df_clean["ME"] = (
            (c1 / 2)
            * (
                np.exp(c2 * (df_clean["RPM_Port"] / 1000))
                + np.exp(c2 * (df_clean["RPM_Stbd"] / 1000))
            )
            * df_clean["Duration_Days"]
        )
        total_me = round(df_clean["ME"].sum(), 3)
        total_ae = round(steaming_time * 0.29, 3)
        total_me_ae = round(total_me + total_ae, 3)
        st.success(
            f"**Total ME:** {total_me:.3f} | **Total AE:** {total_ae:.3f} |"
            f" **Total ME + AE:** {total_me_ae:.3f}"
        )

      elif pilihan_kapal == "SEAGULL 351":
        c1, c2 = 0.222352, 2.648732
        df_clean["ME"] = (
            (c1 / 2)
            * (
                np.exp(c2 * (df_clean["RPM_Port"] / 1000))
                + np.exp(c2 * (df_clean["RPM_Stbd"] / 1000))
            )
            * df_clean["Duration_Days"]
        )
        total_me = round(df_clean["ME"].sum(), 3)
        total_ae = round(steaming_time * 0.29, 3)
        total_me_ae = round(total_me + total_ae, 3)
        st.success(
            f"**Total ME:** {total_me:.3f} | **Total AE:** {total_ae:.3f} |"
            f" **Total ME + AE:** {total_me_ae:.3f}"
        )

      elif pilihan_kapal == "FALCON 19":
        c3, c4 = 0.229405, 12.113255
        df_clean["ME"] = (
            c3
            * np.exp(c4 * (df_clean["RPM"] / 1000))
            * df_clean["Duration_Days"]
        )
        total_me = round(df_clean["ME"].sum(), 3)
        total_ae = round(steaming_time * 0.7, 3)
        total_me_ae = round(total_me + total_ae, 3)
        st.success(
            f"**Total ME:** {total_me:.3f} | **Total AE:** {total_ae:.3f} |"
            f" **Total ME + AE:** {total_me_ae:.3f}"
        )

      st.subheader("Detail Tabel Hasil Perhitungan")
      st.dataframe(df_clean)

      # Perbaikan Tombol Download Excel menggunakan io.BytesIO
      output = io.BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_clean.to_excel(writer, index=False, sheet_name="Hasil Kalkulasi")
      xlsx_result = output.getvalue()

      st.download_button(
          label="Download Hasil Perhitungan (.xlsx)",
          data=xlsx_result,
          file_name="hasil_bunker_calculator.xlsx",
          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      )
    except Exception as e:
      st.error(f"Terjadi kesalahan saat menghitung: {e}")