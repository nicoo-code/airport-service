from typing import Any

from src.domain.models.airport import Airport


class PlotlyAdapter:
    """Adaptador de infraestructura que traduce modelos de dominio a la estructura requerida por Plotly JS Scattergeo."""

    def format_for_scattergeo(self, airports: list[Airport]) -> dict[str, Any]:
        lats = []
        lons = []
        texts = []
        hover_texts = []
        ids = []

        for a in airports:
            # Filtrar aeropuertos con coordenadas válidas de Colombia
            if a.latitude != 0.0 and a.longitude != 0.0:
                lats.append(a.latitude)
                lons.append(a.longitude)
                texts.append(f"{a.iata_code}")
                hover_texts.append(
                    f"<b>{a.name}</b><br>IATA: {a.iata_code}<br>Ciudad: {a.city} ({a.department})<br>Tipo: {a.type}"
                )
                ids.append(a.id)

        scattergeo_trace = {
            "type": "scattergeo",
            "mode": "markers+text",
            "text": texts,
            "textposition": "top center",
            "hoverinfo": "text",
            "hovertext": hover_texts,
            "lat": lats,
            "lon": lons,
            "ids": ids,
            "marker": {
                "size": 10,
                "color": "#0284c7",
                "symbol": "circle",
                "line": {"width": 1.5, "color": "#ffffff"},
            },
        }

        layout = {
            "title": {
                "text": "Red Nacional e Internacional de Aeropuertos de Colombia",
                "font": {"size": 18, "color": "#0f172a"},
            },
            "showlegend": False,
            "geo": {
                "scope": "south america",
                "resolution": 50,
                "showland": True,
                "landcolor": "#f1f5f9",
                "countrycolor": "#cbd5e1",
                "coastlinecolor": "#94a3b8",
                "showsubunits": True,
                "subunitcolor": "#e2e8f0",
                "center": {"lat": 4.5709, "lon": -74.2973},
                "projection": {"type": "mercator", "scale": 4.5},
            },
            "margin": {"l": 0, "r": 0, "t": 40, "b": 0},
            "autosize": True,
        }

        return {"data": [scattergeo_trace], "layout": layout, "count": len(ids)}
