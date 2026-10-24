// Cylindrical spacer with 10 mm hole along Z
// Outer diameter 26 mm, inner hole 10 mm, height 7 mm

difference() {
    // Main spacer body
    cylinder(h = 7, d = 26, center = true, $fn = 100);
    
    // Central 10 mm hole along Z axis
    cylinder(h = 10, d = 10, center = true, $fn = 100);
}