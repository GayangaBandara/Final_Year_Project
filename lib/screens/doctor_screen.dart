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
    // Add a small delay to ensure Supabase is initialized
    Future.delayed(Duration(milliseconds: 500), _fetchDoctor);
  }

  Future<void> _fetchDoctor() async {
    setState(() {
      isLoading = true;
    });

    try {
      final user = Supabase.instance.client.auth.currentUser;
      if (user == null) {
        setState(() {
          assignedDoctor = "⚠️ Please log in to see your assigned doctor.";
          isLoading = false;
        });
        return;
      }

      // Call your backend API
      final response = await http.post(
        Uri.parse("http://192.168.1.6:8000/recommend"),
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer ${user.id}", // Add auth token if needed
        },
        body: jsonEncode({"user_id": user.id}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          if (data["assigned_doctor"] != null) {
            final doctor = data["assigned_doctor"];
            assignedDoctor =
                """
👨‍⚕️ Dr. ${doctor["name"] ?? "Unknown"}
📧 Email: ${doctor["email"] ?? "N/A"}
📞 Phone: ${doctor["phone"] ?? "N/A"}
🏥 Category: ${doctor["category"] ?? "General"}
""";
          } else {
            assignedDoctor =
                """
⚠️ ${data["error"] ?? "No doctor assigned yet"}

This could be because:
• Your mental state assessment is pending
• No matching doctor is available
• System is still processing your request

Please try again in a few moments.
""";
          }
          isLoading = false;
        });
      } else {
        setState(() {
          assignedDoctor =
              """
❌ Failed to fetch doctor information

Error: ${response.statusCode} - ${response.reasonPhrase}
Please check your internet connection and try again.
""";
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        assignedDoctor =
            """
❌ Connection Error

Could not connect to the server. This might be because:
• You're not connected to the internet
• The server is not running
• The server URL is incorrect

Technical details: $e
""";
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Assigned Doctor"),
        backgroundColor: Theme.of(context).primaryColor,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: isLoading
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text(
                      "Finding the best doctor for you...",
                      style: TextStyle(fontSize: 16),
                    ),
                  ],
                ),
              )
            : RefreshIndicator(
                onRefresh: _fetchDoctor,
                child: ListView(
                  children: [
                    Card(
                      elevation: 4,
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "Your Mental Health Professional",
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Theme.of(context).primaryColor,
                              ),
                            ),
                            SizedBox(height: 16),
                            Text(
                              assignedDoctor ?? "No doctor assigned",
                              style: TextStyle(fontSize: 18),
                            ),
                            SizedBox(height: 16),
                            if (assignedDoctor?.contains("Error") ?? false)
                              ElevatedButton(
                                onPressed: _fetchDoctor,
                                child: Text("Try Again"),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Theme.of(
                                    context,
                                  ).primaryColor,
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }
}
