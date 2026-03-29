import axios from 'axios';

// API configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface Location {
    latitude: number;
    longitude: number;
}

export interface Connector {
    id: string;
    connector_type: 'CCS2' | 'CHAdeMO' | 'Type2' | 'Type1';
    power_kw: number;
    status: 'available' | 'occupied' | 'faulted' | 'reserved';
}

export interface Pricing {
    base_rate: number;
    dynamic_multiplier: number;
    effective_rate: number;
}

export interface Station {
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
    station: Station;
    score: number;
    distance_km: number;
    estimated_wait_minutes: number;
}

export interface RecommendationRequest {
    user_location: Location;
    battery_soc?: number;
    connector_type?: string;
    max_distance_km?: number;
    preferences?: {
        distance_weight?: number;
        price_weight?: number;
        speed_weight?: number;
        availability_weight?: number;
    };
}

export interface RecommendationResponse {
    stations: RankedStation[];
    total_count: number;
    user_location: Location;
}

export interface DashboardOverview {
    timestamp: string;
    stations: { total: number; active: number; inactive: number };
    connectors: { total: number; available: number; in_use: number; utilization: number };
    sessions_24h: { total: number; completed: number; active: number };
    revenue_24h: number;
    energy_24h_kwh: number;
    avg_session_value: number;
}

export interface GridLoadData {
    timestamp: string;
    current_load: number;
    status: 'low' | 'normal' | 'high' | 'critical';
    recommendation: string;
    forecast: { hour: number; predicted_load: number; is_peak: boolean }[];
    optimal_charging_hours: number[];
}

export interface DynamicPricingResponse {
    timestamp: string;
    grid_status: string;
    pricing_strategy: string;
    stations: {
        station_id: string;
        station_name: string;
        base_rate: number;
        multiplier: number;
        effective_rate: number;
        reasoning: string;
    }[];
    avg_multiplier: number;
}

// API functions
export const stationsApi = {
    // Get all stations
    getAll: async (params?: {
        lat?: number;
        lon?: number;
        radius_km?: number;
        connector_type?: string;
        is_active?: boolean;
    }): Promise<Station[]> => {
        const response = await api.get('/stations', { params });
        return response.data;
    },

    // Get station by ID
    getById: async (id: string): Promise<Station> => {
        const response = await api.get(`/stations/${id}`);
        return response.data;
    },

    // Get recommendations
    getRecommendations: async (request: RecommendationRequest): Promise<RecommendationResponse> => {
        const response = await api.post('/stations/recommend', request);
        return response.data;
    },
};

// Dashboard API
export const dashboardApi = {
    // Get overview statistics
    getOverview: async (): Promise<DashboardOverview> => {
        const response = await api.get('/dashboard/overview');
        return response.data;
    },

    // Get stations status
    getStationsStatus: async () => {
        const response = await api.get('/dashboard/stations/status');
        return response.data;
    },

    // Get grid load data
    getGridLoad: async (): Promise<GridLoadData> => {
        const response = await api.get('/dashboard/grid/load');
        return response.data;
    },

    // Get pricing overview
    getPricingOverview: async () => {
        const response = await api.get('/dashboard/pricing/overview');
        return response.data;
    },

    // Get analytics trends
    getAnalyticsTrends: async (days: number = 7) => {
        const response = await api.get('/dashboard/analytics/trends', { params: { days } });
        return response.data;
    },

    // Get recent sessions
    getRecentSessions: async (limit: number = 10) => {
        const response = await api.get('/dashboard/sessions/recent', { params: { limit } });
        return response.data;
    },
};

// Pricing API
export const pricingApi = {
    // Get dynamic pricing
    getDynamicPricing: async (params: {
        occupancy: number;
        grid_load: number;
        hour: number;
        day: number;
    }): Promise<DynamicPricingResponse> => {
        const response = await api.post('/pricing/dynamic', {
            current_occupancy: params.occupancy,
            grid_load: params.grid_load,
            hour_of_day: params.hour,
            day_of_week: params.day,
        });
        return response.data;
    },

    // Get current strategy
    getCurrentStrategy: async () => {
        const response = await api.get('/pricing/strategy/current');
        return response.data;
    },

    // Get station pricing
    getStationPricing: async (stationId: string) => {
        const response = await api.get(`/pricing/station/${stationId}`);
        return response.data;
    },
};

// Reservations API
export const reservationsApi = {
    // Create reservation
    create: async (params: {
        station_id: string;
        user_email: string;
        user_name?: string;
        connector_type?: string;
    }) => {
        const response = await api.post('/reservations/', params);
        return response.data;
    },

    // Get reservation
    get: async (id: string) => {
        const response = await api.get(`/reservations/${id}`);
        return response.data;
    },

    // Cancel reservation
    cancel: async (id: string) => {
        const response = await api.delete(`/reservations/${id}`);
        return response.data;
    },

    // Start session
    startSession: async (reservationId: string) => {
        const response = await api.post('/sessions/start', { reservation_id: reservationId });
        return response.data;
    },

    // End session
    endSession: async (sessionId: string, energyKwh: number) => {
        const response = await api.post(`/sessions/${sessionId}/end`, { energy_delivered_kwh: energyKwh });
        return response.data;
    },
};

// Simulation API
export interface SimulationConfig {
    evs: number;
    stations: number;
    cpos: number;
    steps: number;
}

export interface SimulationResult {
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    config: SimulationConfig;
    results?: any;
    error?: string;
    created_at: string;
}

export const simulationApi = {
    // Start simulation
    run: async (config: SimulationConfig): Promise<{ id: string; status: string }> => {
        const response = await api.post('/simulation/run', config);
        return response.data;
    },

    // Get simulation status
    getStatus: async (id: string): Promise<SimulationResult> => {
        const response = await api.get(`/simulation/status/${id}`);
        return response.data;
    },

    // Get simulation history
    getHistory: async (): Promise<SimulationResult[]> => {
        const response = await api.get('/simulation/history');
        return response.data;
    },
};

// Demo API
export interface DemoResponse {
    demo_id: string;
    logs: string[];
}

export const demoApi = {
    // Run demo scenario
    run: async (demoId: string): Promise<DemoResponse> => {
        const response = await api.post(`/demo/run/${demoId}`);
        return response.data;
    },
};

export default api;

