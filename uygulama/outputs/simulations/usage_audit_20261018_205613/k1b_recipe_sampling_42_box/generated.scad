module rectangular_box(length, width, height) {
  difference() {
    cube([length, width, height]);
    translate([length/2 - 10, 0, 0]) cube([10, width, height]);
    translate([-length/2 + 10, 0, 0]) cube([10, width, height]);
  }
}

rectangular_box(40, 30, 8);