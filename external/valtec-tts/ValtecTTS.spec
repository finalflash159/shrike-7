# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

datas = [('src', 'src'), ('valtec_tts', 'valtec_tts')]
binaries = []
hiddenimports = ['src', 'src.models.synthesizer', 'src.text.symbols', 'src.vietnamese.text_processor', 'src.vietnamese.phonemizer', 'src.text', 'src.nn.commons', 'src.nn.mel_processing', 'src.utils.helpers', 'valtec_tts', 'infer']

# Collect customtkinter data
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Viphoneme - pure Python package, needs hiddenimports
hiddenimports += ['viphoneme', 'viphoneme.T2IPA', 'viphoneme.syms', 
                  'viphoneme.text2sequence', 'viphoneme.get_english_sym']

# Vinorm - collect data files and add submodules explicitly
vinorm_datas = collect_data_files('vinorm', include_py_files=False)
datas += vinorm_datas
hiddenimports += ['vinorm', 'vinorm.vinorm', 'vinorm.Dict', 'vinorm.Mapping', 
                  'vinorm.RegexRule', 'vinorm.lib']

# Underthesea data files (corpus, models) - NEEDS data files
underthesea_datas = collect_data_files('underthesea', include_py_files=False)
datas += underthesea_datas

# Gruut language data
gruut_en_datas = collect_data_files('gruut_lang_en', include_py_files=False)
datas += gruut_en_datas

# Add all missing hidden imports
hiddenimports += [
    'underthesea', 'underthesea_core', 'viphoneme', 'vinorm',
    'eng_to_ipa', 'g2p_en', 'gruut', 'gruut_ipa', 'gruut_lang_en',
    'cn2an', 'jieba', 'pypinyin', 'jamo', 'num2words', 'inflect',
    'Unidecode', 'anyascii', 'nltk', 'babel', 'dateparser',
    'python_crfsuite', 'jsonlines', 'proces', 'distance',
    'gruut.g2p', 'gruut_ipa', 'gruut_lang_en'
]


a = Analysis(
    ['gui_app_modern.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ValtecTTS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
