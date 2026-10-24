module rectangular_plate(width, height, depth, center_x, center_y, center_z) {
  difference() {
    cube([width, height, depth]);
    translate([center_x, center_y, center_z])
    cylinder(h=depth, r=4, $fn=50);
    translate([width - center_x, center_y, center_z])
    cylinder(h=depth, r=4, $fn=50);
  }
}

rectangular_plate(60, 24, 4, 15, 0, 0);