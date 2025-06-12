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
    # Simplify polygon supaya lebih ringan
    gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.05, preserve_topology=True)
    return gdf

@st.cache_data
def load_excel(url):
    return pd.read_excel(url)

# Google Drive direct download links
geojson_url = 'https://drive.google.com/uc?id=1nMWyPZ1X5JY9nO4QSsT_N0b4i7wxzMTF'
excel_url = 'https://docs.google.com/spreadsheets/d/1f7aLwp7-NfmdUKcsu1cmVE54ltzF8WdS/export?format=xlsx'

# Load data
jabar_map = load_geojson(geojson_url)
dealer_df = load_excel(excel_url)

# Convert dealer dataframe jadi GeoDataFrame
geometry = [Point(xy) for xy in zip(dealer_df['Longitude'], dealer_df['Latitude'])]
dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=geometry, crs='EPSG:4326')

# --- SIDEBAR FILTER ---
st.sidebar.title('Filter Dealer')
dealer_options = dealer_gdf['Kode Dealer'].unique()
selected_dealers = st.sidebar.multiselect('Pilih Dealer:', dealer_options)

# --- PLOTTING MAP ---
if selected_dealers:
    first_dealer = dealer_gdf[dealer_gdf['Kode Dealer'] == selected_dealers[0]].iloc[0]
    m = folium.Map(location=[first_dealer['Latitude'], first_dealer['Longitude']], zoom_start=9)

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

    # Plot tiap dealer yang dipilih
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

        # Tambahkan marker dealer
        folium.Marker(
            location=[dealer_selected['Latitude'], dealer_selected['Longitude']],
            popup=f"Dealer: {dealer_selected['Kode Dealer']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

        # Hitung jarak dealer lain
        distances = []
        for idx, row in dealer_gdf.iterrows():
            if row['Kode Dealer'] != dealer_code:
                distance = dealer_selected.geometry.distance(row.geometry) * 111000  # Konversi degree ke meter
                distances.append({'Kode Dealer': row['Kode Dealer'], 'Jarak (m)': distance})

        distance_df = pd.DataFrame(distances)

        # Filter dealer dalam Ring 1 dan Ring 2
        ring1 = distance_df[distance_df['Jarak (m)'] <= 5000].sort_values('Jarak (m)')
        ring2 = distance_df[(distance_df['Jarak (m)'] > 5000) & (distance_df['Jarak (m)'] <= 10000)].sort_values('Jarak (m)')

        st.write(f'**Dealer: {dealer_code}**')

        st.write('Dealer dalam Ring 1 (<5km):')
        st.dataframe(ring1[['Kode Dealer', 'Jarak (m)']])

        st.write('Dealer dalam Ring 2 (<10km):')
        st.dataframe(ring2[['Kode Dealer', 'Jarak (m)']])

    folium.LayerControl().add_to(m)

    st_folium(m, width=800, height=600)

else:
    st.write("Silakan pilih minimal satu dealer di sidebar.")
