// Simple 3D cat model
// Body
color("gray")
difference() {
    sphere([0, 0, 0], 20);
    translate([0, 0, -20])
        cube([40, 40, 20], center = true);
}

// Head
color("gray")
translate([0, 0, 25])
    sphere([0, 0, 0], 15);

// Ears
color("gray")
translate([-8, 0, 30])
    rotate([0, 30, 0])
    cylinder(h = 12, r1 = 5, r2 = 0);
translate([8, 0, 30])
    rotate([0, -30, 0])
    cylinder(h = 12, r1 = 5, r2 = 0);

// Eyes
color("black")
translate([-6, 10, 27])
    sphere([0, 0, 0], 2);
translate([6, 10, 27])
    sphere([0, 0, 0], 2);

// Nose
color("pink")
translate([0, 12, 25])
    sphere([0, 0, 0], 3);

// Whiskers
color("black")
translate([-10, 12, 25])
    rotate([0, 0, -20])
    cylinder(h = 10, r = 0.5);
translate([10, 12, 25])
    rotate([0, 0, 20])
    cylinder(h = 10, r = 0.5);

// Legs
color("gray")
translate([-10, 0, -10])
    cylinder(h = 20, r = 4);
translate([10, 0, -10])
    cylinder(h = 20, r = 4);
translate([-10, 0, 10])
    cylinder(h = 20, r = 4);
translate([10, 0, 10])
    cylinder(h = 20, r = 4);

// Tail
color("gray")
translate([0, -20, -5])
    rotate([0, 45, 0])
    cylinder(h = 20, r1 = 4, r2 = 2);