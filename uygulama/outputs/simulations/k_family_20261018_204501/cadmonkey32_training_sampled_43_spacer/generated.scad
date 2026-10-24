// Cylindrical spacer with 6 mm inner hole
difference() {
    cylinder(h = 12, d = 20, center = true);  // outer body
    cylinder(h = 14, d = 6, center = true);   // through-hole (slightly taller to ensure clean subtraction)
}