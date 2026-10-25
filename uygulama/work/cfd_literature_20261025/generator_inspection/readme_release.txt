###############################################################
#
#         Wing-grid generator instruction.
#
# ---------------------------------------------------
#
###############################################################

###############################################################
# Compile the codes by gfortran as below, or ifort, g95, etc.
###############################################################

#------------------------------------------
# compile the HC-family NACA4 grid generation progarm:

  echo "Compiling hcf_wing_v5p0.f90......"
  gfortran -O2 -o hcf_wing       hcf_wing_v5p0.f90

#----------------------------------------------------------------------
# Endianness will be automatically detected, but if you wish,
# you can specify endianness at compilation: e.g., as follows:
#  gfortran -O2 -fconvert=big-endian -o hcf_wing  hcf_wing_v5p0.f90
#     ifort -O2 -convert big_endian  -o hcf_wing  hcf_wing_v5p0.f90
#----------------------------------------------------------------------

#------------------------------------------
# compile the coarsening program:

  echo "Compiling hcf_coarsening_v3p9.f90......"
  gfortran -O2 -o hcf_coarsening  hcf_coarsening_v3p9.f90

#----------------------------------------------------------------------
# Endianness will be automatically detected, but if you wish,
# you can specify endianness at compilation: e.g., as follows:
#  gfortran -O2 -fconvert=big-endian -o hcf_coarsening  hcf_coarsening_v3p9.f90
#     ifort -O2 -convert big_endian  -o hcf_coarsening  hcf_coarsening_v3p9.f90
#----------------------------------------------------------------------

###############################################################
# To generate structured grids
###############################################################

#--------------------------------------------------
# Step 1: Generate a fine structured grid.
#--------------------------------------------------

  cp input.nml_strct  input.nml

  ./hcf_wing

#--------------------------------------------------
# Step 2: Generate coarse grids from the grid just generated.
#--------------------------------------------------

  cp input_coarsen.nml_strct  input_coarsen.nml

  ./hcf_coarsening



###############################################################
# To generate pure tetrahedral grids, repeat with sample
# input files for tests.
###############################################################

#--------------------------------------------------
# Step 1: Generate a fine grid.
#--------------------------------------------------

  cp input.nml_tetra  input.nml

  ./hcf_wing

#--------------------------------------------------
# Step 2: Generate coarse grids from the grid just generated.
#--------------------------------------------------

  cp input_coarsen.nml_tetra  input_coarsen.nml

  ./hcf_coarsening


###############################################################
# To generate a NACA0012 wing with a blunt tip, and then coarse
# grids.
###############################################################

 mkdir naca0012_blunt
 cd    naca0012_blunt

 cp ../input.nml_naca0012_blunt          input.nml
    ../hcf_wing

 cp ../input_coarsen.nml_naca0012_blunt  input_coarsen.nml
    ../hcf_coarsening

 cd ..
 
###############################################################
# To generate a NACA0012 wing with a round tip with an
# equivalent wing-surface grid to that of the blunt version
# above, and then coarse grids.
###############################################################

 mkdir naca0012_round
 cd    naca0012_round

 cp ../input.nml_naca0012_round          input.nml
    ../hcf_wing

 cp ../input_coarsen.nml_naca0012_round  input_coarsen.nml
    ../hcf_coarsening

 cd ..

#######################################################################
#######################################################################
# NOTE:    To convert .ugrid+.mapbc file to a CGNS file.
#
#  Install the CGNS package (see http://cgns.github.io), and use 
#  the utility code 'aflr3_to_cgns': at a terminal (command prompt),
#
#   %$HOME/cgnslib/bin/cgnstools/aflr3_to_cgns xxx.b8.ugrid xxx.cgns
#
#  where $HOME/cgnslib/ is the directory of the CGNS library installed.
#######################################################################
#######################################################################

