import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:curago_field_app/main.dart';

void main() {
  testWidgets('Medicine Onboarding screen displays correctly', (WidgetTester tester) async {
    // Build your medicine delivery app
    await tester.pumpWidget(MyApp());

    // Verify onboarding screen shows up (no counter texts exist)
    expect(find.text('0'), findsNothing);  // Counter doesn't exist
    expect(find.text('1'), findsNothing);  // Counter doesn't exist

    // Verify your actual onboarding content appears
    expect(find.text('Smart Medicine'), findsOneWidget);
    expect(find.text('Delivery Made Simple'), findsOneWidget);
    expect(find.text('live ambulance tracking'), findsOneWidget);
    expect(find.text('Get Started'), findsOneWidget);

    // Verify button exists
    expect(find.byType(GestureDetector), findsOneWidget);
    expect(find.byIcon(Icons.arrow_forward), findsOneWidget);
  });
}
