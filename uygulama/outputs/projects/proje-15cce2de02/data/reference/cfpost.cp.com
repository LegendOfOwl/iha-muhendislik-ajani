1
grid run.cgd      
solution run.cfl  
units fss  
zone 1                     
subset i 33 337 j 1 k 1 
variables x; Cp scale -1 
 set plot curve 1 line style none
 set plot curve 1 symbol type square
 set plot curve 1 title "Experiment (Cook et al., 1979)"
 set plot curve 2 title "WIND"
genplot output cp.wind.gen 
plot data cp.exp.gen merge cp.wind.gen
quit
