difference() {
    // Main solid box
    cube([40, 30, 8], center=true);
    
    // Optional: small chamfer on top edges for visual clarity
    translate([0, 0, 4])
        cube([40.2, 30.2, 0.2], center=true);
}