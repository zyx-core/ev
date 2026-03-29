# Frontend - Mobile & Web Interfaces

## Overview
User interfaces for the IEVC-eco platform:
- **Mobile App (Flutter)**: For EV drivers
- **Web Dashboard (React)**: For CPOs and Grid Aggregators

## Mobile App (Flutter)
### Features
- Station discovery with map view
- Personalized recommendations
- Charging session management
- Privacy-preserving local ML

### Setup
```bash
cd frontend/mobile
flutter pub get
flutter run
```

## Web Dashboard (React)
### Features
- Real-time station monitoring
- Dynamic pricing controls
- Revenue analytics
- Grid load visualization

### Setup
```bash
cd frontend/web
npm install
npm start
```

## Tech Stack
- Flutter 3.16+
- React 18+
- Google Maps API / Mapbox
- Chart.js (analytics)
