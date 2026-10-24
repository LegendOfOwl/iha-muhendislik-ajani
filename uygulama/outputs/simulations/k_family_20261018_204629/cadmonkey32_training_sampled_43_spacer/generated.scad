difference() {
    cylinder(h = 12, d = 20, center = true);
    translate([0, 0, 0])
        cylinder(h = 14, d = 6, center = true);  // slightly taller to ensure hole cuts through all layers
}