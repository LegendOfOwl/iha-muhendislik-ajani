// Rectangular plate with centered hole
difference() {
    cube([40, 30, 8], center = true);  // Main plate body
    rotate([90, 0, 0])                    // Align cylinder vertically (Z)
        cylinder(d = 10, h = 12, center = true, $fn = 50);  // Central hole aligned along X axis
}