import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/interaction.dart';

class FirebaseService extends ChangeNotifier {
  static const String _defaultUrlKey = 'firebase_db_url';
  String _databaseUrl = 'https://rollopod-default-rtdb.asia-southeast1.firebasedatabase.app';
  
  String robotState = 'idle';
  String voiceProfile = 'iron_crush';
  int voicePitchHz = -7;
  String operationalMode = 'hybrid';
  
  String activeQuestion = '';
  String lastReply = '';
  String replySource = '';
  int lastTimestamp = 0;
  
  // Local-only history stored on device (Zero Firebase RTDB network burden)
  final List<Interaction> localHistory = [];
  bool isConnected = false;
  
  Timer? _pollingTimer;

  String get databaseUrl => _databaseUrl;

  FirebaseService() {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedUrl = prefs.getString(_defaultUrlKey);
      if (savedUrl != null && savedUrl.isNotEmpty) {
        _databaseUrl = savedUrl;
      }
      final savedVoice = prefs.getString('saved_voice_profile');
      if (savedVoice != null && savedVoice.isNotEmpty) {
        voiceProfile = savedVoice;
      }
      final savedPitch = prefs.getInt('saved_voice_pitch');
      if (savedPitch != null) {
        voicePitchHz = savedPitch;
      }
    } catch (_) {}
    startListening();
  }

  Future<void> updateDatabaseUrl(String newUrl) async {
    _databaseUrl = newUrl.trim().replaceAll(RegExp(r'/+$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_defaultUrlKey, _databaseUrl);
    notifyListeners();
    startListening();
  }

  void startListening() {
    _pollingTimer?.cancel();
    // Low-overhead 1.2s single endpoint poll
    _pollingTimer = Timer.periodic(const Duration(milliseconds: 1200), (_) => _syncActiveQuestion());
    _syncActiveQuestion();
  }

  Future<void> _syncActiveQuestion() async {
    if (_databaseUrl.isEmpty) return;

    try {
      final res = await http.get(Uri.parse('$_databaseUrl/rollopod/interaction.json')).timeout(const Duration(seconds: 2));
      if (res.statusCode == 200 && res.body != 'null') {
        final Map<String, dynamic> data = jsonDecode(res.body);
        final String q = data['q'] ?? '';
        final String rep = data['reply'] ?? '';
        final String src = data['reply_source'] ?? '';
        final int ts = data['timestamp'] is int ? data['timestamp'] : 0;

        isConnected = true;

        // If new question arrived
        if (ts > lastTimestamp && q.isNotEmpty) {
          lastTimestamp = ts;
          activeQuestion = q;
          lastReply = rep;
          replySource = src;
          
          // Add to local history on device
          _addLocalHistory(q, rep, src, ts);
        } else if (ts == lastTimestamp && rep.isNotEmpty && rep != lastReply) {
          // Reply was populated
          lastReply = rep;
          replySource = src;
          if (localHistory.isNotEmpty) {
            localHistory.first = Interaction(
              id: 'local_$ts',
              question: activeQuestion,
              reply: rep,
              replySource: src,
              status: 'answered',
              timestamp: ts,
            );
          }
        }

        notifyListeners();
      } else {
        isConnected = true;
      }
    } catch (e) {
      isConnected = false;
      notifyListeners();
    }
  }

  void _addLocalHistory(String q, String reply, String source, int ts) {
    // Keep last 30 items locally in memory
    localHistory.insert(0, Interaction(
      id: 'local_$ts',
      question: q,
      reply: reply,
      replySource: source,
      status: reply.isNotEmpty ? 'answered' : 'waiting_for_reply',
      timestamp: ts,
    ));
    if (localHistory.length > 30) {
      localHistory.removeLast();
    }
  }

  /// Sends operator reply for the current question
  Future<bool> sendHumanReply(String replyText) async {
    if (_databaseUrl.isEmpty) return false;
    try {
      final payload = {
        'reply': replyText.trim(),
        'reply_source': 'human',
      };

      final res = await http.patch(
        Uri.parse('$_databaseUrl/rollopod/interaction.json'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      if (res.statusCode == 200) {
        lastReply = replyText.trim();
        replySource = 'human';
        if (localHistory.isNotEmpty) {
          localHistory.first = Interaction(
            id: 'local_$lastTimestamp',
            question: activeQuestion,
            reply: lastReply,
            replySource: 'human',
            status: 'answered',
            timestamp: lastTimestamp,
          );
        }
        notifyListeners();
        return true;
      }
    } catch (_) {}
    return false;
  }

  /// Commands Rollopod to speak directly (soundboard)
  Future<bool> sendDirectSpeech(String textToSpeak) async {
    if (_databaseUrl.isEmpty) return false;
    try {
      final payload = {
        'speak': textToSpeak.trim(),
        'timestamp': DateTime.now().millisecondsSinceEpoch,
      };

      final res = await http.put(
        Uri.parse('$_databaseUrl/rollopod/command.json'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      _addLocalHistory('(Direct Speech)', textToSpeak.trim(), 'human', DateTime.now().millisecondsSinceEpoch);
      notifyListeners();
      return res.statusCode == 200;
    } catch (_) {}
    return false;
  }

  /// Switches voice profile (mech_titan, iron_crush, cyber_sentinel, etc.)
  Future<void> setVoiceProfile(String newProfile) async {
    voiceProfile = newProfile;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('saved_voice_profile', newProfile);

      if (_databaseUrl.isNotEmpty) {
        await http.put(
          Uri.parse('$_databaseUrl/rollopod/command.json'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'voice_profile': newProfile,
            'timestamp': DateTime.now().millisecondsSinceEpoch,
          }),
        );
      }
    } catch (_) {}
  }

  /// Adjusts voice pitch live (-20Hz to +15Hz)
  Future<void> setVoicePitch(int pitchHz) async {
    voicePitchHz = pitchHz;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt('saved_voice_pitch', pitchHz);

      if (_databaseUrl.isNotEmpty) {
        final pitchStr = "${pitchHz >= 0 ? '+' : ''}${pitchHz}Hz";
        await http.put(
          Uri.parse('$_databaseUrl/rollopod/command.json'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'pitch': pitchStr,
            'timestamp': DateTime.now().millisecondsSinceEpoch,
          }),
        );
      }
    } catch (_) {}
  }

  Future<void> setMode(String newMode) async {
    operationalMode = newMode;
    notifyListeners();
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('saved_operational_mode', newMode);

      if (_databaseUrl.isNotEmpty) {
        await http.put(
          Uri.parse('$_databaseUrl/rollopod/command.json'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'mode': newMode,
            'timestamp': DateTime.now().millisecondsSinceEpoch,
          }),
        );
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    super.dispose();
  }
}
