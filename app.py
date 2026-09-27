import streamlit as st
import folium
from streamlit_folium import st_folium
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Akıllı Rota ve Lojistik Optimizasyonu",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Akıllı Rota ve Lojistik Optimizasyon Merkezi")
st.markdown("İstanbul teslimat operasyonları için hızlı, karşılaştırılabilir ve harita destekli rota planlama.")

# Sidebar - Kontrol Paneli
st.sidebar.header("Planlama Ayarları")

# Senaryo Seçimi
senaryo = st.sidebar.selectbox(
    "Hazır senaryo",
    ["İstanbul Avrupa-Anadolu turu", "Beşiktaş - Şişli Dağıtım", "Kadıköy - Maltepe Bölgesi", "Özel / Rastgele Noktalar"]
)

# Durak Sayısı
n_duraklar = st.sidebar.slider("Teslimat noktası sayısı", min_value=3, max_value=15, value=8)

# Operasyon Varsayımları
st.sidebar.subheader("Operasyon Varsayımları")
tuketim = st.sidebar.number_input("Yakıt tüketimi (lt / 100 km)", value=8.5)
yakit_fiyati = st.sidebar.number_input("Yakıt fiyatı (TL / Lt)", value=52.0)
ortalama_hiz = st.sidebar.number_input("Ortalama hız (km / saat)", value=28.0)

# Koordinat Belirleme (Senaryoya göre)
np.random.seed(42)
if "Avrupa-Anadolu" in senaryo:
    merkez_lat, merkez_lon = 41.0082, 28.9784
    lats = merkez_lat + np.random.uniform(-0.05, 0.05, n_duraklar)
    lons = merkez_lon + np.random.uniform(-0.08, 0.08, n_duraklar)
elif "Beşiktaş" in senaryo:
    merkez_lat, merkez_lon = 41.0422, 29.0077
    lats = merkez_lat + np.random.uniform(-0.02, 0.02, n_duraklar)
    lons = merkez_lon + np.random.uniform(-0.02, 0.02, n_duraklar)
else:
    merkez_lat, merkez_lon = 40.9901, 29.0253
    lats = merkez_lat + np.random.uniform(-0.03, 0.03, n_duraklar)
    lons = merkez_lon + np.random.uniform(-0.03, 0.03, n_duraklar)

# Depo ve Durak Listesi
depo = (merkez_lat, merkez_lon)
duraklar = list(zip(lats, lons))

# Basit TSP (Gezgin Satıcı) Sıralaması (En Yakın Komşu Sezgiseli)
def tsp_cozucu(depo_koor, durak_listesi):
    tum_noktalar = [depo_koor] + durak_listesi
    n = len(tum_noktalar)
    koordinat_matrisi = cdist(tum_noktalar, tum_noktalar, metric='euclidean')
    
    ziyaret_edildi = [False] * n
    rota = [0] # Depodan başla
    ziyaret_edildi[0] = True
    
    toplam_mesafe_derece = 0
    anlik = 0
    for _ in range(n - 1):
        en_yakin = -1
        min_mesafe = float('inf')
        for j in range(n):
            if not ziyaret_edildi[j] and koordinat_matrisi[anlik][j] < min_mesafe:
                min_mesafe = koordinat_matrisi[anlik][j]
                en_yakin = j
        ziyaret_edildi[en_yakin] = True
        rota.append(en_yakin)
        toplam_mesafe_derece += min_mesafe
        anlik = en_yakin
        
    # Depoya dönüş
    rota.append(0)
    toplam_mesafe_derece += koordinat_matrisi[anlik][0]
    
    toplam_km = toplam_mesafe_derece * 111
    return rota, tum_noktalar, toplam_km

rota_indeksleri, tum_koordinatlar, toplam_mesafe = tsp_cozucu(depo, duraklar)

# Metrik Hesaplamaları
tahmini_sure_dakika = (toplam_mesafe / ortalama_hiz) * 60
tahmini_maliyet = (toplam_mesafe / 100) * tuketim * yakit_fiyati

# Üst Metrik Kartları
col1, col2, col3, col4 = st.columns(4)
col1.metric("Teslimat Noktası", f"{n_duraklar}")
col2.metric("Toplam Mesafe", f"{toplam_mesafe:.2f} km")
col3.metric("Tahmini Süre", f"{int(tahmini_sure_dakika)} dk")
col4.metric("Yakıt Maliyeti", f"₺{tahmini_maliyet:.2f}")

st.markdown("---")

# Harita Oluşturma
m = folium.Map(location=depo, zoom_start=13, tiles="OpenStreetMap")

# Depo İşareti
folium.Marker(
    location=depo,
    popup="Merkez Depo",
    icon=folium.Icon(color="red", icon="home", prefix="fa")
).add_to(m)

# Durak İşaretleri
for i, durak in enumerate(duraklar, 1):
    folium.Marker(
        location=durak,
        popup=f"Teslimat Noktası {i}",
        icon=folium.Icon(color="blue", icon="shopping-cart", prefix="fa")
    ).add_to(m)

# Rota Çizgileri
rota_koordinatlari = [tum_koordinatlar[i] for i in rota_indeksleri]
folium.PolyLine(rota_koordinatlari, color="green", weight=4, opacity=0.8).add_to(m)

# Haritayı Ekrana Bas
st.subheader("🗺️ Optimizasyon Haritası ve Rota Güzergahı")
st_data = st_folium(m, width=1100, height=550)

# Rota Detay Tablosu
st.subheader("📋 Ziyaret Sıralaması")
rota_sirasi_df = pd.DataFrame({
    "Adım": range(1, len(rota_indeksleri)),
    "Nokta Tipi": ["Depo" if idx == 0 else f"Teslimat Noktası {idx}" for idx in rota_indeksleri[:-1]],
    "Enlem": [tum_koordinatlar[idx][0] for idx in rota_indeksleri[:-1]],
    "Boylam": [tum_koordinatlar[idx][1] for idx in rota_indeksleri[:-1]]
})
st.table(rota_sirasi_df)