module rectangular_plate(length, width, thickness) {
    difference() {
        cube([length, width, thickness]);
        translate([length/4, 0, -thickness/2]) cylinder(h=30, r=10);
    }
}

rectangular_plate(40, 30, 8);