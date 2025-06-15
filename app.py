import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Peta Dealer dan POS", layout="wide")

st.title("Peta Dealer dan POS Jawa Barat")

# --- Upload File ---
excel_file = st.file_uploader("Upload File Excel Dealer (xlsx/csv)", type=['xlsx', 'csv'])
geojson_file = st.file_uploader("Upload File GeoJSON Batas Kecamatan", type=['geojson'])

if excel_file is not None and geojson_file is not None:
    # Load Excel
    if excel_file.name.endswith('.csv'):
        dealer_df = pd.read_csv(excel_file)
    else:
        dealer_df = pd.read_excel(excel_file)

    # Bersihkan header
    dealer_df.columns = dealer_df.columns.str.strip()

    # Load GeoJSON
    jabar_map = gpd.read_file(geojson_file)
    jabar_map = jabar_map.to_crs(epsg=4326)

    # Buat GeoDataFrame dealer
    geometry = [Point(xy) for xy in zip(dealer_df['LONGITUDE'], dealer_df['LATITUDE'])]
    dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=geometry, crs='EPSG:4326')

    # Dropdown Kabupaten dan Dealer
    kabupaten_options = dealer_gdf['AREA'].unique()
    selected_kabupaten = st.selectbox('Pilih Kabupaten:', kabupaten_options)

    filtered_dealers = dealer_gdf[dealer_gdf['AREA'] == selected_kabupaten]['KODE'].unique()
    selected_dealer = st.selectbox('Pilih Dealer/POS:', filtered_dealers)

    # Tampilkan Peta
    m = folium.Map(location=[-6.9, 107.6], zoom_start=10)

    # Plot semua dealer dan pos di kabupaten tersebut
    dealers_in_kabupaten = dealer_gdf[dealer_gdf['AREA'] == selected_kabupaten]

    for idx, dealer in dealers_in_kabupaten.iterrows():
        label_prefix = "Dealer" if dealer['CHANNEL'] == 'DEALER' else "Pos"
        marker_color = "red" if dealer['CHANNEL'] == 'DEALER' else "blue"
        folium.Marker(
            location=[dealer['LATITUDE'], dealer['LONGITUDE']],
            popup=f"{label_prefix}: {dealer['KODE']}<br>{dealer['NAMA CHANNEL']}",
            icon=folium.Icon(color=marker_color,_
