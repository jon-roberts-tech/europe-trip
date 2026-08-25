import os
import math
from collections import defaultdict
from datetime import datetime
import folium
from folium.plugins import AntPath
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

# Setup directory paths
RAW_DIR = "assets/raw_photos"
THUMB_DIR = "assets/magnets/thumbs"
FULL_DIR = "assets/magnets/full"

os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(FULL_DIR, exist_ok=True)


def get_decimal_from_dms(dms, ref):
    """Convert Degrees, Minutes, Seconds to decimal format."""
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ["S", "W"]:
        decimal = -decimal
    return decimal


def extract_photo_metadata(img_path):
    """Extract GPS coordinates and original date/time from photo EXIF data."""
    lat, lon, photo_time = None, None, None
    try:
        image = Image.open(img_path)
        exif_data = image._getexif()
        if not exif_data:
            return None

        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                for key in value:
                    sub_tag = GPSTAGS.get(key, key)
                    gps_info[sub_tag] = value[key]
            elif tag_name == "DateTimeOriginal":
                try:
                    photo_time = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    pass

        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = get_decimal_from_dms(
                gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N")
            )
            lon = get_decimal_from_dms(
                gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E")
            )

        if not photo_time:
            photo_time = datetime.fromtimestamp(os.path.getmtime(img_path))

        if lat is not None and lon is not None:
            return {"lat": lat, "lon": lon, "time": photo_time}

    except Exception as e:
        print(f"Error reading metadata for {img_path}: {e}")

    return None


# -----------------------------------------------------------------------------
# 1. Initialize Base Map & 3 Simple Layer Groups (No Plugins Needed)
# -----------------------------------------------------------------------------
m = folium.Map(
    location=[48.8566, 2.3522],
    zoom_start=5,
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Street Map",
    control_scale=True,
)

magnets_group = folium.FeatureGroup(name="Fridge Magnets")
route_group = folium.FeatureGroup(name="Animated Route")
photos_group = folium.FeatureGroup(name="Trip Photos")

# -----------------------------------------------------------------------------
# 2. Add 29 Magnets to `magnets_group` (Double-Sized 72x72px Icons)
# -----------------------------------------------------------------------------
magnets_data = [
    {"filename": "Amsterdam.png", "title": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041},
    {"filename": "Barcelona.jpg", "title": "Barcelona", "country": "Spain", "lat": 41.3879, "lon": 2.1699},
    {"filename": "Berlin.png", "title": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050},
    {"filename": "Bled.jpg", "title": "Lake Bled", "country": "Slovenia", "lat": 46.3683, "lon": 14.1146},
    {"filename": "Bratislava.png", "title": "Bratislava", "country": "Slovakia", "lat": 48.1486, "lon": 17.1077},
    {"filename": "Brussels.png", "title": "Brussels", "country": "Belgium", "lat": 50.8503, "lon": 4.3517},
    {"filename": "Budapest.jpg", "title": "Budapest", "country": "Hungary", "lat": 47.4979, "lon": 19.0402},
    {"filename": "cd.jpg", "title": "Cote dAzur", "country": "France", "lat": 43.7102, "lon": 7.2620},
    {"filename": "Cologne.png", "title": "Cologne", "country": "Germany", "lat": 50.9375, "lon": 6.9603},
    {"filename": "Como Brunate.jpg", "title": "Como Brunate", "country": "Italy", "lat": 45.8173, "lon": 9.0970},
    {"filename": "Copenhagen.jpg", "title": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683},
    {"filename": "Dortmund.jpg", "title": "Dortmund", "country": "Germany", "lat": 51.5136, "lon": 7.4653},
    {"filename": "Florence.png", "title": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558},
    {"filename": "Geneva.jpg", "title": "Geneva", "country": "Switzerland", "lat": 46.2044, "lon": 6.1432},
    {"filename": "Hamburg.png", "title": "Hamburg", "country": "Germany", "lat": 53.5511, "lon": 9.9937},
    {"filename": "Krakov.png", "title": "Kraków", "country": "Poland", "lat": 50.0647, "lon": 19.9450},
    {"filename": "Luxembourg.jpg", "title": "Luxembourg", "country": "Luxembourg", "lat": 49.6116, "lon": 6.1319},
    {"filename": "Madrid.jpg", "title": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038},
    {"filename": "Milan.png", "title": "Milan", "country": "Italy", "lat": 45.4642, "lon": 9.1900},
    {"filename": "Napoli.jpg", "title": "Naples", "country": "Italy", "lat": 40.8518, "lon": 14.2681},
    {"filename": "Paris.jpg", "title": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522},
    {"filename": "Plitvice Croatia.jpg", "title": "Plitvice Lakes", "country": "Croatia", "lat": 44.8654, "lon": 15.6025},
    {"filename": "Prague.png", "title": "Prague", "country": "Czechia", "lat": 50.0755, "lon": 14.4378},
    {"filename": "Rome.png", "title": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964},
    {"filename": "Rotterdam.png", "title": "Rotterdam", "country": "Netherlands", "lat": 51.9244, "lon": 4.4777},
    {"filename": "The Hague.jpg", "title": "The Hague", "country": "Netherlands", "lat": 52.0705, "lon": 4.3007},
    {"filename": "Venice.jpg", "title": "Venice", "country": "Italy", "lat": 45.4408, "lon": 12.3155},
    {"filename": "Vienna.png", "title": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738},
    {"filename": "Zagreb.png", "title": "Zagreb", "country": "Croatia", "lat": 45.8150, "lon": 15.9819},
]

for mag in magnets_data:
    thumb_ref = f"assets/magnets/thumbs/{mag['filename']}"
    full_ref = f"assets/magnets/full/{mag['filename']}"
    caption = f"{mag['title']} ({mag['country']})"

    magnet_icon_html = f"""
    <div onclick="openLightbox('{full_ref}', '{caption}')" 
         style="
            width: 72px; 
            height: 72px; 
            border: 3px solid #D69E2E; 
            border-radius: 12px; 
            box-shadow: 0 6px 16px rgba(0,0,0,0.4); 
            background-color: white;
            background-image: url('{thumb_ref}'); 
            background-size: cover; 
            background-position: center; 
            cursor: pointer;
            transition: transform 0.2s ease;"
         onmouseover="this.style.transform='scale(1.2)';"
         onmouseout="this.style.transform='scale(1)';"
    ></div>
    """

    folium.Marker(
        location=[mag["lat"], mag["lon"]],
        icon=folium.DivIcon(
            html=magnet_icon_html, icon_size=(72, 72), icon_anchor=(36, 36)
        ),
        tooltip=f"Magnet: {mag['title']}",
    ).add_to(magnets_group)


# -----------------------------------------------------------------------------
# 3. Read, Process, and Mathematically Scatter EXIF Photos
# -----------------------------------------------------------------------------
raw_files = [
    f for f in os.listdir(RAW_DIR) if f.lower().endswith((".jpeg", ".jpg", ".png"))
]
print(f"Reading EXIF metadata for {len(raw_files)} photos...")

extracted_items = []
for filename in raw_files:
    raw_path = os.path.join(RAW_DIR, filename)
    meta = extract_photo_metadata(raw_path)
    if meta:
        meta["raw_path"] = raw_path
        meta["original_filename"] = filename
        extracted_items.append(meta)

extracted_items.sort(key=lambda x: x["time"])

# Correct final photo back to Paris
if extracted_items:
    extracted_items[-1]["lat"] = 48.8566
    extracted_items[-1]["lon"] = 2.3522

# ---- PYTHON SPIDERFY: Fanning out stacked photos ----
location_groups = defaultdict(list)
for item in extracted_items:
    # Group photos taken in roughly the exact same 10-meter spot
    loc_key = (round(item["lat"], 4), round(item["lon"], 4))
    location_groups[loc_key].append(item)

for loc_key, items_at_loc in location_groups.items():
    count = len(items_at_loc)
    if count > 1:
        # Calculate a tiny radius that expands slightly for larger groups of photos
        radius = 0.0002 + (0.00005 * count) 
        for i, item in enumerate(items_at_loc):
            # Arrange them in a perfect circle around the original GPS point
            angle = (2 * math.pi * i) / count
            item["lat"] += radius * math.cos(angle)
            item["lon"] += radius * math.sin(angle)

photo_data = []
route_points = []

for idx, item in enumerate(extracted_items, start=1):
    clean_name = f"photo_{idx:04d}.jpg"
    thumb_path = os.path.join(THUMB_DIR, clean_name)
    full_path = os.path.join(FULL_DIR, clean_name)

    route_points.append([item["lat"], item["lon"]])

    if not os.path.exists(full_path) or not os.path.exists(thumb_path):
        with Image.open(item["raw_path"]) as img:
            img.thumbnail((1600, 1600))
            img.save(full_path, "JPEG", quality=82, optimize=True)

            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) / 2
            top = (height - min_dim) / 2
            right = (width + min_dim) / 2
            bottom = (height + min_dim) / 2

            crop_img = img.crop((left, top, right, bottom))
            crop_img.thumbnail((100, 100))
            crop_img.save(thumb_path, "JPEG", quality=85)

    date_str = item["time"].strftime("%b %d, %Y - %H:%M")
    photo_data.append(
        {
            "filename": clean_name,
            "title": f"Photo #{idx}",
            "date": date_str,
            "lat": item["lat"],
            "lon": item["lon"],
        }
    )

# -----------------------------------------------------------------------------
# 4. Attach Route & Photos to their FeatureGroups
# -----------------------------------------------------------------------------
AntPath(
    locations=route_points,
    color="#FF6B35",
    pulse_color="#2D3748",
    weight=4,
    opacity=0.85,
    delay=800,
    dash_array=[10, 20],
    tooltip="Tommy's Travel Route",
).add_to(route_group)

for item in photo_data:
    thumb_ref = f"assets/magnets/thumbs/{item['filename']}"
    full_ref = f"assets/magnets/full/{item['filename']}"
    caption = f"{item['title']} ({item['date']})"

    # parentNode Z-Index added so hovered photos always pop completely to the front
    icon_html = f"""
    <div onclick="openLightbox('{full_ref}', '{caption}')" 
         style="
            width: 36px; 
            height: 36px; 
            border: 2px solid white; 
            border-radius: 6px; 
            box-shadow: 0 3px 6px rgba(0,0,0,0.3); 
            background-image: url('{thumb_ref}'); 
            background-size: cover; 
            background-position: center; 
            cursor: pointer;
            transition: transform 0.15s ease;"
         onmouseover="this.style.transform='scale(1.4)'; this.parentNode.style.zIndex=9999;"
         onmouseout="this.style.transform='scale(1)'; this.parentNode.style.zIndex='';"
    ></div>
    """

    folium.Marker(
        location=[item["lat"], item["lon"]],
        icon=folium.DivIcon(
            html=icon_html, icon_size=(36, 36), icon_anchor=(18, 18)
        ),
        tooltip=f"{item['title']} - {item['date']}",
    ).add_to(photos_group)

# Add all groups to the map
magnets_group.add_to(m)
route_group.add_to(m)
photos_group.add_to(m)

if route_points:
    m.fit_bounds(route_points, padding=(30, 30))


# -----------------------------------------------------------------------------
# 5. Rock-Solid Zoom Visibility Switcher (Direct Variable Injection)
# -----------------------------------------------------------------------------
zoom_script = f"""
<script>
// setTimeout guarantees the map and layers are fully loaded before attaching the zoom rule
setTimeout(function() {{
    var mapObj = {m.get_name()};
    var magnetLayer = {magnets_group.get_name()};
    var routeLayer = {route_group.get_name()};
    var photoLayer = {photos_group.get_name()};

    function updateVisibilityByZoom() {{
        if (!mapObj) return;
        var currentZoom = mapObj.getZoom();
        
        if (currentZoom <= 6) {{
            if (!mapObj.hasLayer(magnetLayer)) mapObj.addLayer(magnetLayer);
            if (mapObj.hasLayer(routeLayer)) mapObj.removeLayer(routeLayer);
            if (mapObj.hasLayer(photoLayer)) mapObj.removeLayer(photoLayer);
        }} else {{
            if (mapObj.hasLayer(magnetLayer)) mapObj.removeLayer(magnetLayer);
            if (!mapObj.hasLayer(routeLayer)) mapObj.addLayer(routeLayer);
            if (!mapObj.hasLayer(photoLayer)) mapObj.addLayer(photoLayer);
        }}
    }}

    if (mapObj) {{
        mapObj.on('zoomend', updateVisibilityByZoom);
        updateVisibilityByZoom(); // Run immediately on load
    }}
}}, 500);
</script>
"""
m.get_root().html.add_child(folium.Element(zoom_script))


# -----------------------------------------------------------------------------
# 6. Lightbox Modal UI
# -----------------------------------------------------------------------------
lightbox_html = """
<div id="lightbox-modal" style="
    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
    background-color: rgba(0, 0, 0, 0.88); z-index: 99999; justify-content: center; 
    align-items: center; flex-direction: column; backdrop-filter: blur(5px);
" onclick="closeLightbox()">
    <span style="position: absolute; top: 20px; right: 35px; color: white; font-size: 40px; cursor: pointer; font-family: sans-serif;">&times;</span>
    <img id="lightbox-img" src="" style="max-width: 90%; max-height: 80%; border: 3px solid white; border-radius: 6px; box-shadow: 0 8px 25px rgba(0,0,0,0.5);" />
    <div id="lightbox-caption" style="margin-top: 15px; color: white; font-size: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;"></div>
</div>
<script>
function openLightbox(imgUrl, caption) {
    document.getElementById('lightbox-img').src = imgUrl;
    document.getElementById('lightbox-caption').innerText = caption;
    document.getElementById('lightbox-modal').style.display = 'flex';
}
function closeLightbox() {
    document.getElementById('lightbox-modal').style.display = 'none';
}
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') { closeLightbox(); }
});
</script>
"""
m.get_root().html.add_child(folium.Element(lightbox_html))

m.save("magnets.html")
print("Saved map cleanly to magnets.html with mathematical spiderfy!")