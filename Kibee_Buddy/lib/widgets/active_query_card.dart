import 'package:flutter/material.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';

class ActiveQueryCard extends StatefulWidget {
  final FirebaseService service;

  const ActiveQueryCard({super.key, required this.service});

  @override
  State<ActiveQueryCard> createState() => _ActiveQueryCardState();
}

class _ActiveQueryCardState extends State<ActiveQueryCard> {
  final TextEditingController _replyController = TextEditingController();
  bool _isSending = false;

  final List<String> _quickSuggestions = [
    "I am Rollopod, a hybrid walking and rolling hexapod robot.",
    "My 6 legs fold into 2 side rings for high-speed rolling.",
    "I'm showcased under the Senior Category for Robotics.",
    "I use distributed microcontrollers with high-torque servo motors.",
    "Watch my creator demonstrate my transformation live!"
  ];

  @override
  void dispose() {
    _replyController.dispose();
    super.dispose();
  }

  Future<void> _submitReply(String replyText) async {
    if (replyText.trim().isEmpty) return;
    setState(() => _isSending = true);
    
    final success = await widget.service.sendHumanReply(replyText);
    if (mounted) {
      setState(() => _isSending = false);
      if (success) {
        _replyController.clear();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Spoken by Rollopod'),
            backgroundColor: AppTheme.surfaceElevated,
            duration: Duration(seconds: 1),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final hasQuestion = widget.service.activeQuestion.isNotEmpty;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(
                  Icons.chat_bubble_outline,
                  color: AppTheme.pureWhite,
                  size: 16,
                ),
                const SizedBox(width: 8),
                const Text(
                  'LIVE CONVERSATION',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.1,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const Spacer(),
                if (hasQuestion && widget.service.lastReply.isEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.surfaceLight,
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(color: AppTheme.borderLight),
                    ),
                    child: const Text(
                      'PENDING',
                      style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppTheme.pureWhite, letterSpacing: 0.8),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.surfaceLight,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.border),
              ),
              child: Text(
                hasQuestion
                    ? '"${widget.service.activeQuestion}"'
                    : 'Listening for visitor questions...',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w400,
                  fontStyle: hasQuestion ? FontStyle.italic : FontStyle.normal,
                  color: hasQuestion ? AppTheme.textPrimary : AppTheme.textMuted,
                ),
              ),
            ),
            if (widget.service.lastReply.isNotEmpty) ...[
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Last Spoke: ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.textSecondary)),
                  Expanded(
                    child: Text(
                      widget.service.lastReply,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 12),
            const Text(
              'Quick Response Presets',
              style: TextStyle(fontSize: 11, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 6),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _quickSuggestions.map((suggestion) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 6.0),
                    child: ActionChip(
                      label: Text(
                        suggestion,
                        style: const TextStyle(fontSize: 11, color: AppTheme.textPrimary),
                      ),
                      backgroundColor: AppTheme.surfaceLight,
                      side: const BorderSide(color: AppTheme.border),
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                      onPressed: () => _submitReply(suggestion),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _replyController,
                    decoration: const InputDecoration(
                      hintText: 'Type custom response...',
                    ),
                    onSubmitted: _submitReply,
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _isSending ? null : () => _submitReply(_replyController.text),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.pureWhite,
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: _isSending
                      ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                      : const Row(
                          children: [
                            Icon(Icons.arrow_upward, size: 16),
                            SizedBox(width: 4),
                            Text('Send', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                          ],
                        ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
