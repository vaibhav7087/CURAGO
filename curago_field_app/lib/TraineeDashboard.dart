
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'package:curago_field_app/config.dart';

class TraineeDashboard extends StatefulWidget {
  @override
  _TraineeDashboardState createState() => _TraineeDashboardState();
}

class _TraineeDashboardState extends State<TraineeDashboard> {
  List<dynamic> patients = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchTasks();
  }

  Future<void> fetchTasks() async {
    try {
      final response = await http.get(Uri.parse('\/api/trainee/tasks/all'));
      if (response.statusCode == 200) {
        setState(() {
          patients = json.decode(response.body);
          isLoading = false;
        });
      } else {
        setState(() => isLoading = false);
      }
    } catch (e) {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Trainee Dashboard')),
      body: isLoading 
        ? Center(child: CircularProgressIndicator()) 
        : patients.isEmpty 
          ? Center(child: Text('No assigned tasks'))
          : ListView.builder(
              itemCount: patients.length,
              itemBuilder: (context, index) {
                final ticket = patients[index];
                final patientInfo = ticket['patients'] ?? {};
                return ListTile(
                  title: Text(patientInfo['name'] ?? 'Unknown Patient'),
                  subtitle: Text(ticket['symptoms_summary'] ?? 'No symptoms logged'),
                  trailing: ElevatedButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => VitalsCollectionScreen(ticketId: ticket['id'])),
                      );
                    },
                    child: Text('Collect Vitals'),
                  ),
                );
              },
            ),
    );
  }
}

class VitalsCollectionScreen extends StatefulWidget {
  final String ticketId;
  VitalsCollectionScreen({required this.ticketId});

  @override
  _VitalsCollectionScreenState createState() => _VitalsCollectionScreenState();
}

class _VitalsCollectionScreenState extends State<VitalsCollectionScreen> {
  final _tempController = TextEditingController();
  final _bpController = TextEditingController();
  final _spo2Controller = TextEditingController();
  final _extraController = TextEditingController();

  bool _isLoading = false;
  bool _isUploading = false;
  List<String> _requestedChecks = [];
  String? _finalDiagnosis;
  List<String> _uploadedPhotoUrls = [];
  
  final ImagePicker _picker = ImagePicker();

  Future<void> uploadPhoto() async {
    final XFile? photo = await _picker.pickImage(source: ImageSource.camera);
    if (photo == null) return;
    
    setState(() {
      _isUploading = true;
    });
    
    try {
      var request = http.MultipartRequest('POST', Uri.parse('https://api.cloudinary.com/v1_1/db0vjc4gf/image/upload'));
      request.fields['upload_preset'] = 'college_unsigned';
      request.fields['folder'] = 'curago/patient_photos';
      request.files.add(await http.MultipartFile.fromPath('file', photo.path));
      
      var response = await request.send();
      if (response.statusCode == 200) {
        final responseData = await response.stream.bytesToString();
        final jsonResponse = jsonDecode(responseData);
        setState(() {
          _uploadedPhotoUrls.add(jsonResponse['secure_url']);
        });
      }
    } catch (e) {
      print('Upload failed: \');
    } finally {
      setState(() {
        _isUploading = false;
      });
    }
  }

  Future<void> submitVitals() async {
    setState(() {
      _isLoading = true;
    });
    
    final url = Uri.parse('\/api/tickets/vitals/\');
    final payload = {
      'temperature': _tempController.text,
      'blood_pressure': _bpController.text,
      'spo2': _spo2Controller.text,
      'extra_notes': _extraController.text,
      'photo_urls': _uploadedPhotoUrls
    };

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );

      final data = jsonDecode(response.body);

      if (data['status'] == 'needs_more_checks') {
        setState(() {
          _requestedChecks = List<String>.from(data['requested_checks']);
          _isLoading = false;
        });
      } else if (data['status'] == 'complete') {
        setState(() {
          _finalDiagnosis = data['advanced_diagnosis'];
          _isLoading = false;
        });
      } else {
        setState(() { _isLoading = false; });
      }
    } catch (e) {
      print('Error: \');
      setState(() { _isLoading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Record Vitals')),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(controller: _tempController, decoration: InputDecoration(labelText: 'Temperature (F)')),
            TextField(controller: _bpController, decoration: InputDecoration(labelText: 'Blood Pressure (e.g. 120/80)')),
            TextField(controller: _spo2Controller, decoration: InputDecoration(labelText: 'SpO2 (%)')),
            
            SizedBox(height: 20),
            ElevatedButton.icon(
              icon: _isUploading ? SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : Icon(Icons.camera_alt),
              label: Text('Upload Clinical Photo (Optional)'),
              onPressed: _isUploading ? null : uploadPhoto,
            ),
            if (_uploadedPhotoUrls.isNotEmpty) ...[
              SizedBox(height: 10),
              Wrap(
                spacing: 10,
                children: _uploadedPhotoUrls.map((url) => Image.network(url, width: 80, height: 80, fit: BoxFit.cover)).toList(),
              )
            ],
            
            if (_requestedChecks.isNotEmpty) ...[
              SizedBox(height: 20),
              Text('AI requests additional checks:', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
              for (var check in _requestedChecks) Text('- \'),
              TextField(controller: _extraController, decoration: InputDecoration(labelText: 'Enter additional check results')),
            ],
            SizedBox(height: 20),
            _isLoading 
              ? CircularProgressIndicator() 
              : ElevatedButton(
                  onPressed: submitVitals, 
                  child: Text(_requestedChecks.isEmpty ? 'Analyze Vitals' : 'Submit Additional Checks')
                ),
            if (_finalDiagnosis != null) ...[
              SizedBox(height: 20),
              Text('? AI Diagnosis Complete', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 18)),
              Container(
                margin: EdgeInsets.only(top: 10),
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(8)),
                child: Text(_finalDiagnosis!, style: TextStyle(fontSize: 14)),
              ),
            ]
          ],
        ),
      ),
    );
  }
}

