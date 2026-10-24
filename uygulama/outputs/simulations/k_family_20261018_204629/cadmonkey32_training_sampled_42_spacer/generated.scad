difference() {
    cylinder(h = 12, d = 20, center = true);          // main spacer body
    translate([0, 0, -6])                              // central hole along Z
        cylinder(h = 12, d = 6, center = false);       // through-hole
}