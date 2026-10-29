"""Create a source/CMD release, never a claimed Windows EXE."""
from pathlib import Path
import hashlib,json,re,zipfile
root=Path(__file__).resolve().parents[1]
release=root.parent/'georush-release';release.mkdir(exist_ok=True)
files=[]
for p in root.rglob('*'):
 if not p.is_file():continue
 relative=p.relative_to(root)
 if any(x in relative.parts for x in ('.venv','.git','__pycache__','dist','build')):continue
 if p.suffix=='.pyc' or p.name in ('existing_project_before.json','whyilkka_status_before.txt'):continue
 files.append(p)
archive=release/'GeoRush-v1.0-local.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(files):
  assert not re.search(rb'AIza[0-9A-Za-z_-]{35}',p.read_bytes()),p
  z.write(p,'GeoRush-Generator/'+p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for p in files:assert z.read('GeoRush-Generator/'+p.relative_to(root).as_posix())==p.read_bytes(),p
sum=hashlib.sha256(archive.read_bytes()).hexdigest()
(release/'CHECKSUMS.txt').write_text(f'{sum}  {archive.name}\n',encoding='ascii')
(release/'PACKAGE_VALIDATION.json').write_text(json.dumps({'file':str(archive),'bytes':archive.stat().st_size,'sha256':sum,'files':len(files),'crc_pass':True,'source_byte_match':True,'no_existing_program_data':True,'api_key_pattern_scan_pass':True,'windows_exe_included':False},indent=2))
print(archive,archive.stat().st_size,sum,len(files))
