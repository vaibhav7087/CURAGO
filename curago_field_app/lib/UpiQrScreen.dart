import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'Paymentsuccessscreen.dart';

class UpiQrScreen extends StatelessWidget {
  final Map<String, dynamic> order;

  const UpiQrScreen({Key? key, required this.order}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final String amount =
    order['totalAmount'].toString().replaceAll("₹", "");

    // 🔥 UPI Payment String Format
    final String upiId = "tanvig807-4@okhdfcbank";
    final String upiUrl =
        "upi://pay?pa=$upiId&pn=MyStore&am=$amount&cu=INR&tn=Order ${order['id']}";

    return Scaffold(
      backgroundColor: Colors.grey[900],
      appBar: AppBar(
        title: Text("UPI Payment"),
        backgroundColor: Colors.black,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [

            Text(
              "Scan & Pay",
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),

            SizedBox(height: 10),


            Text(
              "UPI ID",
              style: TextStyle(
                color: Colors.grey[400],
                fontSize: 14,
              ),
            ),

            SizedBox(height: 5),

            Container(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.grey[800],
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    upiId,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Icon(Icons.copy, color: Colors.green[400]),
                ],
              ),
            ),

            SizedBox(height: 20),

            Text(
              "Amount: ₹$amount",
              style: TextStyle(
                fontSize: 18,
                color: Colors.green[400],
              ),
            ),

            SizedBox(height: 40),

            // 🔥 QR CODE
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
              ),
              child: QrImageView(
                data: upiUrl,
                size: 250,
              ),
            ),

            SizedBox(height: 40),

            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                      builder: (_) =>
                          PaymentSuccessScreen(order: order),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green[600],
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: Text(
                  "PAYMENT DONE",
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}