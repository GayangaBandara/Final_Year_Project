import 'dart:async';
import 'package:flutter/material.dart';
import 'package:safespace/services/chat_service.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class ChatBotScreen extends StatefulWidget {
  @override
  _ChatBotScreenState createState() => _ChatBotScreenState();
}

class _ChatBotScreenState extends State<ChatBotScreen> {
  final TextEditingController _controller = TextEditingController();
  List<Map<String, dynamic>> messages = [];
  bool isLoading = false;
  final supabase = Supabase.instance.client;
  String? userId;
  String? currentConversationId;
  StreamSubscription<List<Map<String, dynamic>>>? _messageSubscription;
  String selectedModel = "llama2-70b-4096";

  @override
  void initState() {
    super.initState();
    _initializeUser();
    _startNewConversation();
  }

  @override
  void dispose() {
    _messageSubscription?.cancel();
    _controller.dispose();
    _endCurrentConversation();
    super.dispose();
  }

  Future<void> _initializeUser() async {
    final user = supabase.auth.currentUser;
    setState(() {
      userId = user?.id;
    });
  }

  Future<void> _startNewConversation() async {
    setState(() {
      messages = [];
      isLoading = true;
    });

    try {
      // Create a new conversation
      final response = await supabase
          .from('conversations')
          .insert({'user_id': userId})
          .select()
          .single();

      setState(() {
        currentConversationId = response['id'] as String;
      });

      _setupRealtime();
    } catch (e) {
      print('Error starting new conversation: $e');
    } finally {
      setState(() => isLoading = false);
    }
  }

  //mainnnnnass
  Future<void> _endCurrentConversation() async {
    if (currentConversationId != null) {
      try {
        await supabase
            .from('conversations')
            .update({'ended_at': DateTime.now().toIso8601String()})
            .eq('id', currentConversationId!);
      } catch (e) {
        print('Error ending conversation: $e');
      }
    }
  }

  Future<void> _storeMessage(String message, bool isBot) async {
    if (userId == null || currentConversationId == null) return;

    try {
      await supabase.from('messages').insert({
        'conversation_id': currentConversationId,
        'user_id': userId,
        'message': message,
        'is_bot': isBot,
      });

      // Update conversation title with first message
      if (messages.isEmpty && !isBot) {
        await supabase
            .from('conversations')
            .update({'title': _generateConversationTitle(message)})
            .eq('id', currentConversationId!);
      }
    } catch (e) {
      print('Error storing message: $e');
    }
  }

  String _generateConversationTitle(String firstMessage) {
    final trimmed = firstMessage.trim();
    return trimmed.length > 30 ? '${trimmed.substring(0, 30)}...' : trimmed;
  }

  void _setupRealtime() {
    _messageSubscription = supabase
        .from('messages')
        .stream(primaryKey: ['id'])
        .order('created_at')
        .listen((List<Map<String, dynamic>> data) {
          // Filter messages to only include current conversation
          final conversationMessages = data
              .where((msg) => msg['conversation_id'] == currentConversationId)
              .toList();

          if (conversationMessages.isNotEmpty) {
            final newMsg = conversationMessages.last;
            if (newMsg['user_id'] == userId &&
                !messages.any((m) => m['text'] == newMsg['message'])) {
              setState(() {
                messages.add({
                  'sender': newMsg['is_bot'] ? 'bot' : 'user',
                  'text': newMsg['message'],
                  'timestamp': newMsg['created_at'],
                });
              });
            }
          }
        });
  }

  String _formatTimestamp(dynamic timestamp) {
    if (timestamp == null) return '';
    DateTime time = timestamp is DateTime
        ? timestamp
        : DateTime.parse(timestamp);
    return '${time.hour}:${time.minute.toString().padLeft(2, '0')}';
  }

  void handleSend() async {
    String userInput = _controller.text.trim();
    if (userInput.isEmpty || userId == null || currentConversationId == null)
      return;

    setState(() {
      messages.add({"sender": "user", "text": userInput});
      _controller.clear();
      isLoading = true;
    });

    await _storeMessage(userInput, false);

    messages.add({"sender": "bot", "text": "Thinking..."});
    setState(() {});

    try {
      String botReply = await ChatService.sendMessage(userInput, selectedModel);
      messages.removeLast();
      await _storeMessage(botReply, true);

      setState(() {
        messages.add({"sender": "bot", "text": botReply});
      });
    } catch (e) {
      messages.removeLast();
      setState(() {
        messages.add({
          "sender": "bot",
          "text": "Sorry, I encountered an error. Please try again.",
        });
      });
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFF0F8F7),
      appBar: AppBar(
        backgroundColor: Color(0xFFB2DFDB),
        title: Row(
          children: [
            Icon(Icons.spa, color: Colors.white),
            SizedBox(width: 10),
            Text(
              "SafeSpace Chat",
              style: TextStyle(fontFamily: 'Arial Rounded', fontSize: 20),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(10),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final msg = messages[index];
                final isUser = msg['sender'] == 'user';
                return Column(
                  crossAxisAlignment: isUser
                      ? CrossAxisAlignment.end
                      : CrossAxisAlignment.start,
                  children: [
                    if (index == 0 ||
                        messages[index - 1]['sender'] != msg['sender'] ||
                        (msg['timestamp'] != null &&
                            messages[index - 1]['timestamp'] != null &&
                            (DateTime.parse(msg['timestamp'])
                                    .difference(
                                      DateTime.parse(
                                        messages[index - 1]['timestamp'],
                                      ),
                                    )
                                    .inMinutes >
                                5)))
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Text(
                          _formatTimestamp(msg['timestamp']),
                          style: TextStyle(color: Colors.grey, fontSize: 12),
                        ),
                      ),
                    Align(
                      alignment: isUser
                          ? Alignment.centerRight
                          : Alignment.centerLeft,
                      child: Container(
                        margin: EdgeInsets.symmetric(vertical: 6),
                        padding: EdgeInsets.all(14),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.75,
                        ),
                        decoration: BoxDecoration(
                          color: isUser ? Color(0xFF80CBC4) : Colors.white,
                          borderRadius: BorderRadius.only(
                            topLeft: Radius.circular(16),
                            topRight: Radius.circular(16),
                            bottomLeft: Radius.circular(isUser ? 16 : 0),
                            bottomRight: Radius.circular(isUser ? 0 : 16),
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.grey.shade300,
                              blurRadius: 4,
                              offset: Offset(2, 2),
                            ),
                          ],
                        ),
                        child: MarkdownBody(
                          data: msg['text'] ?? '',
                          styleSheet: MarkdownStyleSheet(
                            p: TextStyle(fontSize: 16, height: 1.4),
                          ),
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    enabled: !isLoading,
                    decoration: InputDecoration(
                      hintText: "Type something to share...",
                      filled: true,
                      fillColor: Color(0xFFE0F2F1),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(20),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (_) => handleSend(),
                  ),
                ),
                SizedBox(width: 8),
                ElevatedButton(
                  onPressed: isLoading ? null : handleSend,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFF26A69A),
                    shape: CircleBorder(),
                    padding: EdgeInsets.all(12),
                  ),
                  child: isLoading
                      ? SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.5,
                            color: Colors.white,
                          ),
                        )
                      : Icon(Icons.send, color: Colors.white),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
