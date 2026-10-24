// Rectangular plate with cylindrical holes
// Dimensions: 60 mm along X, 24 mm along Y, 4 mm thick, centered at origin

// Main plate
difference() {
    // Base rectangular plate
    cube([60, 24, 4], center = true);
    
    // First cylindrical hole along X axis
    translate([0, 0, 0])
        rotate([0, 90, 0])
            cylinder(h = 62, d = 4, center = true);
    
    // Second cylindrical hole along Y axis
    translate([0, 0, 0])
        rotate([90, 0, 0])
            cylinder(h = 24, d = 4, center = true);
}