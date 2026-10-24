module rectangular_plate(length, width, thickness) {
    difference() {
        cube([length, width, thickness]);
        translate([length/2 - 5, width/2 - 5, 0])
            cylinder(h=thickness, r=5);
    }
}

rectangular_plate(40, 30, 8);