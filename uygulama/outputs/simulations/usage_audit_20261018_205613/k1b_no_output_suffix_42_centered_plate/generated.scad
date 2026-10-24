module rectangular_plate(width, height, depth, center_x, center_y, center_z) {
  difference() {
    cube([width, height, depth]);
    translate([center_x, center_y, center_z]) {
      cylinder(h = 6, r = 8, center = true);
    }
  }
}

rectangular_plate(60, 40, 6, 30, 20, 20);