import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/station_provider.dart';
import 'station_detail_screen.dart';

class RecommendationsScreen extends StatefulWidget {
  const RecommendationsScreen({super.key});

  @override
  State<RecommendationsScreen> createState() => _RecommendationsScreenState();
}

class _RecommendationsScreenState extends State<RecommendationsScreen> {
  @override
  void initState() {
    super.initState();
    // Load recommendations on init
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StationProvider>().loadRecommendations();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      appBar: AppBar(
        title: const Text('Smart Recommendations'),
        backgroundColor: const Color(0xFF111827),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            onPressed: () => _showPreferencesSheet(context),
          ),
        ],
      ),
      body: Consumer<StationProvider>(
        builder: (context, provider, child) {
          return Column(
            children: [
              // Preference summary bar
              _buildPreferenceSummary(provider),
              // Main content
              Expanded(
                child: _buildContent(provider),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPreferenceSummary(StationProvider provider) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: Color(0xFF111827),
        border: Border(
          bottom: BorderSide(color: Color(0xFF374151), width: 1),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.amber[400], size: 20),
              const SizedBox(width: 8),
              const Text(
                'AI-Powered Ranking',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Based on distance, price, speed, and availability',
            style: TextStyle(color: Colors.grey[400], fontSize: 12),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildInfoChip(
                Icons.battery_charging_full,
                '${provider.batterySoc.toInt()}%',
                const Color(0xFF10B981),
              ),
              const SizedBox(width: 8),
              _buildInfoChip(
                Icons.location_on,
                '${provider.maxDistance.toInt()} km',
                const Color(0xFF3B82F6),
              ),
              if (provider.selectedConnectorType != null) ...[
                const SizedBox(width: 8),
                _buildInfoChip(
                  Icons.power,
                  provider.selectedConnectorType!,
                  const Color(0xFF8B5CF6),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(StationProvider provider) {
    if (provider.isLoading && provider.recommendations.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Color(0xFF3B82F6)),
            SizedBox(height: 16),
            Text(
              'Finding best stations for you...',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      );
    }

    if (provider.error != null && provider.recommendations.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            Text(
              'Error loading recommendations',
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
              onPressed: () => provider.loadRecommendations(),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (provider.recommendations.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, color: Colors.grey[600], size: 64),
            const SizedBox(height: 16),
            Text(
              'No stations found nearby',
              style: TextStyle(color: Colors.grey[400], fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              'Try increasing the search radius',
              style: TextStyle(color: Colors.grey[600], fontSize: 14),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.loadRecommendations(),
      color: const Color(0xFF3B82F6),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: provider.recommendations.length,
        itemBuilder: (context, index) {
          return _buildRankedStationCard(
            provider.recommendations[index],
            index + 1,
          );
        },
      ),
    );
  }

  Widget _buildRankedStationCard(dynamic rankedStation, int rank) {
    final station = rankedStation.station;
    final score = rankedStation.score;
    final distance = rankedStation.distanceKm;

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
          child: Row(
            children: [
              // Rank badge
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  gradient: rank <= 3
                      ? LinearGradient(
                          colors: rank == 1
                              ? [const Color(0xFFFFD700), const Color(0xFFFFA500)]
                              : rank == 2
                                  ? [const Color(0xFFC0C0C0), const Color(0xFF808080)]
                                  : [const Color(0xFFCD7F32), const Color(0xFF8B4513)],
                        )
                      : null,
                  color: rank > 3 ? const Color(0xFF374151) : null,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    '#$rank',
                    style: TextStyle(
                      color: rank <= 3 ? Colors.white : Colors.grey[400],
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // Station info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      station.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Icon(Icons.location_on, size: 14, color: Colors.grey[500]),
                        const SizedBox(width: 4),
                        Text(
                          '${distance.toStringAsFixed(1)} km',
                          style: TextStyle(color: Colors.grey[400], fontSize: 12),
                        ),
                        const SizedBox(width: 12),
                        Icon(Icons.flash_on, size: 14, color: Colors.grey[500]),
                        const SizedBox(width: 4),
                        Text(
                          '${station.maxPower.toInt()} kW',
                          style: TextStyle(color: Colors.grey[400], fontSize: 12),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    // Score indicator
                    Row(
                      children: [
                        Expanded(
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: LinearProgressIndicator(
                              value: score,
                              backgroundColor: const Color(0xFF374151),
                              valueColor: AlwaysStoppedAnimation(
                                Color.lerp(
                                  const Color(0xFFEF4444),
                                  const Color(0xFF10B981),
                                  score,
                                )!,
                              ),
                              minHeight: 6,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '${(score * 100).toInt()}%',
                          style: TextStyle(
                            color: Colors.grey[400],
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              // Price
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '₹${station.pricing.effectiveRate.toStringAsFixed(1)}',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    '/kWh',
                    style: TextStyle(color: Colors.grey[500], fontSize: 11),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showPreferencesSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1F2937),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => _buildPreferencesSheet(),
    );
  }

  Widget _buildPreferencesSheet() {
    return Consumer<StationProvider>(
      builder: (context, provider, child) {
        return Padding(
          padding: EdgeInsets.only(
            left: 24,
            right: 24,
            top: 24,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Preferences',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 20),
              // Battery SoC
              Text(
                'Battery Level: ${provider.batterySoc.toInt()}%',
                style: const TextStyle(color: Colors.grey, fontSize: 14),
              ),
              Slider(
                value: provider.batterySoc,
                min: 5,
                max: 100,
                divisions: 19,
                activeColor: const Color(0xFF10B981),
                onChanged: (value) => provider.setBatterySoc(value),
              ),
              const SizedBox(height: 12),
              // Max distance
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
              const SizedBox(height: 12),
              // Connector type
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
                    label: Text(type ?? 'Any'),
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
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    provider.loadRecommendations();
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF3B82F6),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text('Update Recommendations'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
