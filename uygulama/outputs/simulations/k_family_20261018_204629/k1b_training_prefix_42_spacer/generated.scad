// Parameters
height = 12;
outer_diameter = 20;
hole_diameter = 6;
resolution = 36;

// Cylinder
difference() {
  cylinder(h = height, r = outer_diameter / 2, $fn = resolution);
  cylinder(h = height, r = (outer_diameter - hole_diameter) / 2, $fn = resolution);
}