// 19 mm long, 17 mm wide, 11 mm high rectangular solid box
// Centered at origin (0,0,0)

difference() {
    // Main solid box
    cube([19, 17, 11], center = true);
    
    // Optional: small chamfer on top edges for visual clarity
    // (comment out if not desired)
    translate([0, 0, 5.5])
        cube([19.2, 17.2, 1], center = true);
}