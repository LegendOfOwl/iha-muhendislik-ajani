// Coffee Mug in OpenSCAD

// Parameters
mug_height = 100;
mug_diameter = 80;
handle_height = 50;
handle_width = 25;
handle_depth = 20;
handle_radius = 5;
handle_offset_x = 20;
handle_offset_y = 20;

// Body
module coffee_mug_body() {
  cylinder(h = mug_height - handle_height, r = mug_diameter / 2, center = true);
}

// Handle
module coffee_mug_handle() {
  translate([handle_offset_x, handle_offset_y, 0]) {
    cylinder(h = handle_height, r = handle_radius, center = true);
  }
}

// Coffee Mug
module coffee_mug() {
  difference() {
    coffee_mug_body();
    rotate([0, 0, 90])
    coffee_mug_handle();
  }
}

// Render
coffee_mug();