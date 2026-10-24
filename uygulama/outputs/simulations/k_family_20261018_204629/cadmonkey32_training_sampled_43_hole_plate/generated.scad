// Rectangular plate with centered hole
difference() {
    cube([40, 30, 8], center = true);  // Main rectangular plate
    rotate([90, 0, 0])                    // Rotate cylinder to align along Z axis
        cylinder(h = 32, d = 10, center = true); // Cylinder hole aligned with plate thickness (full height)
}