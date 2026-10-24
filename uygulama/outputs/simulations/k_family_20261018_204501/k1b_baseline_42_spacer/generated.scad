difference() {
  cylinder(h = 12, r = 20, center = false);
  cylinder(h = 12, r = 20 - 2, center = false);
  translate([0,0,-0.1])
  cylinder(h = 12, r = 6, center = false);
}