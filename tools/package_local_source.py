"""Build standalone source ZIP; no hosting/API/Actions calls."""
from pathlib import Path
import zipfile, hashlib, json, re, tempfile
ROOT=Path(__file__).resolve().parents[1]
DEST=Path('/tmp/GeoRush-v1.0-Windows-Source.zip')
entries={}
for folder in ('georush','assets','tests','tools'):
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':entries[p.relative_to(ROOT).as_posix()]=p
for name in ('main.py','START_HERE.cmd','INSTALL.cmd','BUILD_EXE.cmd','requirements.txt','requirements-build.txt','README.md','WINDOWS_처음시작.md','THIRD_PARTY_NOTICES.md','LICENSE','TEST_REPORT_KO.md'):
 entries[name]=ROOT/name
for name in ('local_distribution_tests.log','local_source_gui_check.json','LOCAL_RESOURCE_VALIDATION.json','ACTUAL_SAMPLE_QA.json','ENCODED_ANSWER_CHECK.json','EXISTING_PROJECT_PROTECTION.json'):
 entries['reports/'+name]=ROOT/'reports'/name
for index,folder in enumerate(sorted((ROOT/'samples/GeoRush_Output').glob('GeoRush_*')),1):
 for name in ('video.mp4','title.txt','description.txt','tags.txt','pinned_comment.txt','quiz_data.json','MEDIA_REPORT.json','RENDER_REPORT.json','REVIEW_CONTACT_SHEET.jpg'):
  entries[f'samples/sample_{index:02d}/'+name]=folder/name
 for p in (folder/'encoded_inspection').glob('*.jpg'):
  entries[f'samples/sample_{index:02d}/encoded_inspection/'+p.name]=p
for name,p in entries.items():
 assert p.is_file(),p
 assert not re.search(rb'AIza[0-9A-Za-z_-]{35}',p.read_bytes()),name
with zipfile.ZipFile(DEST,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name,p in sorted(entries.items()):z.write(p,'GeoRush-Generator/'+name)
with zipfile.ZipFile(DEST) as z:
 assert z.testzip() is None
 for name,p in entries.items():assert z.read('GeoRush-Generator/'+name)==p.read_bytes()
 extract=Path(tempfile.mkdtemp(prefix='GeoRush_LocalSource_Zip_Check_'));z.extractall(extract)
summary={'zip':str(DEST),'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'bytes':DEST.stat().st_size,'files':len(entries),'crc':'PASS','source_match':'PASS','windows_exe_included':False,'needs_python_for_source':True,'actions_required':False,'windows_verified':False}
summary['extracted_source']=str(extract/'GeoRush-Generator')
(ROOT/'reports/LOCAL_SOURCE_PACKAGE.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
