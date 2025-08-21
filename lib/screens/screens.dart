import 'profile.dart';
import 'entertainment.dart';
import 'package:flutter/material.dart';
import 'package:safespace/homescreen.dart';
import 'package:safespace/screens/doctor_screen.dart';




// lib/screens/screens.dart

List<Widget> screensWithTheme() => [
  HomeScreen(),
  EntertainmentScreen(),
  DoctorScreen(),
  ProfilePage(),
];
