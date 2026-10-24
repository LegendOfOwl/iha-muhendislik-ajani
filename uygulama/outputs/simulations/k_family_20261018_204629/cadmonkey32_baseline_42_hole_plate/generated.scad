// 40 mm long, 30 mm wide, 8 mm thick plate with centered hole
difference() {
    // Main plate
    cube([40, 30, 8], center = true);
    
    // Cylindrical hole along Z axis
    cylinder(h = 10, d = 10, center = true, $fn = 50);
}