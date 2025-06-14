import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# --- LOAD DATA ---
geojson_url = 'https://drive.google.com/uc?id=1nMWyPZ1X5JY9nO4QSsT_N0b4i7wxzMTF'
excel_url = 'https://docs.google.com/spreadsheets/d/1f7aLwp7-NfmdUKcsu1cmVE54ltzF8WdS/export?format=xlsx'

# Load dealer data
dealer_df = pd.read_excel(excel_url)

# Load geojson map
jabar_map = gpd.read_file(geojson_url)

# --- STREAMLIT APP ---
st.title("Dealer dan POS Jabar Map")

# Dropdown Kabupaten
kabupaten_options = dealer_df['AREA'].unique()
selected_kabupaten = st.selectbox('Pilih Kabupaten', kabupaten_options)

# Dropdown Dealer
filtered_dealers = dealer_df[dealer_df['AREA'] == selected_kabupaten]['KODE'].unique()
selected_dealer = st.selectbox('Pilih Dealer / POS', filtered_dealers)

# Convert dealer data to GeoDataFrame
dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=gpd.points_from_xy(dealer_df['LONGITUDE'], dealer_df['LATITUDE']), crs='EPSG:4326')

# Function to plot folium map
def plot_folium(selected_kabupaten, selected_dealer):
    m = folium.Map(location=[-6.9, 107.6], zoom_start=10)

    # Plot all dealers in selected kabupaten
    dealers_in_kabupaten = dealer_gdf[dealer_gdf['AREA'] == selected_kabupaten]

    for idx, dealer in dealers_in_kabupaten.iterrows():
        label_prefix = "Dealer" if dealer['CHANNEL'] == 'DEALER' else "Pos"
        marker_color = "red" if dealer['CHANNEL'] == 'DEALER' else "blue"
        folium.Marker(
            location=[dealer['LATITUDE'], dealer['LONGITUDE']],
            popup=f"{label_prefix}: {dealer['KODE']}<br>{dealer['NAMA CHANNEL']}",
            icon=folium.Icon(color=marker_color, icon='car')
        ).add_to(m)

    # Plot ring for selected dealer
    selected_dealer_data = dealer_gdf[dealer_gdf['KODE'] == selected_dealer]

    if not selected_dealer_data.empty:
        dealer_selected = selected_dealer_data.iloc[0]

        # Ring 3
        folium.Circle(
            location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
            radius=15000,
            color='red',
            fill=True,
            fill_opacity=0.1,
            popup='Ring 3 (<15km)'
        ).add_to(m)

        # Ring 2
        folium.Circle(
            location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
            radius=10000,
            color='orange',
            fill=True,
            fill_opacity=0.2,
            popup='Ring 2 (<10km)'
        ).add_to(m)

        # Ring 1
        folium.Circle(
            location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
            radius=5000,
            color='green',
            fill=True,
            fill_opacity=0.3,
            popup='Ring 1 (<5km)'
        ).add_to(m)

        # Highlight selected dealer
        label_prefix = "Dealer" if dealer_selected['CHANNEL'] == 'DEALER' else "Pos"
        marker_color = "red" if dealer_selected['CHANNEL'] == 'DEALER' else "blue"
        folium.Marker(
            location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
            popup=f"{label_prefix}: {dealer_selected['KODE']}<br>{dealer_selected['NAMA CHANNEL']}",
            icon=folium.Icon(color=marker_color, icon='info-sign')
        ).add_to(m)

    # Add GeoJSON layer (batas kecamatan)
    folium.GeoJson(
        jabar_map,
        name='Batas Kecamatan',
        style_function=lambda x: {
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['WADMKK', 'WADMKC'],
            aliases=['Kabupaten:', 'Kecamatan:'],
            sticky=False
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m

# Tampilkan peta
st.write('Peta Dealer dan POS')
map_folium = plot_folium(selected_kabupaten, selected_dealer)
st_folium(map_folium, width=800, height=600)
