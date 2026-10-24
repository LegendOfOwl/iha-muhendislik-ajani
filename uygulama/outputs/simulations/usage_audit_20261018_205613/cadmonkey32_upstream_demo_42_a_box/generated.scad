// Simple 3D box model
// Dimensions: 60mm x 40mm x 20mm

// Outer box body
difference() {
    // Main box volume
    cube([60, 40, 20], center = true);

    // Hollow out the inside
    translate([0, 0, 1])
        cube([56, 36, 20], center = true);
}

// Optional lid
translate([0, 0, 11])
    cube([60, 40, 2], center = true);