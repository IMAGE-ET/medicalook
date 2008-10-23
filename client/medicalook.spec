# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'medicalook.py'],
             pathex=['F:\\client'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          name='medicalook.exe',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='images\\medicalook.ico')
