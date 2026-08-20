import 'package:flutter/material.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';

class StatusBanner extends StatelessWidget {
  final FirebaseService service;

  const StatusBanner({super.key, required this.service});

  IconData _getStatusIcon(String state) {
    switch (state.toLowerCase()) {
      case 'listening':
        return Icons.hearing_outlined;
      case 'thinking':
        return Icons.bubble_chart_outlined;
      case 'speaking':
        return Icons.volume_up_outlined;
      case 'idle':
        return Icons.radio_button_checked;
      default:
        return Icons.cloud_off_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceLight,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.borderLight),
                ),
                child: Icon(
                  _getStatusIcon(service.robotState),
                  color: AppTheme.pureWhite,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Text(
                          'SYSTEM STATUS',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 1.1,
                            color: AppTheme.textMuted,
                          ),
                        ),
                        const Spacer(),
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: service.isConnected ? AppTheme.pureWhite : AppTheme.textMuted,
                          ),
                        ),
                        const SizedBox(width: 5),
                        Text(
                          service.isConnected ? 'ONLINE' : 'DISCONNECTED',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 0.8,
                            color: service.isConnected ? AppTheme.pureWhite : AppTheme.textMuted,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      service.robotState.toUpperCase(),
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.pureWhite,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Divider(color: AppTheme.border, height: 1),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Mode',
                style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
              ),
              Row(
                children: [
                  _buildModeChip('ai', 'AI (Instant)', service),
                  const SizedBox(width: 6),
                  _buildModeChip('hybrid', 'Hybrid', service),
                  const SizedBox(width: 6),
                  _buildModeChip('manual', 'Manual', service),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildModeChip(String modeKey, String label, FirebaseService service) {
    final isSelected = service.operationalMode == modeKey;
    return InkWell(
      onTap: () => service.setMode(modeKey),
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.pureWhite : AppTheme.surfaceLight,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: isSelected ? AppTheme.pureWhite : AppTheme.border,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            color: isSelected ? Colors.black : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }
}
