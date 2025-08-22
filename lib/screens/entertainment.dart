import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';

class EntertainmentScreen extends StatefulWidget {
  const EntertainmentScreen({super.key});

  @override
  State<EntertainmentScreen> createState() => _EntertainmentScreenState();
}

class _EntertainmentScreenState extends State<EntertainmentScreen> {
  List<Map<String, dynamic>> entertainmentItems = [];
  bool isLoading = true;
  String errorMessage = '';
  String selectedCategory = 'All';
  final List<String> categories = ['All', 'Meditation', 'Music Track'];

  @override
  void initState() {
    super.initState();
    fetchEntertainmentContent();
  }

  Future<void> fetchEntertainmentContent() async {
    try {
      final user = Supabase.instance.client.auth.currentUser;
      if (user == null) {
        setState(() {
          errorMessage = '⚠️ Please log in to see entertainment recommendations.';
          isLoading = false;
        });
        return;
      }

      final response = await http.post(
        Uri.parse('http://192.168.1.6:8000/recommend_entertainment'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ${user.id}',
        },
        body: jsonEncode({'user_id': user.id}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] && data['recommendations'] != null) {
          setState(() {
            entertainmentItems = List<Map<String, dynamic>>.from(
              data['recommendations'],
            );
            isLoading = false;
            errorMessage = '';
          });
        } else {
          setState(() {
            entertainmentItems = [];
            errorMessage = data['message'] ?? 'No recommendations available.';
            isLoading = false;
          });
        }
      } else {
        final error = jsonDecode(response.body);
        setState(() {
          errorMessage = error['detail'] ?? 'Failed to load (${response.statusCode})';
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = "❌ Connection Error: $e";
        isLoading = false;
      });
    }
  }

  List<Map<String, dynamic>> get filteredItems {
    if (selectedCategory == 'All') return entertainmentItems;
    return entertainmentItems.where((item) => item['type'] == selectedCategory).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color.fromARGB(255, 248, 246, 246), // Spotify-style dark background
      appBar: AppBar(
        title: const Text("Entertainment", style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color.fromARGB(255, 255, 255, 255),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: fetchEntertainmentContent,
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.greenAccent))
          : errorMessage.isNotEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(errorMessage,
                        style: const TextStyle(fontSize: 16, color: Colors.red),
                        textAlign: TextAlign.center),
                  ),
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Category Tabs
                    SizedBox(
                      height: 50,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        itemCount: categories.length,
                        separatorBuilder: (_, __) => const SizedBox(width: 12),
                        itemBuilder: (context, index) {
                          final category = categories[index];
                          final isSelected = selectedCategory == category;
                          return ChoiceChip(
                            label: Text(category,
                                style: TextStyle(
                                  color: isSelected ? const Color.fromARGB(255, 109, 108, 108) : const Color.fromARGB(255, 255, 254, 254),
                                )),
                            selected: isSelected,
                            selectedColor: Colors.greenAccent,
                            backgroundColor: Colors.grey[900],
                            onSelected: (_) {
                              setState(() => selectedCategory = category);
                            },
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Recommended Header
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 16),
                      child: Text(
                        "Recommended for You",
                        style: TextStyle(
                          color: Color.fromARGB(255, 14, 13, 13),
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Horizontal Carousel
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        itemCount: filteredItems.length,
                        itemBuilder: (context, index) {
                          final item = filteredItems[index];
                          return Container(
                            margin: const EdgeInsets.only(bottom: 20),
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(16),
                              child: Stack(
                                children: [
                                  // Cover Image
                                  AspectRatio(
                                    aspectRatio: 16 / 9,
                                    child: item['cover_img_url'] != null
                                        ? Image.network(item['cover_img_url'],
                                            fit: BoxFit.cover)
                                        : Container(
                                            color: Colors.grey[800],
                                            child: Icon(
                                              item['type'] == 'Meditation'
                                                  ? Icons.self_improvement
                                                  : Icons.music_note,
                                              size: 50,
                                              color: const Color.fromARGB(255, 5, 5, 5),
                                            ),
                                          ),
                                  ),

                                  // Gradient Overlay
                                  Container(
                                    decoration: BoxDecoration(
                                      gradient: LinearGradient(
                                        colors: [
                                          Colors.black.withOpacity(0.6),
                                          Colors.transparent,
                                        ],
                                        begin: Alignment.bottomCenter,
                                        end: Alignment.topCenter,
                                      ),
                                    ),
                                  ),

                                  // Text + Play Button
                                  Positioned(
                                    bottom: 16,
                                    left: 16,
                                    right: 16,
                                    child: Row(
                                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                      children: [
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(item['title'] ?? 'Untitled',
                                                  style: const TextStyle(
                                                      color: Color.fromARGB(255, 22, 22, 22),
                                                      fontWeight: FontWeight.bold,
                                                      fontSize: 18),
                                                  maxLines: 1,
                                                  overflow: TextOverflow.ellipsis),
                                              Text(
                                                item['description'] ??
                                                    'No description available',
                                                style: TextStyle(
                                                    color: const Color.fromARGB(255, 92, 91, 91),
                                                    fontSize: 14),
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            ],
                                          ),
                                        ),
                                        InkWell(
                                          onTap: () {
                                            print("Playing: ${item['title']}");
                                          },
                                          child: Container(
                                            decoration: const BoxDecoration(
                                              shape: BoxShape.circle,
                                              color: Colors.greenAccent,
                                            ),
                                            padding: const EdgeInsets.all(12),
                                            child: const Icon(Icons.play_arrow,
                                                size: 28, color: Colors.black),
                                          ),
                                        )
                                      ],
                                    ),
                                  ),
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
