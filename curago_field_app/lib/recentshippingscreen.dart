import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'OrderDetailScreen.dart';
import 'package:curago_field_app/config.dart';

class RecentShippingScreen extends StatefulWidget {
  final String userName;

  const RecentShippingScreen({super.key, required this.userName});
  @override
  _RecentShippingScreenState createState() => _RecentShippingScreenState();
}

class _RecentShippingScreenState extends State<RecentShippingScreen> {
  TextEditingController searchController = TextEditingController();
  String searchQuery = '';
  int currentTabIndex = 0;
  List<dynamic> orders = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchOrders();
  }

  Future<void> fetchOrders() async {
    setState(() => isLoading = true);
    try {
      final shift = currentTabIndex == 0 ? 'Morning' : 'Evening';
      final response = await http.get(Uri.parse('${AppConfig.baseUrl}/api/orders/?shift=$shift'));
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          orders = data.map((o) => {
                'id': o['id'],
                'status': o['status'],
                'statusColor': o['status'] == 'Delivered' ? Colors.blue[600]! : Colors.green[500]!,
                'address': o['delivery_address'] ?? 'Unknown Address',
                'customerName': o['patient_name'] ?? 'Unknown',
                'package': 'Prescription Meds',
                'totalAmount': '₹' + (o['total_bill']?.toString() ?? '150'),
                'liveTime': 'Now',
                'codAmount': '₹' + (o['total_bill']?.toString() ?? '150'),
                'packageItems': o['package_items'] ?? [],
              }).toList();
        });
      }
    } catch (e) {
      print('Error fetching orders: $e');
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final filteredOrders = orders.where((order) =>
        order['id'].toString().toLowerCase().contains(searchQuery) ||
        order['customerName'].toString().toLowerCase().contains(searchQuery)).toList();

    return Scaffold(
      backgroundColor: Colors.grey[900],
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: Padding(
          padding: EdgeInsets.only(left: 16),
          child: CircleAvatar(
            radius: 18,
            backgroundImage: NetworkImage("https://img.freepik.com/premium-vector/20-yearold-man-black-short-hair-front-view-white-background-vector-illustration-cartoon_969863-149862.jpg?w=740"),
          ),
        ),
        title: Row(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Hi', style: TextStyle(color: Colors.grey[400], fontSize: 14)),
                Text(widget.userName, style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            Spacer(),
            Stack(
              children: [
                Icon(Icons.notifications_outlined, color: Colors.white70),
                Positioned(right: 0, top: 0, child: Container(width: 8, height: 8, decoration: BoxDecoration(color: Colors.red, shape: BoxShape.circle))),
              ],
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Recent Shipping', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                SizedBox(height: 16),
                Container(
                  height: 50,
                  child: Row(
                    children: [
                      Expanded(
                        child: GestureDetector(
                          onTap: () {
                            setState(() => currentTabIndex = 0);
                            fetchOrders();
                          },
                          child: Container(
                            decoration: BoxDecoration(
                              color: currentTabIndex == 0 ? Colors.green[500] : Colors.transparent,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.green[400]!),
                            ),
                            child: Center(child: Text('Morning Shift', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
                          ),
                        ),
                      ),
                      SizedBox(width: 12),
                      Expanded(
                        child: GestureDetector(
                          onTap: () {
                            setState(() => currentTabIndex = 1);
                            fetchOrders();
                          },
                          child: Container(
                            decoration: BoxDecoration(
                              color: currentTabIndex == 1 ? Colors.green[500] : Colors.transparent,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: Colors.green[400]!),
                            ),
                            child: Center(child: Text('Evening Shift', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                SizedBox(height: 16),
                Container(
                  decoration: BoxDecoration(color: Colors.grey[800], borderRadius: BorderRadius.circular(15)),
                  child: TextField(
                    controller: searchController,
                    style: TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Search shipping...',
                      hintStyle: TextStyle(color: Colors.grey[500]),
                      prefixIcon: Icon(Icons.search, color: Colors.green[500]),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                    ),
                    onChanged: (value) => setState(() => searchQuery = value.toLowerCase()),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: isLoading
                ? Center(child: CircularProgressIndicator(color: Colors.green[500]))
                : filteredOrders.isEmpty
                    ? Center(child: Text('No orders found', style: TextStyle(color: Colors.grey[400])))
                    : ListView.builder(
                        padding: EdgeInsets.symmetric(horizontal: 24),
                        itemCount: filteredOrders.length,
                        itemBuilder: (context, index) {
                          final order = filteredOrders[index];
                          final showDeliverButton = order['status'] != 'Delivered';
                          return GestureDetector(
                            onTap: () {
                              Navigator.push(context, MaterialPageRoute(builder: (context) => OrderDetailScreen(order: order))).then((_) => fetchOrders());
                            },
                            child: Container(
                              margin: EdgeInsets.only(bottom: 16),
                              padding: EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: Colors.grey[850],
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(width: 5, color: order['statusColor']),
                                boxShadow: [BoxShadow(color: Colors.green.withOpacity(0.2), blurRadius: 10, offset: Offset(0, 4))],
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Row(
                                        children: [
                                          CircleAvatar(
                                            radius: 18,
                                            backgroundColor: Colors.green[500],
                                            child: Text(order['customerName'][0], style: TextStyle(color: Colors.white)),
                                          ),
                                          SizedBox(width: 12),
                                          Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(order['customerName'], style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                                              Text(order['id'].toString().substring(0, 8), style: TextStyle(color: Colors.grey[400], fontSize: 12)),
                                            ],
                                          ),
                                        ],
                                      ),
                                      Container(
                                        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                        decoration: BoxDecoration(
                                          color: order['statusColor'].withOpacity(0.2),
                                          borderRadius: BorderRadius.circular(20),
                                          border: Border.all(color: order['statusColor'], width: 1),
                                        ),
                                        child: Text(order['status'], style: TextStyle(color: order['statusColor'], fontWeight: FontWeight.bold, fontSize: 12)),
                                      ),
                                    ],
                                  ),
                                  SizedBox(height: 16),
                                  Row(
                                    children: [
                                      Expanded(child: Text(order['package'], style: TextStyle(color: Colors.green[400]!, fontSize: 14))),
                                      Container(
                                        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                        decoration: BoxDecoration(
                                          color: Colors.green[500]!.withOpacity(0.2),
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: Text(order['totalAmount'], style: TextStyle(color: Colors.green[500]!, fontWeight: FontWeight.bold)),
                                      ),
                                    ],
                                  ),
                                  SizedBox(height: 16),
                                  Container(
                                    width: double.infinity,
                                    padding: EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: Colors.grey[800],
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(Icons.location_on, color: Colors.green[500], size: 18),
                                        SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            order['address'],
                                            style: TextStyle(color: Colors.grey[300], fontSize: 13),
                                            maxLines: 2,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (showDeliverButton) ...[
                                    SizedBox(height: 16),
                                    Row(
                                      mainAxisAlignment: MainAxisAlignment.end,
                                      children: [
                                        ElevatedButton(
                                          onPressed: () {
                                            Navigator.push(
                                              context,
                                              MaterialPageRoute(builder: (context) => OrderDetailScreen(order: order)),
                                            ).then((_) => fetchOrders());
                                          },
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: Colors.green[500],
                                            foregroundColor: Colors.white,
                                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                                          ),
                                          child: Text('Deliver Now', style: TextStyle(fontWeight: FontWeight.bold)),
                                        ),
                                      ],
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
