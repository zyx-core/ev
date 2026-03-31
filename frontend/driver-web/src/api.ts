export const API_BASE = 'http://localhost:8000/api/v1';

export interface Location {
  latitude: number;
  longitude: number;
}

export interface Connector {
  id: string;
  connector_type: string;
  power_kw: number;
  status: 'available' | 'occupied' | 'reserved' | 'faulted' | 'unknown';
}

export interface Pricing {
  base_rate: number;
  dynamic_multiplier: number;
  effective_rate: number;
}

export interface ChargingStation {
  id: string;
  name: string;
  location: Location;
  operator_id: string;
  pricing: Pricing;
  connectors: Connector[];
  is_active: boolean;
  blockchain_address?: string;
}

export interface RankedStation {
  station: ChargingStation;
  score: number;
  distance_km: number;
  estimated_wait_minutes: number;
}

export const api = {
  async getStations(params?: { lat?: number; lon?: number; radius_km?: number; connector_type?: string }): Promise<ChargingStation[]> {
    const url = new URL(`${API_BASE}/stations/`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) url.searchParams.append(key, value.toString());
      });
    }
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to fetch stations');
    return res.json();
  },

  async getStation(id: string): Promise<ChargingStation> {
    const res = await fetch(`${API_BASE}/stations/${id}`);
    if (!res.ok) throw new Error('Station not found');
    return res.json();
  },

  async getRecommendations(params: {
    user_location: Location;
    battery_soc?: number;
    max_distance_km?: number;
    connector_type?: string;
    preferences?: { distance_weight: number; price_weight: number; speed_weight: number; availability_weight: number };
  }): Promise<RankedStation[]> {
    const res = await fetch(`${API_BASE}/pricing/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error('Failed to get recommendations');
    const data = await res.json();
    return data.stations;
  },

  async enableV2g(sessionId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/enable_v2g`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to enable V2G');
    return res.json();
  },

  async createReservation(params: { station_id: string; connector_type?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/reservations/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...params,
        user_email: 'driver@ievc.eco',
        user_name: 'Eco Driver'
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Reservation failed');
    }
    return res.json();
  }
};
