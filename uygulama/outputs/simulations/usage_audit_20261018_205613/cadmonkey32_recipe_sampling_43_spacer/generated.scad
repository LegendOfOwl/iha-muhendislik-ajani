// Cylindrical spacer with 6 mm inner hole
difference() {
    cylinder(h = 12, d = 20, center = true);  // main spacer body
    translate([0, 0, 0])                        // central 6 mm bore
        cylinder(h = 13, d = 6, center = true);   // remove material for 6 mm hole
}