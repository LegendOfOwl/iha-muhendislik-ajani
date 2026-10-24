// 40 mm long, 30 mm wide, 8 mm high rectangular solid box
// Centered at origin, no holes, all dimensions in mm

difference() {
    // Main solid box
    cube([40, 30, 8], center=true);
    
    // Optional: small cylindrical hole through the length (comment out if not needed)
    // cylinder(h=10, d=4, center=true, $fn=32);
}