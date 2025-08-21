import 'package:flutter/material.dart';
import 'package:safespace/navbar.dart';
import 'package:safespace/homescreen.dart';
import 'package:safespace/screens/profile.dart';
import 'package:safespace/screens/doctor_screen.dart';
import 'package:safespace/screens/entertainment.dart';




class NavManager extends StatefulWidget {
  final bool isGuest;
  const NavManager({super.key, required this.isGuest});

  @override
  State<NavManager> createState() => _NavManagerState();
}

class _NavManagerState extends State<NavManager> {
  int _selectedIndex = 0;

  late final List<Widget> _screens = [
    const HomeScreen(),
    const EntertainmentScreen(),
    if (!widget.isGuest)  DoctorScreen() else const SizedBox.shrink(),
    if (!widget.isGuest) const ProfilePage() else const SizedBox.shrink(),
  ];

  void _onTabChange(int index) {
    if (widget.isGuest && index >= 2) {
      // Show message for guests trying to access restricted tabs
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please sign in to access this feature'),
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }
    setState(() => _selectedIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavBar(
        selectedIndex: _selectedIndex,
        onTabChange: _onTabChange,
        isGuest: widget.isGuest,
      ),
    );
  }
}