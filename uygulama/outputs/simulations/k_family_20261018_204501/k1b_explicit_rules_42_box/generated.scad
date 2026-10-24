module rectangular_box(length, width, height, center_x, center_y, center_z) {
  difference() {
    cube([length, width, height]);
    translate([center_x, center_y, center_z])
    cylinder(h=height, r=diameter/2, $fn=64);
    translate([length - center_x, center_y, center_z])
    cylinder(h=height, r=diameter/2, $fn=64);
    translate([center_x, width - center_y, center_z])
    cylinder(h=height, r=diameter/2, $fn=64);
    translate([length - center_x, width - center_y, center_z])
    cylinder(h=height, r=diameter/2, $fn=64);
  }
}

rectangular_box(40, 30, 8, 10, 10, 10);