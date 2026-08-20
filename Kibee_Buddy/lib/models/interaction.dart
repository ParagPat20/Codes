class Interaction {
  final String id;
  final String question;
  final String reply;
  final String replySource; // 'human', 'gemini_flash', 'preknown_fact', 'pending'
  final String status; // 'waiting_for_reply', 'answered'
  final int timestamp;
  final int? answeredAt;

  Interaction({
    required this.id,
    required this.question,
    required this.reply,
    required this.replySource,
    required this.status,
    required this.timestamp,
    this.answeredAt,
  });

  factory Interaction.fromJson(Map<String, dynamic> json) {
    return Interaction(
      id: json['id'] ?? 'unknown',
      question: json['question'] ?? '',
      reply: json['reply'] ?? '',
      replySource: json['reply_source'] ?? 'pending',
      status: json['status'] ?? 'waiting_for_reply',
      timestamp: json['timestamp'] is int ? json['timestamp'] : DateTime.now().millisecondsSinceEpoch,
      answeredAt: json['answered_at'] is int ? json['answered_at'] : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'question': question,
      'reply': reply,
      'reply_source': replySource,
      'status': status,
      'timestamp': timestamp,
      'answered_at': answeredAt,
    };
  }
}
