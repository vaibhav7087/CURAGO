import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'UpiQrScreen.dart';
import 'PaymentSuccessScreen.dart';
import 'package:curago_field_app/config.dart';

class PaymentScreen extends StatefulWidget {
  final Map<String, dynamic> order;
  const PaymentScreen({Key? key, required this.order}) : super(key: key);

  @override
  _PaymentScreenState createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  String selectedPayment = 'Cash';
  bool isProcessing = false;

  Future<void> markDelivered() async {
    setState(() => isProcessing = true);
    try {
      final response = await http.patch(
        Uri.parse('${AppConfig.baseUrl}/api/orders/${widget.order['id']}/status'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'status': 'Delivered'}),
      );

      if (response.statusCode == 200) {
        if (selectedPayment == 'Cash') {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => PaymentSuccessScreen(order: widget.order),
            ),
          );
        } else if (selectedPayment == 'UPI') {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => UpiQrScreen(order: widget.order),
            ),
          );
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to update status')));
      }
    } catch (e) {
      print(e);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Network error')));
    } finally {
      setState(() => isProcessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final order = widget.order;

    return Scaffold(
      backgroundColor: Colors.grey[900],
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('Payment', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 20)),
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.grey[800],
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Total Amount', style: TextStyle(color: Colors.white, fontSize: 16)),
                      Text(order['totalAmount'], style: TextStyle(color: Colors.green[500], fontWeight: FontWeight.bold, fontSize: 20)),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text('Order: ${order['id'].toString().substring(0, 8)}', style: TextStyle(color: Colors.grey[400], fontSize: 12)),
                ],
              ),
            ),
            SizedBox(height: 32),
            Text('Select Payment Method', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 20),
            GestureDetector(
              onTap: () => setState(() => selectedPayment = 'Cash'),
              child: Container(
                width: double.infinity,
                padding: EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.grey[850],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: selectedPayment == 'Cash' ? Colors.green[400]! : Colors.transparent,
                    width: selectedPayment == 'Cash' ? 2 : 1,
                  ),
                  boxShadow: selectedPayment == 'Cash'
                      ? [BoxShadow(color: Colors.green.withOpacity(0.2), blurRadius: 10)]
                      : [],
                ),
                child: Row(
                  children: [
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.green[500]!.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(Icons.attach_money, color: Colors.green[500], size: 24),
                    ),
                    SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        'Cash Collected',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    if (selectedPayment == 'Cash')
                      Icon(Icons.check_circle, color: Colors.green[500], size: 28),
                  ],
                ),
              ),
            ),
            SizedBox(height: 16),
            GestureDetector(
              onTap: () => setState(() => selectedPayment = 'UPI'),
              child: Container(
                width: double.infinity,
                padding: EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.grey[850],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: selectedPayment == 'UPI' ? Colors.blue[400]! : Colors.transparent,
                    width: selectedPayment == 'UPI' ? 2 : 1,
                  ),
                  boxShadow: selectedPayment == 'UPI'
                      ? [BoxShadow(color: Colors.blue.withOpacity(0.2), blurRadius: 10)]
                      : [],
                ),
                child: Row(
                  children: [
                    Container(
                      padding: EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.blue[500]!.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(Icons.qr_code_2, color: Colors.blue[500], size: 24),
                    ),
                    SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        'UPI QR Code',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    if (selectedPayment == 'UPI')
                      Icon(Icons.check_circle, color: Colors.blue[500], size: 28),
                  ],
                ),
              ),
            ),
            Spacer(),
            Container(
              width: double.infinity,
              height: 60,
              child: ElevatedButton(
                onPressed: isProcessing ? null : markDelivered,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green[500],
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  elevation: 8,
                ),
                child: isProcessing
                    ? CircularProgressIndicator(color: Colors.white)
                    : Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle_outline, size: 28),
                          SizedBox(width: 12),
                          Text(
                            'MARK DELIVERED',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 18,
                              letterSpacing: 1,
                            ),
                          ),
                        ],
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
