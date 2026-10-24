// Rectangular plate with centered hole
difference() {
    // Main plate body
    cube([60, 40, 6], center = true);
    
    // Cylindrical hole along Z axis
    cylinder(h = 7, d = 8, center = true, $fn = 64);
}