// Rectangular plate with centered hole
difference() {
    // Base rectangular plate
    cube([40, 30, 8], center = true);
    
    // Cylindrical hole along Z-axis
    cylinder(h = 12, d = 10, center = true, $fn = 64);
}