import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'services/firebase_service.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final firebaseService = FirebaseService();
  runApp(KibeeBuddyApp(firebaseService: firebaseService));
}

class KibeeBuddyApp extends StatelessWidget {
  final FirebaseService firebaseService;

  const KibeeBuddyApp({super.key, required this.firebaseService});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kibee Buddy',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: HomeScreen(service: firebaseService),
    );
  }
}
