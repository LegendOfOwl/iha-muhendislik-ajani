module rectangular_plate(width, height, depth) {
  difference() {
    cube([width, height, depth]);
    translate([width/4, height/4, depth/4])
    cylinder(h=depth, r=width/4, center=true);
    translate([width/4, height/4, depth/4])
    cylinder(h=depth, r=height/4, center=true);
  }
}

rectangular_plate(54, 36, 4);