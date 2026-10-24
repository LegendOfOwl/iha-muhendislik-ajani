module rectangular_plate(width, height, depth) {
  difference() {
    cube([width, height, depth]);
    translate([0, 0, -0.1])
    cylinder(h = depth + 0.1, r = 8, $fn = 50);
  }
}

rectangular_plate(60, 40, 6);