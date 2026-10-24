module rectangular_box(length, width, height) {
  difference() {
    cube([length, width, height]);
    translate([length/4, length/4, height/4]) cube([length/2, width/2, height/2]);
  }
}

rectangular_box(40, 30, 8);