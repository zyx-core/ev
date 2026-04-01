import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/station_provider.dart';
import '../services/api_service.dart';
import 'station_detail_screen.dart';
import 'recommendations_screen.dart';

class StationListScreen extends StatefulWidget {
  const StationListScreen({super.key});

  @override
  State<StationListScreen> createState() => _StationListScreenState();
}

class _StationListScreenState extends State<StationListScreen> {
  @override
  void initState() {
    super.initState();
    // Load stations on init
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StationProvider>().loadStations();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      appBar: AppBar(
        title: const Text('Charging Stations'),
        backgroundColor: const Color(0xFF111827),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () => _showFilterSheet(context),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<StationProvider>().loadStations(),
          ),
        ],
      ),
      body: Consumer<StationProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.stations.isEmpty) {
            return const Center(
              child: CircularProgressIndicator(color: Color(0xFF3B82F6)),
            );
          }

          if (provider.error != null && provider.stations.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, color: Colors.red, size: 48),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading stations',
                    style: TextStyle(color: Colors.grey[400], fontSize: 16),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    provider.error!,
                    style: TextStyle(color: Colors.grey[600], fontSize: 12),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.loadStations(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (provider.stations.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.ev_station, color: Colors.grey[600], size: 64),
                  const SizedBox(height: 16),
                  Text(
                    'No stations found',
                    style: TextStyle(color: Colors.grey[400], fontSize: 16),
                  ),
                ],
              ),
            );
          }

          return Column(
            children: [
              // Stats bar
              _buildStatsBar(provider),
              // Station list
              Expanded(
                child: RefreshIndicator(
                  onRefresh: () => provider.loadStations(),
                  color: const Color(0xFF3B82F6),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: provider.stations.length,
                    itemBuilder: (context, index) {
                      return _buildStationCard(provider.stations[index]);
                    },
                  ),
                ),
              ),
            ],
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const RecommendationsScreen(),
            ),
          );
        },
        backgroundColor: const Color(0xFF3B82F6),
        icon: const Icon(Icons.auto_awesome),
        label: const Text('Get Recommendations'),
      ),
    );
  }

  Widget _buildStatsBar(StationProvider provider) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: const Color(0xFF111827),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatItem(
            '${provider.stations.length}',
            'Stations',
            Icons.ev_station,
            const Color(0xFF3B82F6),
          ),
          _buildStatItem(
            '${provider.availableConnectors}',
            'Available',
            Icons.check_circle,
            const Color(0xFF10B981),
          ),
          _buildStatItem(
            '${provider.totalConnectors - provider.availableConnectors}',
            'In Use',
            Icons.flash_on,
            const Color(0xFFF59E0B),
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String value, String label, IconData icon, Color color) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.15),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(color: Colors.grey[400], fontSize: 12),
        ),
      ],
    );
  }

  Widget _buildStationCard(ChargingStation station) {
    final available = station.availableConnectors;
    final total = station.connectors.length;
    final hasAvailable = available > 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: const Color(0xFF1F2937),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => StationDetailScreen(station: station),
            ),
          );
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF3B82F6), Color(0xFF8B5CF6)],
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.ev_station, color: Colors.white),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          station.name,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: hasAvailable
                                    ? const Color(0xFF10B981)
                                    : const Color(0xFFF59E0B),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              '$available/$total available',
                              style: TextStyle(
                                color: hasAvailable
                                    ? const Color(0xFF10B981)
                                    : const Color(0xFFF59E0B),
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '₹${station.pricing.effectiveRate.toStringAsFixed(1)}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        '/kWh',
                        style: TextStyle(color: Colors.grey[400], fontSize: 12),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Connector chips
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: station.connectorTypes.map((type) {
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF111827),
                      borderRadius: BorderRadius.circular(6),
                      border: Border(
                        left: BorderSide(
                          width: 3,
                          color: _getConnectorColor(type),
                        ),
                      ),
                    ),
                    child: Text(
                      type,
                      style: TextStyle(color: Colors.grey[300], fontSize: 12),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.flash_on, color: Colors.grey[500], size: 16),
                  const SizedBox(width: 4),
                  Text(
                    '${station.maxPower.toInt()} kW max',
                    style: TextStyle(color: Colors.grey[400], fontSize: 12),
                  ),
                  const Spacer(),
                  Icon(Icons.location_on, color: Colors.grey[500], size: 16),
                  const SizedBox(width: 4),
                  Text(
                    '${station.location.latitude.toStringAsFixed(3)}, ${station.location.longitude.toStringAsFixed(3)}',
                    style: TextStyle(color: Colors.grey[400], fontSize: 12),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getConnectorColor(String type) {
    switch (type) {
      case 'CCS2':
        return const Color(0xFF3B82F6);
      case 'CHAdeMO':
        return const Color(0xFF8B5CF6);
      case 'Type2':
        return const Color(0xFF10B981);
      case 'Type1':
        return const Color(0xFFF59E0B);
      default:
        return Colors.grey;
    }
  }

  void _showFilterSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1F2937),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _buildFilterSheet(),
    );
  }

  Widget _buildFilterSheet() {
    return Consumer<StationProvider>(
      builder: (context, provider, child) {
        return Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Filter Stations',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                'Connector Type',
                style: TextStyle(color: Colors.grey, fontSize: 14),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [null, 'CCS2', 'CHAdeMO', 'Type2', 'Type1'].map((type) {
                  final isSelected = provider.selectedConnectorType == type;
                  return ChoiceChip(
                    label: Text(type ?? 'All'),
                    selected: isSelected,
                    onSelected: (selected) {
                      provider.setConnectorType(selected ? type : null);
                    },
                    selectedColor: const Color(0xFF3B82F6),
                    backgroundColor: const Color(0xFF111827),
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.white : Colors.grey[400],
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),
              Text(
                'Max Distance: ${provider.maxDistance.toInt()} km',
                style: const TextStyle(color: Colors.grey, fontSize: 14),
              ),
              Slider(
                value: provider.maxDistance,
                min: 5,
                max: 100,
                divisions: 19,
                activeColor: const Color(0xFF3B82F6),
                onChanged: (value) => provider.setMaxDistance(value),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    provider.loadStations();
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF3B82F6),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text('Apply Filters'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
