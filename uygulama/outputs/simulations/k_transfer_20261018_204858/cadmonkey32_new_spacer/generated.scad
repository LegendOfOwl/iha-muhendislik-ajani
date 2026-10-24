// Cylindrical spacer with 7 mm height, 26 mm outer diameter, 10 mm inner hole
difference() {
    // Main spacer body
    cylinder(h = 7, d = 26, center = true, $fn = 100);
    
    // Central 10 mm hole
    cylinder(h = 7.1, d = 10, center = true, $fn = 100);
}