// Rectangular plate with centered hole
difference() {
    // Main plate body
    cube([54, 36, 4], center = true);
    
    // Cylindrical hole along Z axis
    cylinder(h = 5, d = 6, center = true);
}