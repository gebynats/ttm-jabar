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
def load_csv(url):
    return pd.read_csv(url)

# Google Drive direct download links
geojson_url = 'https://drive.google.com/uc?id=1nMWyPZ1X5JY9nO4QSsT_N0b4i7wxzMTF'
csv_url = 'https://docs.google.com/spreadsheets/d/1f7aLwp7-NfmdUKcsu1cmVE54ltzF8WdS/export?format=csv'

# Load data
jabar_map = load_geojson(geojson_url)
dealer_df = load_csv(csv_url)

dealer_df.columns = dealer_df.columns.str.strip().str.upper()

# Pastikan kolom Latitude dan Longitude numeric
dealer_df['Latitude'] = pd.to_numeric(dealer_df['Latitude'], errors='coerce')
dealer_df['Longitude'] = pd.to_numeric(dealer_df['Longitude'], errors='coerce')
dealer_df = dealer_df.dropna(subset=['Latitude', 'Longitude'])

# Convert ke GeoDataFrame
geometry = [Point(xy) for xy in zip(dealer_df['Longitude'], dealer_df['Latitude'])]
dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=geometry, crs='EPSG:4326')

# --- SIDEBAR FILTER ---
st.sidebar.title('Filter Dealer')
channel_options = dealer_gdf['Channel'].unique()
selected_channel = st.sidebar.selectbox('Pilih Channel:', ['Semua'] + list(channel_options))

if selected_channel != 'Semua':
    filtered_dealer_gdf = dealer_gdf[dealer_gdf['Channel'] == selected_channel]
else:
    filtered_dealer_gdf = dealer_gdf

area_options = filtered_dealer_gdf['Area'].unique()
selected_area = st.sidebar.selectbox('Pilih Area:', ['Semua'] + list(area_options))

if selected_area != 'Semua':
    filtered_dealer_gdf = filtered_dealer_gdf[filtered_dealer_gdf['Area'] == selected_area]

dealer_options = filtered_dealer_gdf['Kode Dealer'].unique()
selected_dealers = st.sidebar.multiselect('Pilih Dealer:', dealer_options)

# --- PLOTTING MAP ---
if len(filtered_dealer_gdf) > 0:
    m = folium.Map(location=[filtered_dealer_gdf.iloc[0]['Latitude'], filtered_dealer_gdf.iloc[0]['Longitude']], zoom_start=8)

    # Batas Kecamatan
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

    # Tampilkan semua dealer yang sesuai filter
    for idx, row in filtered_dealer_gdf.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"{row['Kode Dealer']} - {row.get('Nama Dealer', '')}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    # Kalau dealer sudah dipilih, tampilkan ring
    if selected_dealers:
        for dealer_code in selected_dealers:
            dealer_selected = dealer_gdf[dealer_gdf['Kode Dealer'] == dealer_code].iloc[0]

            # Tambahkan Ring 3
            folium.Circle(
                location=[dealer_selected['Latitude'], dealer_selected['Longitude']],
                radius=15000,
                color='red',
                fill=True,
                fill_opacity=0.1,
                popup='Ring 3 (<15km)'
            ).add_to(m)

            # Tambahkan Ring 2
            folium.Circle(
                location=[dealer_selected['Latitude'], dealer_selected['Longitude']],
                radius=10000,
                color='orange',
                fill=True,
                fill_opacity=0.2,
                popup='Ring 2 (<10km)'
            ).add_to(m)

            # Tambahkan Ring 1
            folium.Circle(
                location=[dealer_selected['Latitude'], dealer_selected['Longitude']],
                radius=5000,
                color='green',
                fill=True,
                fill_opacity=0.3,
                popup='Ring 1 (<5km)'
            ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=800, height=600)

else:
    st.write("Data dealer tidak ditemukan untuk filter yang dipilih.")
