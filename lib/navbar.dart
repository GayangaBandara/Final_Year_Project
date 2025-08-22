import 'package:flutter/material.dart';
import 'package:line_icons/line_icons.dart';
import 'package:google_nav_bar/google_nav_bar.dart';

class NavBar extends StatelessWidget {
  final int selectedIndex;
  final Function(int) onTabChange;
  final bool isGuest; // Added guest mode parameter

  const NavBar({
    Key? key,
    required this.selectedIndex,
    required this.onTabChange,
    this.isGuest = false, // Default to false
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            blurRadius: 20,
            color: Colors.black.withOpacity(.1),
          ),
        ],
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 15.0, vertical: 8),
          child: GNav(
            rippleColor: Colors.grey[300]!,
            hoverColor: Colors.grey[100]!,
            gap: 8,
            activeColor: Colors.black,
            iconSize: 24,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            duration: const Duration(milliseconds: 400),
            tabBackgroundColor: const Color.fromARGB(255, 119, 238, 152)!,
            color: Colors.black,
            tabs: [
              const GButton(
                icon: LineIcons.home,
                text: 'Home',
              ),
              const GButton(
                icon: LineIcons.music,
                text: 'Entertainment',
              ),
              GButton(
                icon: LineIcons.stethoscope,
                text: 'Doctors',
                iconColor: isGuest ? Colors.grey : null, // Grey out if guest
                textColor: isGuest ? Colors.grey : null, // Grey out if guest
              ),
              GButton(
                icon: LineIcons.user,
                text: 'Profile',
                iconColor: isGuest ? Colors.grey : null, // Grey out if guest
                textColor: isGuest ? Colors.grey : null, // Grey out if guest
              ),
            ],
            selectedIndex: selectedIndex,
            onTabChange: (index) {
              if (isGuest && (index == 2 || index == 3)) {
                // Show restriction message for guests trying to access Doctors or Profile
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Please sign in to access this feature'),
                    duration: Duration(seconds: 2),
                    behavior: SnackBarBehavior.floating,
                  ),
                );
                return;
              }
              onTabChange(index);
            },
          ),
        ),
      ),
    );
  }
}