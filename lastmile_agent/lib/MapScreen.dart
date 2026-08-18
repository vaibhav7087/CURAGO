import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geocoding/geocoding.dart';

class MapScreen extends StatefulWidget {
  final String address;

  const MapScreen({Key? key, required this.address}) : super(key: key);

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  GoogleMapController? mapController;
  LatLng? destination;

  @override
  void initState() {
    super.initState();
    getLocationFromAddress();
  }

  Future<void> getLocationFromAddress() async {
    List<Location> locations =
    await locationFromAddress(widget.address);

    setState(() {
      destination =
          LatLng(locations.first.latitude, locations.first.longitude);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Delivery Location")),
      body: destination == null
          ? Center(child: CircularProgressIndicator())
          : GoogleMap(
        initialCameraPosition: CameraPosition(
          target: destination!,
          zoom: 16,
        ),
        markers: {
          Marker(
            markerId: MarkerId("destination"),
            position: destination!,
            infoWindow: InfoWindow(title: "Customer Location"),
          ),
        },
        onMapCreated: (controller) {
          mapController = controller;
        },
      ),
    );
  }
}