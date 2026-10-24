// Rectangular Solid Box with dimensions 40mm x 30mm x 8mm
module solid_box() {
    cube([40, 30, 8], center = true);
}

// Render the box centered at origin
solid_box();