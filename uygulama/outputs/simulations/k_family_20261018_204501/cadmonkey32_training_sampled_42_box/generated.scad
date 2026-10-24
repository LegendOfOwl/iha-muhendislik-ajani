// Rectangular Solid Box with Dimensions 40mm x 30mm x 8mm
// Centered at origin for easy placement

difference() {
    // Main box body - centered in X and Y axes
    cube([40, 30, 8], center = true);
}