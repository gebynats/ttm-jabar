import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import Search
from streamlit_folium import st_folium
from shapely.geometry import Point

# --- LOAD DATA DENGAN CACHE ---
@st.cache_data
def load_geojson(url):
    gdf = gpd.read_file(url)
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001, preserve_topology=True)
    return gdf

@st.cache_data
def load_excel(url):
    return pd.read_excel(url)

# Load data
geojson_url = 'https://drive.google.com/uc?id=1nMWyPZ1X5JY9nO4QSsT_N0b4i7wxzMTF'
excel_url = 'https://docs.google.com/spreadsheets/d/1f7aLwp7-NfmdUKcsu1cmVE54ltzF8WdS/export?format=xlsx'

jabar_map = load_geojson(geojson_url)
dealer_df = load_excel(excel_url)

# Bersihkan nama kolom
dealer_df.columns = dealer_df.columns.str.strip().str.upper()

# Pastikan latitude & longitude numeric
dealer_df['LATITUDE'] = pd.to_numeric(dealer_df['LATITUDE'], errors='coerce')
dealer_df['LONGITUDE'] = pd.to_numeric(dealer_df['LONGITUDE'], errors='coerce')

# Konversi ke GeoDataFrame
geometry = [Point(xy) for xy in zip(dealer_df['LONGITUDE'], dealer_df['LATITUDE'])]
dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=geometry, crs='EPSG:4326')

# --- SIDEBAR FILTER ---
st.sidebar.title('Filter Dealer')

channel_options = dealer_gdf['CHANNEL'].dropna().unique()
selected_channel = st.sidebar.selectbox('Pilih Channel:', options=['All'] + list(channel_options))

area_options = dealer_gdf['AREA'].dropna().unique()
selected_area = st.sidebar.selectbox('Pilih Area:', options=['All'] + list(area_options))

# Filter data sesuai channel dan area
filtered_dealers = dealer_gdf.copy()

if selected_channel != 'All':
    filtered_dealers = filtered_dealers[filtered_dealers['CHANNEL'] == selected_channel]

if selected_area != 'All':
    filtered_dealers = filtered_dealers[filtered_dealers['AREA'] == selected_area]

dealer_options = filtered_dealers['KODE DEALER'].unique()
selected_dealers = st.sidebar.multiselect('Pilih Dealer:', dealer_options)

# --- PLOTTING MAP ---
if not filtered_dealers.empty:
    # Pusatkan ke dealer pertama
    first_point = filtered_dealers.iloc[0]
    m = folium.Map(location=[first_point['LATITUDE'], first_point['LONGITUDE']], zoom_start=9)

    # Tambahkan batas kecamatan
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

    # Tampilkan semua dealer yang terfilter
    for idx, row in filtered_dealers.iterrows():
        folium.Marker(
            location=[row['LATITUDE'], row['LONGITUDE']],
            popup=f"Dealer: {row['KODE DEALER']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    # Jika dealer sudah dipilih → tampilkan ring
    if selected_dealers:
        for dealer_code in selected_dealers:
            dealer_selected = filtered_dealers[filtered_dealers['KODE DEALER'] == dealer_code].iloc[0]

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

    folium.LayerControl().add_to(m)

    st_folium(m, width=800, height=600)

else:
    st.write("Data tidak ditemukan. Coba ubah filter channel atau area.")
