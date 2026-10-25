from common import ROOT,BASE,PROJECT,read,save,sha,now

path=ROOT/'work/setup/tmr_m6_install.json';m=read(path)
family=PROJECT/'reports/tmr_mesh_family_20261025.json';mesh=read(family)
assert len(mesh['levels'])==3 and all(x['mesh_screens_passed'] for x in mesh['levels'])
m.update(runtime_mesh_verified=True,coarsener_runtime_verified=True,last_test_utc=now(),test_report=str(family.relative_to(ROOT)),
         test_report_sha256=sha(family),source_geometry='Official TMR normalized sharp-TE M6; no arbitrary-CAD mesher',
         physical_qualification_passed=False,limits=['Hex Jacobian sampled at27 points; no global proof.',
         'Source radial BL tag is not a flow-derived delta99.', 'Three generated levels are not three converged CFD solutions.',
         'Only source M6 family tested; global PATH not modified.'])
save(path,m)
config_path=ROOT/'work/setup/tool_config.json';config=read(config_path)
config['tmr_m6_grid_generator']={'version':'HCF wing5.0/coarsener3.9','manifest':str(path.relative_to(ROOT)),
    'executables':m['executables'],'process_PATH_prefix':m['process_PATH_prefix'],'runtime_verified':True,
    'source_geometry':'TMR normalized sharp-TE M6 only','physical_qualification_passed':False,'system_PATH_changed':False}
save(config_path,config)
print('Portable source mesh tool registered; flow qualification remains false')
