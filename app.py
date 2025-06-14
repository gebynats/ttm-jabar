import streamlit as st
import folium
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from streamlit_folium import st_folium

# Load data dealer
dealer_df = pd.read_excel('/content/drive/MyDrive/Koordinat Dealer dan POS JABAR.xlsx')

# Load peta batas kecamatan
jabar_map = gpd.read_file('/content/drive/MyDrive/JAWABARAT_ADM_KEC/JAWABARAT_ADM_KEC.shp')
jabar_map = jabar_map.to_crs(epsg=4326)

# Buat GeoDataFrame dealer
geometry = [Point(xy) for xy in zip(dealer_df['LONGITUDE'], dealer_df['LATITUDE'])]
dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=geometry, crs='EPSG:4326')

# Streamlit UI
st.title('Peta Dealer dan POS Jawa Barat')

# Dropdown Kabupaten
kabupaten_options = dealer_gdf['AREA'].unique()
selected_kabupaten = st.selectbox('Pilih Kabupaten:', kabupaten_options)

# Dropdown Dealer
filtered_dealers = dealer_gdf[dealer_gdf['AREA'] == selected_kabupaten]['KODE'].unique()
if len(filtered_dealers) == 0:
    st.warning('Tidak ada dealer di kabupaten ini')
    st.stop()

selected_dealer = st.selectbox('Pilih Kode Dealer:', filtered_dealers)

# Tombol
if st.button('Tampilkan Peta'):
    # Plot Folium
    m = folium.Map(location=[-6.9, 107.6], zoom_start=10)

    # Plot semua dealer dan pos di kabupaten tersebut
    dealers_in_kabupaten = dealer_gdf[dealer_gdf['AREA'] == selected_kabupaten]

    for idx, dealer in dealers_in_kabupaten.iterrows():
        label_prefix = "Dealer" if dealer['CHANNEL'] == 'DEALER' else "Pos"
        marker_color = "red" if dealer['CHANNEL'] == 'DEALER' else "blue"
        folium.Marker(
            location=[dealer['LATITUDE'], dealer['LONGITUDE']],
            popup=f"{label_prefix}: {dealer['KODE']}<br>{dealer['NAMA CHANNEL']}",
            icon=folium.Icon(color=marker_color, icon='car')
        ).add_to(m)

    # Plot ring untuk dealer yang dipilih
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

        # Dealer marker khusus
        label_prefix = "Dealer" if dealer_selected['CHANNEL'] == 'DEALER' else "Pos"
        marker_color = "red" if dealer_selected['CHANNEL'] == 'DEALER' else "blue"
        folium.Marker(
            location=[dealer_selected['LATITUDE'], dealer_selected['LONGITUDE']],
            popup=f"{label_prefix}: {dealer_selected['KODE']}<br>{dealer_selected['NAMA CHANNEL']}",
            icon=folium.Icon(color=marker_color, icon='info-sign')
        ).add_to(m)

    # Tambahkan batas kecamatan + tooltip
    folium.GeoJson(
        jabar_map.__geo_interface__,
        name='Batas Kecamatan',
        style_function=lambda x: {
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['WADMKK', 'WADMKC'],
            aliases=['Kabupaten:', 'Kecamatan:'],
            sticky=False,
            style=(
                "background-color: white; "
                "color: black; "
                "font-family: Arial; "
                "font-size: 12px; "
                "padding: 5px;"
            )
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Tampilkan di Streamlit
    st_folium(m, width=900, height=600)
