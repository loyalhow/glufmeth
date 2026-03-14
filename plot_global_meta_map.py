import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

gcmeta_path = Path("c:/Users/loyal/Documents/trae_projects/Phosphorus-cycling-database/gcMeta_output/metainformation/merged_meta_information.tsv")
smag_xlsx_path = Path("c:/Users/loyal/Documents/trae_projects/Phosphorus-cycling-database/SMAG_output/Supplementary Data 1.xlsx")
output_path = Path("c:/Users/loyal/Documents/trae_projects/Phosphorus-cycling-database/gcMeta_output/metainformation/global_sample_locations_fancy.html")


def col_to_index(ref: str) -> int:
    letters = "".join(ch for ch in ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def read_xlsx_rows(xlsx_path: Path, sheet_index: int = 0):
    with ZipFile(xlsx_path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rel = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib.get("Id"): r.attrib.get("Target") for r in rel.findall(".//{*}Relationship")}
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in ss.findall(".//{*}si"):
                shared.append("".join((t.text or "") for t in si.findall(".//{*}t")))
        sheets = wb.findall(".//{*}sheets/{*}sheet")
        sh = sheets[sheet_index]
        rid = sh.attrib.get("{http://purl.oclc.org/ooxml/officeDocument/relationships}id") or sh.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = relmap[rid]
        ws_path = "xl/" + target if not target.startswith("xl/") else target
        ws = ET.fromstring(z.read(ws_path))
        rows = []
        for row in ws.findall(".//{*}sheetData/{*}row"):
            vals = []
            for c in row.findall("{*}c"):
                ref = c.attrib.get("r", "")
                ci = col_to_index(ref) if ref else len(vals)
                while len(vals) <= ci:
                    vals.append("")
                t = c.attrib.get("t")
                v = c.find("{*}v")
                if v is None:
                    vals[ci] = ""
                    continue
                raw = v.text or ""
                if t == "s" and raw.isdigit() and int(raw) < len(shared):
                    vals[ci] = shared[int(raw)]
                else:
                    vals[ci] = raw
            rows.append(vals)
        return rows


groups = {}
legend_groups = set()
gcmeta_valid_rows = 0
smag_valid_rows = 0
sample_points = []

with gcmeta_path.open("r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            lat = float(row.get("Latitude", ""))
            lon = float(row.get("Longitude", ""))
        except ValueError:
            continue
        gcmeta_valid_rows += 1
        sample_points.append({"lat": lat, "lon": lon, "source": "gcMeta"})
        cat = (row.get("Catalogue_name") or "Unknown").strip()
        group_label = f"gcMeta | {cat}"
        country = (row.get("Country") or "Unknown").strip()
        biosample = (row.get("Biosample") or "").strip()
        try:
            completeness = float(row.get("Completeness", "0") or 0)
        except ValueError:
            completeness = 0.0
        try:
            contamination = float(row.get("Contamination", "0") or 0)
        except ValueError:
            contamination = 0.0
        key = (lat, lon, group_label, country, "gcMeta")
        if key not in groups:
            groups[key] = {
                "lat": lat,
                "lon": lon,
                "group": group_label,
                "country": country,
                "source": "gcMeta",
                "count": 0,
                "biosamples": set(),
                "completeness_sum": 0.0,
                "contamination_sum": 0.0,
            }
        groups[key]["count"] += 1
        groups[key]["biosamples"].add(biosample)
        groups[key]["completeness_sum"] += completeness
        groups[key]["contamination_sum"] += contamination
        legend_groups.add(group_label)

smag_rows = read_xlsx_rows(smag_xlsx_path, sheet_index=0)
header_idx = None
for i, row in enumerate(smag_rows):
    keys = {v.strip() for v in row if str(v).strip()}
    if {"Sample", "Lat", "Lon"}.issubset(keys):
        header_idx = i
        break

if header_idx is not None:
    header = smag_rows[header_idx]
    col_map = {str(v).strip(): idx for idx, v in enumerate(header) if str(v).strip()}
    for row in smag_rows[header_idx + 1 :]:
        try:
            lat = float(row[col_map["Lat"]]) if col_map["Lat"] < len(row) else None
            lon = float(row[col_map["Lon"]]) if col_map["Lon"] < len(row) else None
        except ValueError:
            continue
        if lat is None or lon is None:
            continue
        smag_valid_rows += 1
        sample_points.append({"lat": lat, "lon": lon, "source": "SMAG"})
        ecosystem = row[col_map["Ecosystem"]].strip() if "Ecosystem" in col_map and col_map["Ecosystem"] < len(row) else "Unknown"
        nation = row[col_map["Nation"]].strip() if "Nation" in col_map and col_map["Nation"] < len(row) else "Unknown"
        sample = row[col_map["Sample"]].strip() if "Sample" in col_map and col_map["Sample"] < len(row) else ""
        group_label = f"SMAG | {ecosystem}"
        key = (lat, lon, group_label, nation, "SMAG")
        if key not in groups:
            groups[key] = {
                "lat": lat,
                "lon": lon,
                "group": group_label,
                "country": nation,
                "source": "SMAG",
                "count": 0,
                "biosamples": set(),
                "completeness_sum": 0.0,
                "contamination_sum": 0.0,
            }
        groups[key]["count"] += 1
        groups[key]["biosamples"].add(sample)
        legend_groups.add(group_label)

points = []
for item in groups.values():
    count = item["count"]
    points.append(
        {
            "lat": item["lat"],
            "lon": item["lon"],
            "group": item["group"],
            "country": item["country"],
            "source": item["source"],
            "count": count,
            "biosamples": len([b for b in item["biosamples"] if b]),
            "mean_completeness": round(item["completeness_sum"] / count, 2) if item["source"] == "gcMeta" else None,
            "mean_contamination": round(item["contamination_sum"] / count, 2) if item["source"] == "gcMeta" else None,
        }
    )

palette = [
    "#60a5fa",
    "#34d399",
    "#f59e0b",
    "#f472b6",
    "#a78bfa",
    "#2dd4bf",
    "#f87171",
    "#facc15",
    "#38bdf8",
    "#fb7185",
    "#22c55e",
    "#eab308",
    "#c084fc",
    "#ef4444",
    "#14b8a6",
]
legend_list = sorted(legend_groups)
color_map = {name: palette[i % len(palette)] for i, name in enumerate(legend_list)}

data_json = json.dumps(points, ensure_ascii=False)
colors_json = json.dumps(color_map, ensure_ascii=False)
sample_json = json.dumps(sample_points, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Global gcMeta + SMAG Sample Locations</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      height: 100%;
      background: radial-gradient(circle at top, #111827 0%, #020617 70%);
      font-family: Inter, Segoe UI, Arial, sans-serif;
      color: #e2e8f0;
    }}
    #map {{
      height: calc(100% - 86px);
      width: min(98vw, 1700px);
      margin: 0 auto 12px auto;
      border-radius: 18px;
      box-shadow: 0 10px 35px rgba(0, 0, 0, 0.45);
      border: 1px solid rgba(148, 163, 184, 0.22);
      overflow: hidden;
    }}
    .header {{
      width: min(98vw, 1700px);
      margin: 14px auto 10px auto;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 12px;
    }}
    .title {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 0.2px;
    }}
    .subtitle {{
      font-size: 13px;
      color: #94a3b8;
      margin-top: 4px;
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 12px;
      justify-content: flex-end;
      max-width: 62%;
    }}
    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #cbd5e1;
      background: rgba(15, 23, 42, 0.65);
      border: 1px solid rgba(148, 163, 184, 0.3);
      border-radius: 999px;
      padding: 4px 9px;
    }}
    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,0.7);
    }}
    .leaflet-popup-content-wrapper {{
      background: #0f172a;
      color: #e2e8f0;
      border: 1px solid #334155;
      border-radius: 10px;
    }}
    .leaflet-popup-tip {{
      background: #0f172a;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <div class="title">Global Distribution of gcMeta + SMAG Sampling Points</div>
      <div class="subtitle">Marker radius scales with record count at each location</div>
    </div>
    <div id="legend" class="legend"></div>
  </div>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
  <script>
    const points = {data_json};
    const samplePoints = {sample_json};
    const colorMap = {colors_json};

    const map = L.map('map', {{
      worldCopyJump: true,
      zoomControl: true,
      minZoom: 2
    }}).setView([20, 0], 2);

    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
      attribution: '&copy; OpenStreetMap &copy; CARTO'
    }}).addTo(map);

    const extentLayer = L.layerGroup();
    samplePoints.forEach(p => {{
      const m = L.circleMarker([p.lat, p.lon], {{
        radius: 1.8,
        color: 'rgba(156,163,175,0.45)',
        weight: 0.2,
        fillColor: 'rgba(156,163,175,0.5)',
        fillOpacity: 0.42
      }});
      extentLayer.addLayer(m);
    }});
    extentLayer.addTo(map);

    const clusters = L.markerClusterGroup({{
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      disableClusteringAtZoom: 6
    }});

    function markerRadius(count) {{
      const base = 4;
      return Math.min(base + Math.sqrt(count) * 2.0, 22);
    }}

    points.forEach(p => {{
      const color = colorMap[p.group] || '#60a5fa';
      const stroke = p.source === 'SMAG' ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.75)';
      const weight = p.source === 'SMAG' ? 1.4 : 1;
      const marker = L.circleMarker([p.lat, p.lon], {{
        radius: markerRadius(p.count),
        color: stroke,
        weight: weight,
        fillColor: color,
        fillOpacity: 0.84
      }});

      const qc = (p.mean_completeness === null || p.mean_completeness === undefined)
        ? ''
        : `<div><b>Mean completeness:</b> ${{p.mean_completeness}}%</div><div><b>Mean contamination:</b> ${{p.mean_contamination}}%</div>`;

      marker.bindPopup(
        `<div style="line-height:1.5;">
          <div style="font-weight:700;font-size:14px;margin-bottom:4px;">${{p.country}}</div>
          <div><b>Dataset:</b> ${{p.source}}</div>
          <div><b>Group:</b> ${{p.group}}</div>
          <div><b>Records:</b> ${{p.count}}</div>
          <div><b>Unique samples:</b> ${{p.biosamples}}</div>
          ${{qc}}
          <div><b>Lat/Lon:</b> ${{p.lat.toFixed(4)}}, ${{p.lon.toFixed(4)}}</div>
        </div>`
      );

      clusters.addLayer(marker);
    }});

    map.addLayer(clusters);

    const legend = document.getElementById('legend');
    Object.entries(colorMap).forEach(([name, color]) => {{
      const item = document.createElement('div');
      item.className = 'legend-item';
      item.innerHTML = `<span class="dot" style="background:${{color}}"></span><span>${{name}}</span>`;
      legend.appendChild(item);
    }});
  </script>
</body>
</html>
"""

output_path.write_text(html, encoding="utf-8")

print(f"Saved: {output_path}")
print(f"gcMeta rows with valid coordinates: {gcmeta_valid_rows}")
print(f"SMAG rows with valid coordinates: {smag_valid_rows}")
print(f"Total raw sampling points plotted: {len(sample_points)}")
print(f"Plotted aggregated points: {len(points)}")
