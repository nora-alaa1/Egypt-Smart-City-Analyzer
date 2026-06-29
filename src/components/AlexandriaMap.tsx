"use client";

import { useEffect, useRef, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Navigation } from "lucide-react";

interface MapProps {
  rankings?: { area_id: number; area_name: string; suitability_score: number }[] | null;
}

interface DistrictMarker {
  id: number; name: string; lat: number; lng: number; score: number; label?: string;
}

// Simple 1-12 IDs (matching fallback model — consistent across frontend)
const DISTRICTS: DistrictMarker[] = [
  { id: 1,  name: "Smouha",      lat: 31.212, lng: 29.948, score: 92 },
  { id: 2,  name: "Sidi Gaber",  lat: 31.225, lng: 29.915, score: 85 },
  { id: 3,  name: "Stanley",     lat: 31.230, lng: 29.930, score: 72 },
  { id: 4,  name: "Louran",      lat: 31.218, lng: 29.940, score: 88 },
  { id: 5,  name: "Cleopatra",   lat: 31.208, lng: 29.920, score: 68 },
  { id: 6,  name: "Sports City", lat: 31.198, lng: 29.905, score: 95 },
  { id: 7,  name: "Rushdy",      lat: 31.236, lng: 29.918, score: 89 },
  { id: 8,  name: "Shatby",      lat: 31.215, lng: 29.928, score: 81 },
  { id: 9,  name: "Ibrahimia",   lat: 31.222, lng: 29.935, score: 78 },
  { id: 10, name: "Moharam Bek", lat: 31.190, lng: 29.910, score: 55 },
  { id: 11, name: "Kafr Abdu",   lat: 31.205, lng: 29.925, score: 65 },
  { id: 12, name: "El-Attarin",  lat: 31.195, lng: 29.895, score: 42 },
  { id: 13, name: "Abu Qir",     lat: 31.315, lng: 30.070, score: 48 },
  { id: 14, name: "Miami",       lat: 31.245, lng: 29.970, score: 62 },
  { id: 15, name: "Mansheya",    lat: 31.200, lng: 29.885, score: 45 },
  { id: 16, name: "Agami",       lat: 31.115, lng: 29.780, score: 58 },
];

function getScoreInfo(score: number) {
  if (score >= 80) return { color: "#22C55E", label: "Optimal" };
  if (score >= 60) return { color: "#86EFAC", label: "Good" };
  if (score >= 40) return { color: "#FDE047", label: "Fair" };
  return { color: "#EF4444", label: "Low" };
}

export default function AlexandriaMap({ rankings }: MapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const [mapReady, setMapReady] = useState(false);
  const LRef = useRef<any>(null);

  const districts = useMemo(() => {
    if (!rankings?.length) return DISTRICTS;
    const m = new Map(rankings.map(r => [r.area_id, r.suitability_score]));
    return DISTRICTS.map(d => ({
      ...d,
      score: m.has(d.id) ? Math.round(m.get(d.id)! * 10) : d.score,
    }));
  }, [rankings]);

  // Init map once
  useEffect(() => {
    if (typeof window === "undefined" || !mapRef.current || mapInstanceRef.current) return;

    (async () => {
      const L = (await import("leaflet")).default;
      LRef.current = L;

      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = L.map(mapRef.current!, {
        center: [31.205, 29.915],
        zoom: 12,
        zoomControl: false,
      });

      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
      }).addTo(map);

      mapInstanceRef.current = map;
      setMapReady(true);
    })();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update markers when districts data changes (or map becomes ready)
  useEffect(() => {
    const map = mapInstanceRef.current;
    const L = LRef.current;
    if (!map || !L) return;

    markersRef.current.forEach((m) => map.removeLayer(m));
    markersRef.current = [];

      districts.forEach((d) => {
        const info = getScoreInfo(d.score);
        const displayName = d.label || d.name;
        const marker = L.circleMarker([d.lat, d.lng], {
          radius: 12 + (d.score / 100) * 6,
          fillColor: info.color,
          color: "#ffffff",
          weight: 1.5,
          opacity: 0.6,
          fillOpacity: 0.35,
        }).addTo(map);

        marker.bindTooltip(
          `<div style="font-family:Inter,sans-serif;font-size:11px;padding:2px 0">
            <strong style="font-size:13px">${displayName}</strong><br/>
            Score: <span style="color:${info.color};font-weight:700">${d.score}/100</span><br/>
            <span style="color:#94A3B8">${info.label}</span>
          </div>`,
          { direction: "top", offset: [0, -8] }
        );

        const label = L.marker([d.lat, d.lng], {
          icon: L.divIcon({
            className: "",
            html: `<div style="
              color:#F8FAFC; font-size:9px; font-weight:600; text-align:center;
              text-shadow:0 1px 3px rgba(0,0,0,0.8); white-space:nowrap;
              font-family:'Space Grotesk',sans-serif; letter-spacing:0.3px;
              transform:translateY(12px);
            ">${displayName}</div>`,
            iconSize: [0, 0],
          }),
          interactive: false,
        }).addTo(map);

      markersRef.current.push(marker, label);
    });
  }, [districts, mapReady]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-5 overflow-hidden"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-heading text-lg font-semibold flex items-center gap-2">
          <MapPin className="w-4 h-4 text-accent-purple" />
          Alexandria — Real Map
        </h3>
        <div className="flex items-center gap-2 text-[10px] text-text-secondary">
          <Navigation size={12} />
          <span>OpenStreetMap</span>
        </div>
      </div>

      <div
        ref={mapRef}
        className="w-full rounded-lg overflow-hidden"
        style={{ height: 420, background: "#0A0F2C" }}
      />

      <div className="flex items-center flex-wrap justify-center gap-3 mt-2 text-[10px] text-text-secondary">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#22C55E]" /> Optimal (80+)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#86EFAC]" /> Good (60-79)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#FDE047]" /> Fair (40-59)</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#EF4444]" /> Low (&lt;40)</span>
      </div>
    </motion.div>
  );
}
