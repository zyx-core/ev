import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'reservation_screen.dart';

class StationDetailScreen extends StatefulWidget {
  final ChargingStation station;

  const StationDetailScreen({super.key, required this.station});

  @override
  State<StationDetailScreen> createState() => _StationDetailScreenState();
}

class _StationDetailScreenState extends State<StationDetailScreen> {
  // V2G State
  bool _v2gEnabled = false;
  double _batterySoc = 75.0; // Assume 75% SoC by default
  bool _v2gLoading = false;

  // V2G earnings calculation constants
  static const double _batteryCapacityKwh = 60.0; // Average EV battery (kWh)
  static const double _v2gSellingPriceMultiplier = 1.2; // 20% above effective rate during peak

  double get _availableEnergyKwh {
    // Energy available to sell = charge above 20% reserve threshold
    final reservePercent = 20.0;
    return _batteryCapacityKwh * ((_batterySoc - reservePercent) / 100).clamp(0.0, 1.0);
  }

  double get _estimatedEarning {
    final sellRate = widget.station.pricing.effectiveRate * _v2gSellingPriceMultiplier;
    return _availableEnergyKwh * sellRate;
  }

  Future<void> _toggleV2G(bool value) async {
    setState(() {
      _v2gLoading = true;
    });

    // Simulate the API call delay
    await Future.delayed(const Duration(milliseconds: 600));

    setState(() {
      _v2gEnabled = value;
      _v2gLoading = false;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            value
                ? '⚡ V2G Mode Activated! You will sell ${_availableEnergyKwh.toStringAsFixed(1)} kWh back to the grid.'
                : '🔋 V2G Mode Deactivated. Standard charging mode resumed.',
          ),
          backgroundColor: value ? const Color(0xFF10B981) : const Color(0xFF374151),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      body: CustomScrollView(
        slivers: [
          // App bar with gradient
          SliverAppBar(
            expandedHeight: 200,
            pinned: true,
            backgroundColor: const Color(0xFF111827),
            foregroundColor: Colors.white,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                widget.station.name,
                style: const TextStyle(fontSize: 16),
              ),
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFF3B82F6), Color(0xFF8B5CF6)],
                  ),
                ),
                child: Center(
                  child: Icon(
                    Icons.ev_station,
                    size: 80,
                    color: Colors.white.withOpacity(0.3),
                  ),
                ),
              ),
            ),
          ),
          // Content
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildStatusCard(),
                  const SizedBox(height: 16),
                  _buildPricingCard(),
                  const SizedBox(height: 16),
                  // ⚡ V2G Panel
                  _buildV2GPanel(),
                  const SizedBox(height: 16),
                  _buildConnectorsSection(),
                  const SizedBox(height: 16),
                  _buildLocationSection(),
                  const SizedBox(height: 24),
                  _buildActionButtons(context),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─────────────────── V2G PANEL ───────────────────
  Widget _buildV2GPanel() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeInOut,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: _v2gEnabled
            ? const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF064E3B), Color(0xFF065F46)],
              )
            : null,
        color: _v2gEnabled ? null : const Color(0xFF1F2937),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: _v2gEnabled ? const Color(0xFF10B981) : const Color(0xFF374151),
          width: _v2gEnabled ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: (_v2gEnabled
                      ? const Color(0xFF10B981)
                      : const Color(0xFF6B7280))
                      .withOpacity(0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  Icons.electric_bolt,
                  color: _v2gEnabled ? const Color(0xFF10B981) : Colors.grey,
                  size: 24,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Vehicle-to-Grid (V2G)',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Sell excess battery to the grid & earn tokens',
                      style: TextStyle(
                        color: Colors.grey[400],
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              // Toggle
              _v2gLoading
                  ? const SizedBox(
                      width: 40,
                      height: 24,
                      child: Center(
                        child: SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Color(0xFF10B981),
                          ),
                        ),
                      ),
                    )
                  : Switch(
                      value: _v2gEnabled,
                      onChanged: _toggleV2G,
                      activeColor: const Color(0xFF10B981),
                      activeTrackColor: const Color(0xFF10B981).withOpacity(0.3),
                    ),
            ],
          ),

          if (_v2gEnabled) ...[
            const SizedBox(height: 20),
            const Divider(color: Color(0xFF10B981), height: 1, thickness: 0.5),
            const SizedBox(height: 16),

            // ── Battery SoC Slider ──
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'My Battery Level',
                  style: TextStyle(color: Colors.grey[300], fontSize: 13),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF10B981).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${_batterySoc.toInt()}%',
                    style: const TextStyle(
                      color: Color(0xFF10B981),
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            SliderTheme(
              data: SliderTheme.of(context).copyWith(
                activeTrackColor: const Color(0xFF10B981),
                inactiveTrackColor: const Color(0xFF1F2937),
                thumbColor: const Color(0xFF10B981),
                overlayColor: const Color(0xFF10B981).withOpacity(0.2),
                trackHeight: 6,
              ),
              child: Slider(
                value: _batterySoc,
                min: 20.0,
                max: 100.0,
                divisions: 80,
                onChanged: (v) => setState(() => _batterySoc = v),
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('20% (min reserve)', style: TextStyle(color: Colors.grey[600], fontSize: 10)),
                Text('100%', style: TextStyle(color: Colors.grey[600], fontSize: 10)),
              ],
            ),

            const SizedBox(height: 20),

            // ── Earnings Calculator ──
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.25),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  _buildEarningsRow(
                    label: 'Available Energy',
                    value: '${_availableEnergyKwh.toStringAsFixed(1)} kWh',
                    icon: Icons.battery_charging_full,
                  ),
                  const SizedBox(height: 10),
                  _buildEarningsRow(
                    label: 'Grid Sell Rate',
                    value: '₹${(widget.station.pricing.effectiveRate * _v2gSellingPriceMultiplier).toStringAsFixed(2)}/kWh',
                    icon: Icons.price_change,
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 10),
                    child: Divider(color: Color(0xFF374151), height: 1),
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Estimated Earning',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      Text(
                        '₹${_estimatedEarning.toStringAsFixed(2)}',
                        style: const TextStyle(
                          color: Color(0xFF10B981),
                          fontWeight: FontWeight.bold,
                          fontSize: 20,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 14),

            // Confirm button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(
                        'V2G session confirmed! Selling ${_availableEnergyKwh.toStringAsFixed(1)} kWh → Earning ₹${_estimatedEarning.toStringAsFixed(2)}',
                      ),
                      backgroundColor: const Color(0xFF10B981),
                      behavior: SnackBarBehavior.floating,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  );
                },
                icon: const Icon(Icons.send_to_mobile, size: 18),
                label: const Text('Confirm V2G Session'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF10B981),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ] else ...[
            const SizedBox(height: 12),
            Text(
              'Enable V2G to sell your excess battery energy back to the grid during peak demand and earn Energy Tokens.',
              style: TextStyle(color: Colors.grey[500], fontSize: 12, height: 1.4),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildEarningsRow({
    required String label,
    required String value,
    required IconData icon,
  }) {
    return Row(
      children: [
        Icon(icon, color: Colors.grey[400], size: 16),
        const SizedBox(width: 8),
        Expanded(
          child: Text(label, style: TextStyle(color: Colors.grey[400], fontSize: 13)),
        ),
        Text(
          value,
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ],
    );
  }

  // ─────────────────── EXISTING CARDS (unchanged) ───────────────────

  Widget _buildStatusCard() {
    final available = widget.station.availableConnectors;
    final total = widget.station.connectors.length;
    final hasAvailable = available > 0;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1F2937),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: (hasAvailable ? const Color(0xFF10B981) : const Color(0xFFF59E0B))
                  .withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              hasAvailable ? Icons.check_circle : Icons.schedule,
              color: hasAvailable ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
              size: 28,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  hasAvailable ? 'Available Now' : 'Currently Busy',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '$available of $total connectors available',
                  style: TextStyle(color: Colors.grey[400], fontSize: 14),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPricingCard() {
    final multiplier = widget.station.pricing.dynamicMultiplier;
    final isDiscounted = multiplier < 1;
    final isPremium = multiplier > 1;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1F2937),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Pricing',
            style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '₹${widget.station.pricing.effectiveRate.toStringAsFixed(2)}',
                    style: const TextStyle(
                      color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text('per kWh', style: TextStyle(color: Colors.grey[400], fontSize: 14)),
                ],
              ),
              if (isDiscounted || isPremium)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: (isDiscounted ? const Color(0xFF10B981) : const Color(0xFFEF4444))
                        .withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        isDiscounted ? Icons.arrow_downward : Icons.arrow_upward,
                        size: 16,
                        color:
                            isDiscounted ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${(multiplier * 100 - 100).abs().toStringAsFixed(0)}%',
                        style: TextStyle(
                          color:
                              isDiscounted ? const Color(0xFF10B981) : const Color(0xFFEF4444),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Base rate: ₹${widget.station.pricing.baseRate.toStringAsFixed(2)}/kWh',
            style: TextStyle(color: Colors.grey[500], fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildConnectorsSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1F2937),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Connectors',
            style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          ...widget.station.connectors.map((connector) => _buildConnectorRow(connector)),
        ],
      ),
    );
  }

  Widget _buildConnectorRow(Connector connector) {
    final isAvailable = connector.isAvailable;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 4,
            height: 40,
            decoration: BoxDecoration(
              color: _getConnectorColor(connector.connectorType),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(connector.connectorType,
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                Text('${connector.powerKw.toInt()} kW',
                    style: TextStyle(color: Colors.grey[400], fontSize: 12)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: (isAvailable ? const Color(0xFF10B981) : const Color(0xFFF59E0B))
                  .withOpacity(0.15),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isAvailable ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  connector.status.toUpperCase(),
                  style: TextStyle(
                    color: isAvailable ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLocationSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1F2937),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Location',
            style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(Icons.location_on, color: Colors.grey[400], size: 20),
              const SizedBox(width: 8),
              Text(
                '${widget.station.location.latitude.toStringAsFixed(6)}, ${widget.station.location.longitude.toStringAsFixed(6)}',
                style: TextStyle(color: Colors.grey[300], fontSize: 14),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: widget.station.availableConnectors > 0
                ? () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ReservationScreen(station: widget.station),
                      ),
                    );
                  }
                : null,
            icon: const Icon(Icons.calendar_today),
            label: const Text('Reserve Slot'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF3B82F6),
              disabledBackgroundColor: Colors.grey[700],
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Navigation feature coming soon!')),
              );
            },
            icon: const Icon(Icons.directions),
            label: const Text('Get Directions'),
            style: OutlinedButton.styleFrom(
              foregroundColor: const Color(0xFF3B82F6),
              side: const BorderSide(color: Color(0xFF3B82F6)),
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
      ],
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
}
