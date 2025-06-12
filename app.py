import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Search, MeasureControl
from streamlit_folium import st_folium
from shapely.geometry import Point

# --- LOAD DATA DENGAN CACHE ---
@st.cache_data
def load_geojson(url):
    gdf = gpd.read_file(url)
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.05, preserve_topology=True)
    return gdf

@st.cache_data
def load_excel(url):
    return pd.read_excel(url)

# --- URL DATA ---
geojson_url = 'https://drive.google.com/uc?id=1nMWyPZ1X5JY9nO4QSsT_N0b4i7wxzMTF'
excel_url = 'https://docs.google.com/spreadsheets/d/1f7aLwp7-NfmdUKcsu1cmVE54ltzF8WdS/export?format=xlsx'

# --- LOAD DATA ---
jabar_map = load_geojson(geojson_url)
dealer_df = load_excel(excel_url)

# --- STANDARISASI KOLOM ---
dealer_df.columns = dealer_df.columns.str.strip().str.upper()

# --- RENAME KODE TO KODE DEALER ---
dealer_df.rename(columns={
    'KODE': 'KODE DEALER'
}, inplace=True)

# --- CHECK COLUMN VALIDITY ---
required_columns = ['CHANNEL', 'AREA', 'KODE DEALER', 'LATITUDE', 'LONGITUDE']
missing_columns = [col for col in required_columns if col not in dealer_df.columns]

if missing_columns:
    st.error(f"Kolom berikut tidak ditemukan di data: {missing_columns}")
    st.stop()

# --- DEBUG: Tampilkan Kolom ---
st.write('Kolom yang tersedia:', dealer_df.columns.tolist())

# Pastikan latitude dan longitude numerik
dealer_df['LATITUDE'] = pd.to_numeric(dealer_df['LATITUDE'], errors='coerce')
dealer_df['LONGITUDE'] = pd.to_numeric(dealer_df['LONGITUDE'], errors='coerce')

# Konversi ke GeoDataFrame
geometry = [Point(xy) for xy in zip(dealer_df['LONGITUDE'], dealer_df['LATITUDE'])]
dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=geometry, crs='EPSG:4326')

# --- SIDEBAR FILTER ---
st.sidebar.title('Filter Dealer')

channel_options = dealer_gdf['CHANNEL'].dropna().unique()
selected_channel = st.sidebar.selectbox('Pilih Channel:', ['Semua'] + list(channel_options))

if selected_channel != 'Semua':
    filtered_area = dealer_gdf[dealer_gdf['CHANNEL'] == selected_channel]
else:
    filtered_area = dealer_gdf

area_options = filtered_area['AREA'].dropna().unique()
selected_area = st.sidebar.selectbox('Pilih Area:', ['Semua'] + list(area_options))

if selected_area != 'Semua':
    filtered_dealers = filtered_area[filtered_area['AREA'] == selected_area]
else:
    filtered_dealers = filtered_area

dealer_options = filtered_dealers['KODE DEALER'].unique()
selected_dealers = st.sidebar.multiselect('Pilih Dealer:', dealer_options)

# --- PLOTTING MAP ---
if selected_channel != 'Semua' and selected_area != 'Semua':
    m = folium.Map(location=[filtered_dealers['LATITUDE'].mean(), filtered_dealers['LONGITUDE'].mean()], zoom_start=9)

    style_normal = {'fillColor': '#ffffff00', 'color': 'black', 'weight': 1}
    style_highlight = {'fillColor': '#ffff00', 'color': 'red', 'weight': 2}

    geojson = folium.GeoJson(
        jabar_map,
        name='Batas Kecamatan',
        style_function=lambda x: style_normal,
        highlight_function=lambda x: style_highlight,
        tooltip=folium.GeoJsonTooltip(fields=['WADMKC'], aliases=['Kecamatan:'])
    ).add_to(m)

    Search(
        layer=geojson,
        geom_type='Polygon',
        placeholder='Cari Kecamatan...',
        search_label='WADMKC',
        collapsed=False
    ).add_to(m)

    # Tambahkan kontrol pengukur jarak
    m.add_child(MeasureControl())

    # Tampilkan semua dealer
    for idx, row in filtered_dealers.iterrows():
        folium.Marker(
            location=[row['LATITUDE'], row['LONGITUDE']],
            popup=f"{row['KODE DEALER']}<br>{row.get('NAMA CHANNEL', '')}",
            icon=folium.Icon(color='gray', icon='info-sign')
        ).add_to(m)

    # Tampilkan ring jika dealer dipilih
    if selected_dealers:
        for dealer_code in selected_dealers:
            dealer_selected = dealer_gdf[dealer_gdf['KODE DEALER'] == dealer_code].iloc[0]

            folium.Circle(
                location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
                radius=15000,
                color='red',
                fill=True,
                fill_opacity=0.1,
                popup='Ring 3 (<15km)'
            ).add_to(m)

            folium.Circle(
                location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
                radius=10000,
                color='orange',
                fill=True,
                fill_opacity=0.2,
                popup='Ring 2 (<10km)'
            ).add_to(m)

            folium.Circle(
                location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
                radius=5000,
                color='green',
                fill=True,
                fill_opacity=0.3,
                popup='Ring 1 (<5km)'
            ).add_to(m)

            folium.Marker(
                location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
                popup=f"Dealer: {dealer_selected['KODE DEALER']}<br>{dealer_selected.get('NAMA CHANNEL', '')}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=800, height=600)

else:
    st.write("Silakan pilih Channel dan Area terlebih dahulu.")
