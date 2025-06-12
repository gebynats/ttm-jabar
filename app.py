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

# --- LINK DATA ---
geojson_url = 'https://drive.google.com/uc?id=1nMWyPZ1X5JY9nO4QSsT_N0b4i7wxzMTF'
excel_url = 'https://docs.google.com/spreadsheets/d/1f7aLwp7-NfmdUKcsu1cmVE54ltzF8WdS/export?format=csv'


# --- LOAD DATA ---
jabar_map = load_geojson(geojson_url)
dealer_df = load_excel(excel_url)

# --- CONVERT GEODATAFRAME ---
geometry = [Point(xy) for xy in zip(dealer_df['Longitude'], dealer_df['Latitude'])]
dealer_gdf = gpd.GeoDataFrame(dealer_df, geometry=geometry, crs='EPSG:4326')

# --- SIDEBAR FILTER ---
st.sidebar.title('Filter Dealer')

selected_channels = st.sidebar.multiselect('Pilih Channel:', dealer_gdf['Channel'].unique())
filtered_area = dealer_gdf[dealer_gdf['Channel'].isin(selected_channels)]['Area'].unique()
selected_areas = st.sidebar.multiselect('Pilih Area:', filtered_area)

filtered_dealers = dealer_gdf[
    (dealer_gdf['Channel'].isin(selected_channels)) &
    (dealer_gdf['Area'].isin(selected_areas))
]

selected_dealers = st.sidebar.multiselect('Pilih Dealer:', filtered_dealers['Kode Dealer'].unique())

# --- PLOTTING MAP ---
if not filtered_dealers.empty:
    first_point = filtered_dealers.iloc[0]
    m = folium.Map(location=[first_point['Latitude'], first_point['Longitude']], zoom_start=9)

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

    # Tampilkan semua titik sesuai filter
    for idx, row in filtered_dealers.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=f"{row['Kode Dealer']} - {row['Channel']} - {row['Area']}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    # Kalau dealer dipilih, tampilkan ring 1, 2, 3
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
    st.write("Silakan pilih minimal satu channel dan area untuk menampilkan data.")
