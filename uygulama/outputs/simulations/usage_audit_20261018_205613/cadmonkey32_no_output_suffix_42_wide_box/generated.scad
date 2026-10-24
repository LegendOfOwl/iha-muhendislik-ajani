// 72 mm long, 24 mm wide, 5 mm high rectangular solid box
// Centered at origin (0,0,0)

difference() {
    // Main solid box
    cube([72, 24, 5], center = true);
    
    // Optional: small chamfer on top edges for visual clarity
    // (comment out if not desired)
    translate([0, 0, 2.4])
        cube([72, 24, 0.2], center = true);
}