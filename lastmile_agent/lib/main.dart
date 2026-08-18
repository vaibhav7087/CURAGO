import 'package:flutter/material.dart';
import 'package:llastmileagent/Signin.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title:'fultter demo ',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      debugShowCheckedModeBanner: false,
      home: MedicineOnboardingScreen(),
    );
  }
}





class MedicineOnboardingScreen extends StatefulWidget {
  @override
  _MedicineOnboardingScreenState createState() => _MedicineOnboardingScreenState();
}

class _MedicineOnboardingScreenState extends State<MedicineOnboardingScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: BoxDecoration(
          image: DecorationImage(
            image: AssetImage('assets/images/ambulance.png'), // Ambulance/delivery at sunset
            fit: BoxFit.cover,
          ),
        ),
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Colors.black.withOpacity(0.7),
                Colors.black.withOpacity(0.3),
              ],
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: EdgeInsets.all(32.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Dots section completely removed
                  Spacer(),
                  // Title and Subtitle (Ambulance-themed)
                  Column(
                    children: [
                      Text(
                        'Smart Medicine\nDelivery Made Simple',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 36,
                          fontWeight: FontWeight.bold,
                          height: 1.1,
                          shadows: [Shadow(color: Colors.black54, offset: Offset(2, 2), blurRadius: 4)],
                        ),
                      ),
                      SizedBox(height: 24),
                      Text(
                        'Stay updated every step of the way with\nlive tracking.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.9),
                          fontSize: 18,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 60),
                  // Get Started Button
                  TextButton(
                    onPressed: () {
                      Navigator.push(
                          context,
                        MaterialPageRoute(
                          builder: (_) => SignInScreen(),
                        ),
                      );
                    },
                    child: Container(
                      width: double.infinity,
                      padding: EdgeInsets.symmetric(vertical: 20),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [Colors.green[600]!, Colors.green[700]!]),
                        borderRadius: BorderRadius.circular(30),
                        boxShadow: [BoxShadow(color: Colors.green.withOpacity(0.5), blurRadius: 20, offset: Offset(0, 10))],
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.arrow_forward, color: Colors.white),
                          SizedBox(width: 12),
                          Text('Get Started', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
