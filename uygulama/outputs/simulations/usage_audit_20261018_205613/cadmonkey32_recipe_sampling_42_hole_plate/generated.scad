// Rectangular plate with centered hole
difference() {
    // Base plate (length = 40, width = 30, height = 8)
    cube([40, 30, 8], center=true);
    
    // Cylindrical hole running along Z axis
    cylinder(h=12, d=10, center=true, $fn=64);
}