import 'dart:convert';
import 'package:http/http.dart' as http;

class ChatService {
  static const String _baseUrl = 'http://localhost:8000/api/chat';

  static Future<String> sendMessage(String userMessage, String model) async {
    final url = Uri.parse(_baseUrl);

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: json.encode({"message": userMessage, "model": model}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['response'] ?? "⚠ No response from AI.";
      } else {
        print("Server Error Status: ${response.statusCode}");
        print("Server Error Body: ${response.body}");
        return "⚠ Server Error: ${response.statusCode} - ${response.body}";
      }
    } catch (e) {
      print("Network Error: $e");
      return "⚠ Network Error: $e";
    }
  }
}
