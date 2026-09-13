# -*- mode: python ; coding: utf-8 -*-
"""
Spec do PyInstaller para o StudySync desktop. Use `desktop\\build.ps1`, que
builda o frontend antes; rodar direto:
    backend\\venv\\Scripts\\pyinstaller.exe desktop\\StudySync.spec
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

ROOT = Path(SPECPATH).parent
BACKEND = ROOT / "backend"
FRONTEND_DIST = ROOT / "frontend" / "dist"

if not (FRONTEND_DIST / "index.html").is_file():
    raise SystemExit("frontend/dist não existe — rode `npm run build` em frontend/ antes.")

# As migrations são carregadas do disco pelo Alembic (não por import), então
# vão como arquivos. O caminho de destino `alembic/` fica ao lado do pacote
# `app/`, exatamente onde `init_db.py` e `env.py` procuram.
alembic_datas = [
    (str(path), str(Path("alembic") / path.parent.relative_to(BACKEND / "alembic")))
    for path in (BACKEND / "alembic").rglob("*")
    if path.is_file() and "__pycache__" not in path.parts
]

a = Analysis(
    [str(ROOT / "desktop" / "launcher.py")],
    pathex=[str(BACKEND)],
    datas=[
        *alembic_datas,
        (str(FRONTEND_DIST), "frontend_dist"),
        # Pacotes que consultam a própria versão via importlib.metadata.
        *copy_metadata("email-validator"),
        *copy_metadata("alembic"),
        *copy_metadata("APScheduler"),
    ],
    hiddenimports=[
        *collect_submodules("app"),
        # O uvicorn escolhe loop/protocolos por nome, em tempo de execução.
        *collect_submodules("uvicorn"),
        *collect_submodules("websockets"),
        # Importados pelos scripts de migration, que o PyInstaller não analisa.
        *collect_submodules("alembic", filter=lambda name: ".testing" not in name),
        "sqlalchemy.dialects.sqlite",
    ],
    excludes=["tkinter", "pytest", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="StudySync",
    console=False,
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="StudySync",
    upx=False,
)
