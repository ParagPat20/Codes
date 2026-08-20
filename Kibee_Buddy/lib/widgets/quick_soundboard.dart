import 'package:flutter/material.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';

class QuickSoundboard extends StatefulWidget {
  final FirebaseService service;

  const QuickSoundboard({super.key, required this.service});

  @override
  State<QuickSoundboard> createState() => _QuickSoundboardState();
}

class _QuickSoundboardState extends State<QuickSoundboard> {
  final TextEditingController _customSpeakController = TextEditingController();

  final Map<String, List<Map<String, String>>> _categories = {
    'Project Overview': [
      {
        'title': 'Full Pitch',
        'text': 'Hi everyone! I am Rollopod, a transforming hexapod robot combining walking and rolling locomotion!'
      },
      {
        'title': 'Dual-Mode Locomotion',
        'text': 'I walk over rocky terrain with 6 articulated legs and roll smoothly on 2 side rings on flat floors!'
      },
      {
        'title': 'Why Rollopod?',
        'text': 'Wheels struggle with stairs and obstacles, while hexapods are slow on flat ground. Rollopod solves both!'
      },
      {
        'title': 'Senior Category',
        'text': 'I am competing under the Senior Category for Robotics and Aerial Robotics at the Tech Expo!'
      },
    ],
    'Tech & Specs': [
      {
        'title': 'Transformation',
        'text': 'Three legs on each side coordinate their servo joints to curve and lock into rolling rings!'
      },
      {
        'title': 'Actuators & Power',
        'text': 'I run on dedicated digital servo motors with isolated power buses and lithium battery packs.'
      },
      {
        'title': 'Payload Balance',
        'text': 'My central body stays suspended and stable between both wheels for uninterrupted scanning!'
      },
    ],
    'Greetings & Demos': [
      {
        'title': 'Welcome Judges',
        'text': 'Welcome esteemed judges and visitors! Thank you for stopping by the Rollopod project booth!'
      },
      {
        'title': 'Thank You',
        'text': 'Thank you so much! Please ask any technical questions or feel free to look at our CAD designs!'
      },
      {
        'title': 'Ready to Roll',
        'text': 'Transforming into rolling mode in three, two, one, let us roll!'
      },
    ]
  };

  void _triggerDirectSpeak(String text) {
    widget.service.sendDirectSpeech(text);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Spoken: "$text"'),
        backgroundColor: AppTheme.surfaceElevated,
        duration: const Duration(seconds: 1),
      ),
    );
  }

  @override
  void dispose() {
    _customSpeakController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.volume_up_outlined, color: AppTheme.pureWhite, size: 16),
                SizedBox(width: 8),
                Text(
                  'SOUNDBOARD & MANUAL OVERRIDE',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ..._categories.entries.map((category) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 10.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      category.key,
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textMuted,
                        letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: category.value.map((item) {
                        return OutlinedButton(
                          onPressed: () => _triggerDirectSpeak(item['text']!),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: AppTheme.pureWhite,
                            backgroundColor: AppTheme.surfaceLight,
                            side: const BorderSide(color: AppTheme.border),
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                          ),
                          child: Text(
                            item['title']!,
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 4),
            const Divider(color: AppTheme.border),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _customSpeakController,
                    decoration: const InputDecoration(
                      hintText: 'Make robot speak custom phrase...',
                    ),
                    onSubmitted: (text) {
                      if (text.trim().isNotEmpty) {
                        _triggerDirectSpeak(text.trim());
                        _customSpeakController.clear();
                      }
                    },
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: () {
                    final text = _customSpeakController.text.trim();
                    if (text.isNotEmpty) {
                      _triggerDirectSpeak(text);
                      _customSpeakController.clear();
                    }
                  },
                  style: IconButton.styleFrom(
                    backgroundColor: AppTheme.pureWhite,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  icon: const Icon(Icons.arrow_upward, size: 16),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
