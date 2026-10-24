// Rectangular plate with cylindrical holes
difference() {
    // Main plate
    cube([60, 24, 4], center = true);
    
    // First cylindrical hole along X axis
    translate([0, 0, 0])
        rotate([0, 90, 0])
            cylinder(h = 62, d = 4, center = true);
    
    // Second cylindrical hole along Z axis
    translate([0, 0, 0])
        rotate([90, 0, 0])
            cylinder(h = 24, d = 4, center = true);
}