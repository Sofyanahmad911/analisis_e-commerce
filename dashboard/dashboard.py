import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Konfigurasi Halaman Utama
st.set_page_config(
    page_title="E-Commerce Insights",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk gaya profesional dan modern
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stPlotlyChart {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .insight-card {
        background-color: #ffffff;
        border-left: 5px solid #3b82f6;
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .recommendation-card {
        background-color: #eff6ff;
        border-left: 5px solid #3b82f6;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #0f172a;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    try:
        # Memuat data utama (fokus pada pesanan yang sudah 'delivered')
        df_main = pd.read_csv('dashboard/main_data.csv')
        
        # Konversi kolom tanggal ke datetime
        if 'order_purchase_timestamp' in df_main.columns:
            df_main['order_purchase_timestamp'] = pd.to_datetime(df_main['order_purchase_timestamp'])
        
        # Penanganan nama kategori
        cat_col = 'product_category_name_english' if 'product_category_name_english' in df_main.columns else 'product_category'
        
        return df_main, cat_col
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return pd.DataFrame(), ""

df_main, cat_col = load_data()

# --- SIDEBAR & FILTER ---
with st.sidebar:
    st.markdown("##  Filter Dashboard")
    st.markdown("---")
    
    if not df_main.empty:
        # Filter Rentang Waktu
        min_date = df_main['order_purchase_timestamp'].min().date()
        max_date = df_main['order_purchase_timestamp'].max().date()
        
        selected_date_range = st.date_input(
            "Periode Analisis",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        if isinstance(selected_date_range, (list, tuple)) and len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
        else:
            start_date = end_date = (selected_date_range[0] if isinstance(selected_date_range, list) else selected_date_range)

        # Filter Kategori Produk
        all_categories = sorted(df_main[cat_col].dropna().unique().tolist())
        selected_cat = st.multiselect(
            "Kategori Fokus", 
            options=all_categories, 
            default=all_categories if len(all_categories) > 5 else all_categories
        )

        # PROSES FILTER DATA
        mask = (df_main['order_purchase_timestamp'].dt.date >= start_date) & \
               (df_main['order_purchase_timestamp'].dt.date <= end_date)
        
        df_filtered = df_main.loc[mask]
        
        if selected_cat:
            df_filtered = df_filtered[df_filtered[cat_col].isin(selected_cat)]
    else:
        df_filtered = pd.DataFrame()
        start_date = end_date = datetime.now().date()

    st.markdown("---")
    st.success(f"Analisis pada {len(df_filtered):,} transaksi")

# --- PERHITUNGAN DINAMIS ---
if not df_filtered.empty:
    total_customers = df_filtered['customer_id'].nunique()
    total_rev = df_filtered['price'].sum()
    avg_score = df_filtered['review_score'].mean()
    total_orders = df_filtered['order_id'].nunique()

    # Tren Bulanan
    df_filtered['month_year'] = df_filtered['order_purchase_timestamp'].dt.to_period('M').astype(str)
    trend_data = df_filtered.groupby('month_year').agg(
        order_count=('order_id', 'nunique'),
        revenue=('price', 'sum')
    ).reset_index().sort_values('month_year')

    # Performa Review (Worst Performing)
    review_perf = df_filtered.groupby(cat_col).agg(
        avg_score=('review_score', 'mean'),
        sales_count=('order_id', 'count')
    ).reset_index()
    lowest_reviews = review_perf[review_perf['sales_count'] > 10].sort_values('avg_score').head(8)
    
    # Distribusi Revenue per Kategori
    revenue_dist = df_filtered.groupby(cat_col)['price'].sum().reset_index().sort_values('price', ascending=False).head(10)
else:
    total_customers = total_rev = avg_score = total_orders = 0
    trend_data = lowest_reviews = revenue_dist = pd.DataFrame()

# --- TAMPILAN DASHBOARD ---
st.title("Analisis Performa E-Commerce")
st.markdown(f"Wawasan operasional berdasarkan data transaksi (**{start_date}** - **{end_date}**)")

# KPI Utama di atas tab
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Pelanggan Unik", f"{total_customers:,}")
with k2:
    st.metric("Total Penjualan", f"Rp {total_rev:,.0f}")
with k3:
    st.metric("Kepuasan Pelanggan", f"{avg_score:.2f} / 5.0")
with k4:
    st.metric("Total Pesanan", f"{total_orders:,}")

st.markdown("---")

# --- TAB INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Ringkasan Eksekutif", 
    "Tren Pesanan (Q1)", 
    "Kualitas Produk (Q2)", 
    "Strategi & Insight"
])

with tab1:
    st.subheader("Ringkasan Performa")
    c1, c2 = st.columns([2, 1])
    with c1:
        if not trend_data.empty:
            fig_sum = px.line(trend_data, x='month_year', y='order_count', title="Volume Pesanan Bulanan")
            st.plotly_chart(fig_sum, use_container_width=True)
    with c2:
        if not revenue_dist.empty:
            fig_pie_sum = px.pie(revenue_dist, values='price', names=cat_col, title="Top 10 Kategori (Revenue)", hole=0.4)
            st.plotly_chart(fig_pie_sum, use_container_width=True)
    
    st.markdown("""
    **Ringkasan Kondisi:**
    Data menunjukkan pertumbuhan yang stabil dengan konsentrasi revenue pada kategori tertentu. Fokus utama saat ini adalah menjaga kestabilan kepuasan pelanggan yang berada di angka ~4.0.
    """)

with tab2:
    st.header("Pertanyaan 1: Tren Pesanan Bulanan")
    st.markdown("> **Bagaimana tren jumlah pesanan bulanan selama periode waktu yang tersedia?**")
    
    if not trend_data.empty:
        fig_trend = px.area(
            trend_data, 
            x='month_year', 
            y='order_count',
            labels={'month_year': 'Bulan', 'order_count': 'Volume Pesanan'},
            color_discrete_sequence=['#3b82f6'],
            template='plotly_white',
            line_shape='spline'
        )
        #  Membuat chart dalam bentuk Bar Chart / Histogram
        fig_trend = px.bar(
            trend_data, 
            x='month_year', 
            y='order_count',
            text='order_count',
            color_discrete_sequence=["#3b82f6"]
        )

        fig_trend.update_traces(textposition='outside')

        fig_trend.update_xaxes(
            type='category',     # Memaksa Plotly membaca setiap bulan sebagai kategori terpisah
            tickangle=-45,       # Memutar teks kemiringan 45 derajat agar tidak bertumpukan
            tickfont=dict(size=10) # Mengecilkan sedikit ukuran font jika datanya sangat banyak
        )
        
        y_val = trend_data[trend_data['month_year']=='2017-11']['order_count'].values[0] if '2017-11' in trend_data['month_year'].values else 0
        
        
        fig_trend.update_layout(
            xaxis_title="Bulan & Tahun",
            yaxis_title="Jumlah Pesanan",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=50, b=80) 
        )

        st.plotly_chart(fig_trend, use_container_width=True)
        
        st.markdown(f"""
        <div class="insight-card">
            <h4>Jawaban & Insight:</h4>
            <ul>
                <li><b>Jawaban:</b> Tren jumlah pesanan menunjukkan pertumbuhan yang signifikan dari tahun 2017 hingga pertengahan 2018.</li>
                <li><b>Puncak Tertinggi:</b> Terjadi lonjakan drastis pada <b>November 2017</b>. Hal ini dikarenakan adanya fenomena <b>Black Friday</b> di mana antusiasme belanja meningkat tajam.</li>
                <li><b>Implikasi:</b> Fluktuasi ini menunjukkan adanya ketergantungan pada event musiman untuk memicu volume transaksi besar.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Pilih rentang waktu yang mencakup tahun 2017-2018 untuk melihat tren.")

with tab3:
    st.header("Pertanyaan 2: Kualitas Kategori Produk")
    st.markdown("> **Kategori produk mana yang memiliki rata-rata skor review terendah?**")
    
    # Pastikan variabel cat_col di-set sesuai nama kolom di data Anda
    cat_col = 'product_category_name_english'
    
    # Filter HANYA untuk kategori yang penjualannya lebih dari 100
    # Agregasi review score dan jumlah transaksi per kategori
    # Menggunakan product_category_name_english jika tersedia
    category_col = 'product_category_name_english' if 'product_category_name_english' in df_main.columns else 'product_category_name'

    category_analysis_df = df_main.groupby(category_col).agg({
        'review_score': 'mean',
        'order_id': 'count'
    }).reset_index()

    category_analysis_df.columns = ['product_category', 'avg_review_score', 'transaction_count']

    # Filter kategori dengan transaksi > 100 dan review < 4
    low_rated_categories = category_analysis_df[
        (category_analysis_df['transaction_count'] > 100) &
        (category_analysis_df['avg_review_score'] < 4)
    ].sort_values(by='avg_review_score')

    # --- GRAFIK 1: Kategori dengan Rating Terendah ---
    st.subheader("Kategori dengan Rating Terendah")
    if not low_rated_categories.empty:
        fig_low = px.bar(
            low_rated_categories,
            x='avg_review_score',
            y='product_category',
            orientation='h',
            color='avg_review_score',
            color_continuous_scale='Reds',
            text='avg_review_score',             
            hover_data=['transaction_count'],  
            labels={
                'avg_review_score': 'Skor Rating', 
                'product_category': 'Kategori Produk',
                'transaction_count': 'Total Pesanan' 
            },
            template='plotly_white'
        )
        fig_low.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_low.update_layout(
            coloraxis_showscale=False,
            yaxis={'categoryorder': 'total descending'}, # Memastikan bar terurut rapi
            margin=dict(r=50) # Memberi ruang agar teks tidak terpotong
        )
        st.plotly_chart(fig_low, use_container_width=True)

    # Garis pembatas agar UI lebih rapi
    st.divider() 

    

    st.markdown(f"""
    <div class="insight-card">
        <h4>Jawaban & Insight:</h4>
        <ul>
            <li><b>Jawaban:</b> Kategori <b>'office_furniture'</b> adalah kategori dengan rata-rata skor review terendah dibandingkan kategori lainnya (untuk kategori dengan transaksi > 10).</li>
            <li><b>Masalah Kualitas:</b> Kategori perabotan kantor sering kali mendapat keluhan terkait pengiriman (barang berat/besar) atau ketidaksesuaian material.</li>
            <li><b>Kontras Revenue:</b> Meskipun beberapa kategori memiliki revenue besar, jika rating rendah dibiarkan, hal ini akan meningkatkan biaya retur dan menurunkan kepercayaan pelanggan jangka panjang.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with tab4:
    st.header("Rekomendasi Strategis")
    
    st.markdown("""
    Berdasarkan analisis data yang telah dilakukan di notebook, berikut adalah langkah konkret yang direkomendasikan:
    """)
    
    st.markdown("""
    <div class="recommendation-card">
        <strong>1. Manajemen Logistik Musiman (Fokus November)</strong><br>
        Antisipasi lonjakan pesanan seperti pada Black Friday 2017. Perusahaan perlu mempersiapkan infrastruktur logistik dan ketersediaan stok 1-2 bulan sebelum bulan November untuk menghindari keterlambatan pengiriman.
    </div>
    
    <div class="recommendation-card">
        <strong>2. Audit Kualitas Kategori Furniture</strong><br>
        Lakukan audit mendalam pada vendor di kategori <code>office_furniture</code>. Rendahnya skor ulasan menunjukkan adanya ketidakpuasan sistemik yang harus segera diperbaiki melalui peninjauan deskripsi produk, kualitas material, atau proteksi saat pengiriman.
    </div>
    
    <div class="recommendation-card">
        <strong>3. Strategi Retensi pada Kategori High-Revenue</strong><br>
        Kategori dengan kontribusi revenue besar harus dijaga stabilitas layanannya. Implementasikan program loyalitas khusus untuk kategori unggulan guna memastikan arus kas tetap stabil di luar periode diskon besar.
    </div>
    """, unsafe_allow_html=True)