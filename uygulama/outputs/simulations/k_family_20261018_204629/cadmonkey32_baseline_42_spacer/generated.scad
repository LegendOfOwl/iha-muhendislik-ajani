// Cylindrical spacer with 6 mm hole
difference() {
    // Main spacer body
    cylinder(h = 12, d = 20, center = true);
    
    // Central 6 mm hole
    cylinder(h = 14, d = 6, center = true);
}