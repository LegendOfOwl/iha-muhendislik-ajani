difference() {
    // Main plate
    cube([40, 30, 8], center=true);
    
    // Cylindrical hole along Z
    cylinder(h=10, d=10, center=true, $fn=64);
}