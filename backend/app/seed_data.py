"""
Seed data for development and testing
Run: python -m app.seed_data
"""
from .database import SessionLocal, init_db
from .models import ChargingStation, Connector, ConnectorType, ConnectorStatus, User


def seed_stations():
    """Create sample charging stations"""
    
    stations_data = [
        {
            "name": "EcoCharge Downtown Hub",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "base_rate": 12.0,
            "connectors": [
                {"type": ConnectorType.CCS2, "power_kw": 150.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.CCS2, "power_kw": 150.0, "status": ConnectorStatus.OCCUPIED},
                {"type": ConnectorType.TYPE2, "power_kw": 22.0, "status": ConnectorStatus.AVAILABLE},
            ]
        },
        {
            "name": "GreenPower Mall Station",
            "latitude": 12.9352,
            "longitude": 77.6245,
            "base_rate": 10.5,
            "connectors": [
                {"type": ConnectorType.CCS2, "power_kw": 100.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.CHADEMO, "power_kw": 50.0, "status": ConnectorStatus.AVAILABLE},
            ]
        },
        {
            "name": "TechPark Fast Charger",
            "latitude": 12.9081,
            "longitude": 77.6476,
            "base_rate": 15.0,
            "dynamic_multiplier": 1.2,
            "connectors": [
                {"type": ConnectorType.CCS2, "power_kw": 350.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.CCS2, "power_kw": 350.0, "status": ConnectorStatus.RESERVED},
            ]
        },
        {
            "name": "Airport EV Station",
            "latitude": 13.1989,
            "longitude": 77.7068,
            "base_rate": 18.0,
            "connectors": [
                {"type": ConnectorType.CCS2, "power_kw": 150.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.CHADEMO, "power_kw": 100.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.TYPE2, "power_kw": 22.0, "status": ConnectorStatus.FAULTED},
            ]
        },
        {
            "name": "Central Station Charging Point",
            "latitude": 12.9779,
            "longitude": 77.5726,
            "base_rate": 11.0,
            "connectors": [
                {"type": ConnectorType.TYPE2, "power_kw": 22.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.TYPE2, "power_kw": 22.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.TYPE1, "power_kw": 7.4, "status": ConnectorStatus.AVAILABLE},
            ]
        },
        {
            "name": "Highway Rest Stop Alpha",
            "latitude": 13.0500,
            "longitude": 77.4500,
            "base_rate": 14.0,
            "connectors": [
                {"type": ConnectorType.CCS2, "power_kw": 250.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.CCS2, "power_kw": 250.0, "status": ConnectorStatus.OCCUPIED},
                {"type": ConnectorType.CHADEMO, "power_kw": 100.0, "status": ConnectorStatus.AVAILABLE},
            ]
        },
        {
            "name": "Residential Complex Charger",
            "latitude": 12.9200,
            "longitude": 77.5800,
            "base_rate": 8.0,
            "connectors": [
                {"type": ConnectorType.TYPE2, "power_kw": 11.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.TYPE2, "power_kw": 11.0, "status": ConnectorStatus.OCCUPIED},
            ]
        },
        {
            "name": "Corporate Park Station",
            "latitude": 12.9600,
            "longitude": 77.6400,
            "base_rate": 13.5,
            "dynamic_multiplier": 0.8,
            "connectors": [
                {"type": ConnectorType.CCS2, "power_kw": 120.0, "status": ConnectorStatus.AVAILABLE},
                {"type": ConnectorType.TYPE2, "power_kw": 22.0, "status": ConnectorStatus.AVAILABLE},
            ]
        },
    ]
    
    db = SessionLocal()
    try:
        # Clear existing data
        db.query(Connector).delete()
        db.query(ChargingStation).delete()
        
        for station_data in stations_data:
            connectors_data = station_data.pop("connectors")
            station = ChargingStation(**station_data)
            db.add(station)
            db.flush()  # Get station ID
            
            for conn_data in connectors_data:
                connector = Connector(
                    station_id=station.id,
                    connector_type=conn_data["type"],
                    power_kw=conn_data["power_kw"],
                    status=conn_data["status"]
                )
                db.add(connector)
        
        db.commit()
        print(f"[OK] Seeded {len(stations_data)} charging stations")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding data: {e}")
        raise
    finally:
        db.close()


def seed_users():
    """Create sample users"""
    users_data = [
        {"email": "driver1@example.com", "name": "John Driver"},
        {"email": "driver2@example.com", "name": "Jane EV"},
        {"email": "cpo@example.com", "name": "CPO Admin"},
    ]
    
    db = SessionLocal()
    try:
        db.query(User).delete()
        
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
        
        db.commit()
        print(f"[OK] Seeded {len(users_data)} users")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding users: {e}")
        raise
    finally:
        db.close()


def seed_sessions():
    """Create sample charging sessions"""
    from .models import ChargingSession, SessionStatus
    import random
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        stations = db.query(ChargingStation).all()
        
        if not users or not stations:
            print("[WARN] No users or stations found. Skipping sessions.")
            return
            
        for i in range(12):
            user = random.choice(users)
            station = random.choice(stations)
            connector = random.choice(station.connectors)
            
            # Create a mix of past and recent sessions
            created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))
            
            session = ChargingSession(
                user_id=user.id,
                station_id=station.id,
                connector_id=connector.id,
                start_time=created_at,
                end_time=created_at + timedelta(minutes=random.randint(30, 120)),
                energy_delivered_kwh=round(random.uniform(10, 60), 2),
                cost=round(random.uniform(200, 1500), 2),
                status=random.choice([SessionStatus.COMPLETED, SessionStatus.ACTIVE, SessionStatus.RESERVED]),
                created_at=created_at
            )
            db.add(session)
            
        db.commit()
        print(f"[OK] Seeded 12 sample charging sessions")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding sessions: {e}")
    finally:
        db.close()


def main():
    """Run all seed functions"""
    print("[*] Initializing database...")
    init_db()
    
    print("[*] Seeding charging stations...")
    seed_stations()
    
    print("[*] Seeding users...")
    seed_users()
    
    print("[*] Seeding sessions...")
    seed_sessions()
    
    print("[OK] Database seeding complete!")


if __name__ == "__main__":
    main()
