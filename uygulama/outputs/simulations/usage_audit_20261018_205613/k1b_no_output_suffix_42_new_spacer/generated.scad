module cylinder(h, d) {
  cylinder(h = h, d = d);
}

module spacer(height, outer_diameter, inner_diameter, z_offset) {
  difference() {
    cylinder(h = height, d = outer_diameter);
    translate([0, 0, z_offset])
    cylinder(h = height, d = inner_diameter);
  }
}

// Parameters
height = 7;
outer_diameter = 26;
inner_diameter = 10;
z_offset = 0;

// Create the spacer
spacer(height, outer_diameter, inner_diameter, z_offset);