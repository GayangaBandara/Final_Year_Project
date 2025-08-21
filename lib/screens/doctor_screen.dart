import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';

class DoctorScreen extends StatefulWidget {
  @override
  _DoctorScreenState createState() => _DoctorScreenState();
}

class _DoctorScreenState extends State<DoctorScreen> {
  String? assignedDoctor;
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchDoctor();
  }

  Future<void> _fetchDoctor() async {
    try {
      final user = Supabase.instance.client.auth.currentUser;
      if (user == null) {
        setState(() {
          assignedDoctor = "User not logged in.";
          isLoading = false;
        });
        return;
      }

      // Call your backend API
      final response = await http.post(
        Uri.parse("http://127.0.0.1:8000/recommend"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"user_id": user.id}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          if (data["assigned_doctor"] != null) {
            assignedDoctor = "Doctor assigned: ${data["assigned_doctor"]["name"] ?? "Unknown"}";
          } else {
            assignedDoctor = data["error"] ?? "No doctor assigned yet";
          }
          isLoading = false;
        });
      } else {
        setState(() {
          assignedDoctor = "Failed to fetch doctor";
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        assignedDoctor = "Error: $e";
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Assigned Doctor")),
      body: Center(
        child: isLoading
            ? CircularProgressIndicator()
            : Text(
                assignedDoctor ?? "No doctor assigned",
                style: TextStyle(fontSize: 18),
              ),
      ),
    );
  }
}
