// Rectangular plate with centered hole
difference() {
    cube([40, 30, 8], center = true);  // Main plate body
    rotate([90, 0, 0])                    // Align cylinder along Z axis
        cylinder(h = 50, d = 10, center = true);  // Central hole
}