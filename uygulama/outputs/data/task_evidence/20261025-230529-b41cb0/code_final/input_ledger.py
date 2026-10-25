from prepare import ROOT,BASE,CASE,read,save,sha,now

def main():
    items=[]
    def add(name,value,unit,kind,source,limit):items.append({'name':name,'value':value,'unit':unit,'kind':kind,'source':source,'limits_or_uncertainty':limit})
    intro='https://tmbwg.github.io/turbmodels/flatplate.html';inp='https://tmbwg.github.io/turbmodels/FlatPlate/SA/cfl3d_typical.inp'
    add('Mach',.2,'1','kaynaklı',intro,'Prescribed compressible verification condition, not measured uncertainty')
    add('Reynolds per length',5e6,'1/m','kaynaklı',intro,'At x=1m Re_x=5M; wall ends at2m')
    add('Static temperature',300,'K','kaynaklı',inp,'540R converted to300K')
    add('Flow angle',0,'deg','kaynaklı',inp,'Nominal zero incidence')
    add('Reference area',2,'m2','kaynaklı',inp,'2D unit span; wall length2m')
    add('nu_tilde inflow / nu_inf',3,'1','kaynaklı',inp,'tur10=3; not eddy/laminar viscosity ratio')
    add('SA variant','NEGATIVE,WITHFT2','1','kaynaklı','https://tmbwg.github.io/turbmodels/spalart.html','Standard SA-neg recommended; expected same as standard SA for positive states, not universal equivalence')
    add('gamma',1.4,'1','varsayım','Explicit standard-air SU2 configuration','Calorically perfect gas for verification case')
    add('gas constant',287.058,'J/(kg K)','varsayım','Explicit standard-air SU2 configuration','Matches chosen SI gas law; not measured experiment input')
    add('Sutherland mu_ref/T_ref/S',[1.716e-5,273.15,110.4],'Pa s; K; K','varsayım','Explicit conventional SU2 SI Sutherland constants','Full dimensional TMR constant identity is not independently established; no coefficient tuning')
    add('Prandtl laminar/turbulent',[.72,.9],'1','kaynaklı','https://tmbwg.github.io/turbmodels/spalart.html','Default compressible SA perfect-gas heat-transfer convention')
    for name,value in read(CASE/'contract.json')['derived_freestream'].items():
        add(name,value,{'mu_Pa_s':'Pa s','U_m_s':'m/s','rho_kg_m3':'kg/m3','p_Pa':'Pa','inlet_Ttotal_K':'K'}[name],'hesaplanmış','Mach/Re/T and explicit SI gas/viscosity laws','Derived consistently; original rounded tutorial static pressure115056Pa is not silently copied')
    save(ROOT/'outputs/data/qualification/flatplate_SAneg_20261025_v1/input_ledger.json',{'created_utc':now(),'inputs':items,
        'source_manifest_sha256':sha(BASE/'sources/input_sources_manifest.json'),'scope':'Source numerical verification; no experimental inputs or aircraft requirements inferred.'})
    print('Input provenance and limitations recorded')

if __name__=='__main__':main()
