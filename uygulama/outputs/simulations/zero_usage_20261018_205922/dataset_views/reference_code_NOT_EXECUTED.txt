import cadquery as cq

cap_height = 30.0
cap_radius = 40.0
cap_thickness = 12.0
arc_control_x = cap_radius + 12.0
arc_control_y = cap_height + 5.0
hole_diameter = 8.0
fillet_radius = 2.0

profile = (
    cq.Workplane("XY")
    .moveTo(0, 0)
    .lineTo(cap_radius, 0)
    .lineTo(cap_radius, cap_height - 6)
    .threePointArc((arc_control_x, arc_control_y), (0, cap_height))
    .close()
)

solid = profile.extrude(cap_thickness)

solid = (
    solid.faces(">Z")
    .workplane()
    .center(0, cap_height / 2)
    .hole(hole_diameter, depth=cap_thickness + 1)
)

result = solid.edges("|Z").fillet(fillet_radius)
