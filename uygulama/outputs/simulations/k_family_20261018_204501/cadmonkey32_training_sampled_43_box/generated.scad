// Rectangular solid box with dimensions 40 mm × 30 mm × 8 mm
// Centered at origin (0,0,0)

difference() {
    // Main body of the box – a simple cuboid
    cube([40, 30, 8], center = true);   // [length, width, height] → [40, 30, 8]
}