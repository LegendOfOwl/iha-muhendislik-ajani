// Rectangular Plate
module rectangular_plate(length, width, thickness) {
  cube([length, width, thickness]);
}

// Center the plate at the origin
translate([0, 0, 0])
rectangular_plate(40, 30, 8);

// Hole in the center
translate([length/2, width/2, -0.1])
cylinder(h = 10, r = 0.1);