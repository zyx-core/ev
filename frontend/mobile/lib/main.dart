import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'providers/station_provider.dart';
import 'screens/station_list_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Set system UI overlay style for dark theme
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF0A0E17),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
  
  runApp(const IEVCEcoApp());
}

class IEVCEcoApp extends StatelessWidget {
  const IEVCEcoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => StationProvider()),
      ],
      child: MaterialApp(
        title: 'IEVC-eco',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          brightness: Brightness.dark,
          colorScheme: ColorScheme.dark(
            primary: const Color(0xFF3B82F6),
            secondary: const Color(0xFF8B5CF6),
            surface: const Color(0xFF1F2937),
            background: const Color(0xFF0A0E17),
            error: const Color(0xFFEF4444),
            onPrimary: Colors.white,
            onSecondary: Colors.white,
            onSurface: Colors.white,
            onBackground: Colors.white,
            onError: Colors.white,
          ),
          scaffoldBackgroundColor: const Color(0xFF0A0E17),
          appBarTheme: const AppBarTheme(
            backgroundColor: Color(0xFF111827),
            foregroundColor: Colors.white,
            elevation: 0,
          ),
          cardTheme: CardThemeData(
            color: const Color(0xFF1F2937),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF3B82F6),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
          textTheme: const TextTheme(
            headlineLarge: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
            headlineMedium: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
            bodyLarge: TextStyle(color: Colors.white),
            bodyMedium: TextStyle(color: Colors.white),
          ),
          sliderTheme: SliderThemeData(
            activeTrackColor: const Color(0xFF3B82F6),
            inactiveTrackColor: const Color(0xFF374151),
            thumbColor: const Color(0xFF3B82F6),
            overlayColor: const Color(0xFF3B82F6).withOpacity(0.2),
          ),
          chipTheme: ChipThemeData(
            backgroundColor: const Color(0xFF111827),
            selectedColor: const Color(0xFF3B82F6),
            labelStyle: TextStyle(color: Colors.grey[400]),
            secondaryLabelStyle: const TextStyle(color: Colors.white),
          ),
        ),
        home: const StationListScreen(),
      ),
    );
  }
}
