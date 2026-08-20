import 'package:flutter/material.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends StatefulWidget {
  final FirebaseService service;

  const SettingsScreen({super.key, required this.service});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlController;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: widget.service.databaseUrl);
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  void _saveSettings() {
    widget.service.updateDatabaseUrl(_urlController.text);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Firebase Database URL updated'),
        backgroundColor: AppTheme.surfaceElevated,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Settings & Config',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 0.5),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'FIREBASE DATABASE URL',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.0, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 6),
            const Text(
              'Realtime Database endpoint for robot synchronization.',
              style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                hintText: 'https://your-project-default-rtdb.firebaseio.com',
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _saveSettings,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.pureWhite,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                child: const Text('Save URL', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
              ),
            ),
            const SizedBox(height: 20),
            const Divider(color: AppTheme.border),
            const SizedBox(height: 16),
            const Text(
              'ROBOT VOICE PROFILE',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.0, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 6),
            const Text(
              'Select neural voice model and timbre for speech output.',
              style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 12),
            _buildVoiceOption('kokoro_adam', 'Kokoro 82M Adam', 'Ultra-fast local neural robot voice (<100ms) - Default'),
            _buildVoiceOption('kokoro_michael', 'Kokoro 82M Michael', 'Deep, assertive, low-latency mech voice'),
            _buildVoiceOption('kokoro_george', 'Kokoro 82M George', 'Deep British resonant robotics voice'),
            _buildVoiceOption('kokoro_bella', 'Kokoro 82M Bella', 'Warm, expressive, high-speed neural AI voice'),
            _buildVoiceOption('iron_crush', 'Iron Core', 'Rugged, strong mechanical authority (Edge Neural)'),
            _buildVoiceOption('mech_titan', 'Mech Titan', 'Deep, powerful, cinematic transformer presence'),
            _buildVoiceOption('cyber_sentinel', 'Cyber Sentinel', 'Resonant, crisp, intelligent AI mech voice'),
            _buildVoiceOption('indo_titan', 'Indo Titan', 'Deep Indian English authoritative robotics voice'),
            const SizedBox(height: 16),
            const Divider(color: AppTheme.border),
            const SizedBox(height: 14),
            Row(
              children: [
                const Text(
                  'VOICE PITCH TUNING',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.0, color: AppTheme.textMuted),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppTheme.surfaceLight,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: AppTheme.borderLight),
                  ),
                  child: Text(
                    '${widget.service.voicePitchHz >= 0 ? '+' : ''}${widget.service.voicePitchHz} Hz',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.pureWhite),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Adjust vocal pitch frequency lower (for deep mech) or higher.',
              style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 10),
            SliderTheme(
              data: SliderTheme.of(context).copyWith(
                activeTrackColor: AppTheme.pureWhite,
                inactiveTrackColor: AppTheme.surfaceLight,
                thumbColor: AppTheme.pureWhite,
                overlayColor: AppTheme.pureWhite.withAlpha(30),
                valueIndicatorColor: AppTheme.surfaceElevated,
              ),
              child: Slider(
                value: widget.service.voicePitchHz.toDouble(),
                min: -20.0,
                max: 15.0,
                divisions: 35,
                label: '${widget.service.voicePitchHz >= 0 ? '+' : ''}${widget.service.voicePitchHz} Hz',
                onChanged: (val) {
                  widget.service.setVoicePitch(val.round());
                },
              ),
            ),
            const Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('-20 Hz (Deep)', style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                Text('0 Hz (Neutral)', style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                Text('+15 Hz (High)', style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                _buildPitchChip('Deep Mech (-10Hz)', -10),
                _buildPitchChip('Default (-7Hz)', -7),
                _buildPitchChip('Mid (-4Hz)', -4),
                _buildPitchChip('Neutral (0Hz)', 0),
                _buildPitchChip('Higher (+8Hz)', 8),
              ],
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () {
                widget.service.sendDirectSpeech("Voice pitch set to ${widget.service.voicePitchHz} hertz.");
              },
              style: OutlinedButton.styleFrom(
                foregroundColor: AppTheme.pureWhite,
                backgroundColor: AppTheme.surfaceLight,
                side: const BorderSide(color: AppTheme.border),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.volume_up_outlined, size: 16),
                  SizedBox(width: 6),
                  Text('Test Voice Pitch on Robot', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
            const SizedBox(height: 20),
            const Divider(color: AppTheme.border),
            const SizedBox(height: 16),
            const Text(
              'OPERATOR REFERENCE',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.0, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 10),
            _buildGuideItem(
              '1. Instant AI Mode (Default)',
              'Preknown documentation answers or Gemini Flash AI respond in sub-second time without waiting for human intervention.',
            ),
            _buildGuideItem(
              '2. Manual Mode (Wizard-of-Oz)',
              'Visitor questions are published to this app and wait up to 6.0s for you to type or tap a canned response.',
            ),
            _buildGuideItem(
              '3. Soundboard Overrides',
              'Trigger pitch explanations, greetings, and transformation announcements at any time from the home console.',
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildVoiceOption(String key, String title, String subtitle) {
    final isSelected = widget.service.voiceProfile == key;
    return InkWell(
      onTap: () {
        widget.service.setVoiceProfile(key);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Switched to $title voice'),
            backgroundColor: AppTheme.surfaceElevated,
            duration: const Duration(seconds: 1),
          ),
        );
      },
      borderRadius: BorderRadius.circular(8),
      child: Container(
        margin: const EdgeInsets.only(bottom: 6),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.pureWhite : AppTheme.surface,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? AppTheme.pureWhite : AppTheme.border,
          ),
        ),
        child: Row(
          children: [
            Icon(
              isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
              color: isSelected ? Colors.black : AppTheme.textMuted,
              size: 18,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                      color: isSelected ? Colors.black : AppTheme.textPrimary,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontSize: 10,
                      color: isSelected ? const Color(0xFF444444) : AppTheme.textMuted,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPitchChip(String label, int pitchHz) {
    final isSelected = widget.service.voicePitchHz == pitchHz;
    return ChoiceChip(
      label: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
          color: isSelected ? Colors.black : AppTheme.textPrimary,
        ),
      ),
      selected: isSelected,
      selectedColor: AppTheme.pureWhite,
      backgroundColor: AppTheme.surfaceLight,
      side: BorderSide(
        color: isSelected ? AppTheme.pureWhite : AppTheme.border,
      ),
      onSelected: (_) {
        widget.service.setVoicePitch(pitchHz);
      },
    );
  }

  Widget _buildGuideItem(String title, String body) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.pureWhite)),
          const SizedBox(height: 3),
          Text(body, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, height: 1.3)),
        ],
      ),
    );
  }
}
