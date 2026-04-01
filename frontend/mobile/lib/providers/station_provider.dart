import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

/// Provider for managing station data and state
class StationProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  
  List<ChargingStation> _stations = [];
  List<RankedStation> _recommendations = [];
  ChargingStation? _selectedStation;
  bool _isLoading = false;
  String? _error;
  
  // Filter state
  String? _selectedConnectorType;
  double _maxDistance = 50.0;
  
  // User location (default: Bangalore)
  double _userLat = 12.9716;
  double _userLon = 77.5946;
  
  // Battery state
  double _batterySoc = 50.0;
  
  // Getters
  List<ChargingStation> get stations => _stations;
  List<RankedStation> get recommendations => _recommendations;
  ChargingStation? get selectedStation => _selectedStation;
  bool get isLoading => _isLoading;
  String? get error => _error;
  String? get selectedConnectorType => _selectedConnectorType;
  double get maxDistance => _maxDistance;
  double get userLat => _userLat;
  double get userLon => _userLon;
  double get batterySoc => _batterySoc;
  
  // Stats
  int get totalConnectors => 
      _stations.fold(0, (sum, s) => sum + s.connectors.length);
  int get availableConnectors =>
      _stations.fold(0, (sum, s) => sum + s.availableConnectors);
  
  /// Load all stations
  Future<void> loadStations() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      _stations = await _api.getStations(
        lat: _userLat,
        lon: _userLon,
        radiusKm: _maxDistance,
        connectorType: _selectedConnectorType,
      );
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  /// Load personalized recommendations
  Future<void> loadRecommendations() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      _recommendations = await _api.getRecommendations(
        lat: _userLat,
        lon: _userLon,
        batterySoc: _batterySoc,
        maxDistanceKm: _maxDistance,
        connectorType: _selectedConnectorType,
      );
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  /// Set user location
  void setUserLocation(double lat, double lon) {
    _userLat = lat;
    _userLon = lon;
    notifyListeners();
  }
  
  /// Set battery state of charge
  void setBatterySoc(double soc) {
    _batterySoc = soc;
    notifyListeners();
  }
  
  /// Set connector type filter
  void setConnectorType(String? type) {
    _selectedConnectorType = type;
    notifyListeners();
  }
  
  /// Set max distance filter
  void setMaxDistance(double distance) {
    _maxDistance = distance;
    notifyListeners();
  }
  
  /// Select a station for details view
  void selectStation(ChargingStation? station) {
    _selectedStation = station;
    notifyListeners();
  }
  
  @override
  void dispose() {
    _api.dispose();
    super.dispose();
  }
}
