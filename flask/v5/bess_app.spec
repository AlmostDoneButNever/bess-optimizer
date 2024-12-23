# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('scripts', 'scripts'), ('templates', 'templates')],
    hiddenimports=[
        'pkg_resources.py2_warn','pyomo.common.plugins','pyomo.repn.util',
                'pyomo.opt.plugins',
                'pyomo.core.plugins',
                'pyomo.dataportal.plugins',
                'pyomo.duality.plugins',
                'pyomo.checker.plugins',
                'pyomo.repn.plugins',
                'pyomo.pysp.plugins',
                'pyomo.neos.plugins',
                'pyomo.solvers.plugins',
                'pyomo.gdp.plugins',
                'pyomo.mpec.plugins',
                'pyomo.dae.plugins',
                'pyomo.bilevel.plugins',
                'pyomo.scripting.plugins',
                'pyomo.network.plugins',
                'pandas._libs.skiplist',
                'pyomo.contrib.plugins',
                'pyomo.contrib.ampl_function_demo.plugins',
                'pyomo.contrib.appsi.plugins',
                'pyomo.contrib.community_detection.plugins',
                'pyomo.contrib.cp.plugins',
                'pyomo.contrib.example.plugins',
                'pyomo.contrib.fme.plugins',
                'pyomo.contrib.gdp_bounds.plugins',
                'pyomo.contrib.gdpopt.plugins',
                'pyomo.contrib.gjh.plugins',
                'pyomo.contrib.mcpp.plugins',
                'pyomo.contrib.mindtpy.plugins',
                'pyomo.contrib.multistart.plugins',
                'pyomo.contrib.preprocessing.plugins',
                'pyomo.contrib.pynumero.plugins',
                'pyomo.contrib.trustregion.plugins'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
