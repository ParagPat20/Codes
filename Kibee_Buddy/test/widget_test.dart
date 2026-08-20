import 'package:flutter_test/flutter_test.dart';
import 'package:kibee_buddy/main.dart';
import 'package:kibee_buddy/services/firebase_service.dart';

void main() {
  testWidgets('Kibee Buddy app smoke test', (WidgetTester tester) async {
    final service = FirebaseService();
    await tester.pumpWidget(KibeeBuddyApp(firebaseService: service));
    expect(find.text('KIBEE BUDDY'), findsOneWidget);
  });
}
