module rectangular_plate(width, height, depth, hole_diameter, hole_x_offset, hole_y_offset) {
  difference() {
    cube([width, height, depth]);
    translate([hole_x_offset, hole_y_offset, -0.1])
    cylinder(h = depth + 0.2, r = hole_diameter / 2, $fn = 50);
    translate([width - hole_x_offset, hole_y_offset, -0.1])
    cylinder(h = depth + 0.2, r = hole_diameter / 2, $fn = 50);
  }
}

rectangular_plate(60, 24, 4, 4, -15, -0);