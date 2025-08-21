import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';

class DoctorRecommendationService {
  final String backendUrl = "http://127.0.0.1:8000/recommend"; // replace with deployed URL

  Future<Map<String, dynamic>?> getRecommendedDoctor() async {
    final user = Supabase.instance.client.auth.currentUser;

    if (user == null) {
      throw Exception("User not logged in");
    }

    final response = await http.post(
      Uri.parse(backendUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"user_id": user.id}),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      print("Error: ${response.body}");
      return null;
    }
  }
}
