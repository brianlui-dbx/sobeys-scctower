import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface DcLocation {
  location_id: string;
  location_name: string;
  type: string;
  location: string;
  latitude: number;
  longitude: number;
}

interface CustomerLocation {
  customer_id: string;
  name: string;
  location: string;
  latitude: number;
  longitude: number;
}

interface NetworkMapProps {
  dcs: DcLocation[];
  customers: CustomerLocation[];
}

export default function NetworkMap({ dcs, customers }: NetworkMapProps) {
  // Fix leaflet default icon issue
  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const L = require("leaflet");
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: "",
      iconUrl: "",
      shadowUrl: "",
    });
  }, []);

  const centerLat =
    dcs.length > 0
      ? dcs.reduce((sum, d) => sum + d.latitude, 0) / dcs.length
      : 39.8;
  const centerLng =
    dcs.length > 0
      ? dcs.reduce((sum, d) => sum + d.longitude, 0) / dcs.length
      : -98.5;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Distribution Network Map</CardTitle>
        <p className="text-xs text-muted-foreground">
          <span className="inline-block w-3 h-3 rounded-full bg-green-600 mr-1 align-middle" />
          Distribution Centres ({dcs.length})
          <span className="inline-block w-3 h-3 rounded-full bg-blue-500 ml-3 mr-1 align-middle" />
          Customer Locations ({customers.length})
        </p>
      </CardHeader>
      <CardContent>
        <div className="h-96 rounded-lg overflow-hidden border">
          <MapContainer
            center={[centerLat, centerLng]}
            zoom={4}
            style={{ height: "100%", width: "100%" }}
            scrollWheelZoom={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {dcs.map((dc) => (
              <CircleMarker
                key={dc.location_id}
                center={[dc.latitude, dc.longitude]}
                radius={10}
                pathOptions={{
                  color: "#0E5A19",
                  fillColor: "#469E41",
                  fillOpacity: 0.9,
                  weight: 2,
                }}
              >
                <Tooltip>{dc.location_name}</Tooltip>
                <Popup>
                  <strong>{dc.location_name}</strong>
                  <br />
                  {dc.location}
                </Popup>
              </CircleMarker>
            ))}
            {customers.map((c) => (
              <CircleMarker
                key={c.customer_id}
                center={[c.latitude, c.longitude]}
                radius={6}
                pathOptions={{
                  color: "#2563eb",
                  fillColor: "#3b82f6",
                  fillOpacity: 0.7,
                  weight: 1,
                }}
              >
                <Tooltip>{c.name}</Tooltip>
                <Popup>
                  <strong>{c.name}</strong>
                  <br />
                  {c.location}
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      </CardContent>
    </Card>
  );
}
