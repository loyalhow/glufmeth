import pandas as pd
import folium
from folium.plugins import MarkerCluster

# --- CONFIGURATION ---
input_file = "Agricultural_Soil_MAGs_with_GIS.csv"
output_html = "MAG_Interactive_Map.html"
# ---------------------

print("1. Loading MAG data...")
df = pd.read_csv(input_file)

# Ensure coordinates are numeric and drop missing values
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df_clean = df.dropna(subset=['Latitude', 'Longitude'])

print(f"Loaded {len(df_clean)} MAGs with valid locations.")

# 2. Initialize the Base Map
# We start with a global view (lat 20, lon 0) using a clean, minimalist style
print("2. Building the map...")
m = folium.Map(location=[20, 0], zoom_start=2, tiles='CartoDB positron')

# 3. Initialize the MarkerCluster Plugin
# This is the magic feature that groups overlapping points!
marker_cluster = MarkerCluster().add_to(m)

# 4. Add Every MAG to the Map
print("3. Generating markers and popups...")
for idx, row in df_clean.iterrows():
    
    # Clean up the taxonomy string so the popup isn't cluttered
    tax = str(row.get('GTDB_taxonomy', 'Unknown'))
    tax_parts = tax.split(';')
    # Get the last taxonomic rank (e.g., Species or Genus)
    short_tax = tax_parts[-1] if tax_parts else tax
    if short_tax == "s__" and len(tax_parts) > 1: 
        short_tax = tax_parts[-2]  # Fall back to Genus if Species is blank

    # Create the HTML for the popup that appears when you click a dot
    popup_html = f"""
    <div style="width:250px; font-family: Arial, sans-serif;">
        <h4 style="margin-bottom: 5px; color: #d35400;">MAG Information</h4>
        <b>ID:</b> {row['MAG']}<br>
        <b>Country:</b> {row.get('Country', 'N/A')}<br>
        <b>Completeness:</b> {row.get('Completeness', 'N/A')}%<br>
        <b>Taxonomy:</b> {short_tax}
    </div>
    """
    
    # Add the marker to the cluster
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="orange", icon="leaf") 
    ).add_to(marker_cluster)

# 5. Save the Map
m.save(output_html)
print(f"Success! Double-click '{output_html}' to explore your map in any web browser.")