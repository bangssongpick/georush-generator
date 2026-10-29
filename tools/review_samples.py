from pathlib import Path
import json, hashlib, math
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from georush.catalog import Catalog
from georush.quiz import validate_quiz
from georush.render import _question_static,_background
root=Path(__file__).resolve().parents[1]
folder=root/'samples/GeoRush_Output'
catalog=Catalog();reports=[];signatures=set();all_codes=[]
font=ImageFont.truetype(str(root/'assets/fonts/DejaVuSans-Bold.ttf'),22)
for i,d in enumerate(sorted(p for p in folder.iterdir() if p.is_dir()),1):
 quiz=json.loads((d/'quiz_data.json').read_text());validate_quiz(quiz,catalog)
 assert quiz['signature'] not in signatures;signatures.add(quiz['signature'])
 row={'sample':i,'folder':str(d),'signature':quiz['signature'],'questions':[]}
 for j,q in enumerate(quiz['questions'],1):
  all_codes.append(q['country_code'])
  expected=np.asarray(_question_static(q,j-1,3,_background()).crop((130,445,950,945)),dtype=float)
  actual=np.asarray(Image.open(d/f'encoded_inspection/q{j}_start.jpg').convert('RGB').crop((130,445,950,945)),dtype=float)
  mse=float(np.mean((expected-actual)**2));psnr=10*math.log10(255**2/max(mse,1e-12))
  assert psnr>29, (d,j,psnr)
  row['questions'].append({'code':q['country_code'],'country':q['country_name'],'answer':q['options'][q['correct_index']], 'answer_letter':chr(65+q['correct_index']),'flag_region_psnr_db':round(psnr,3),'options':q['options']})
 for name in ['title.txt','description.txt','tags.txt','pinned_comment.txt']:
  value=(d/name).read_text(encoding='utf8');assert value.strip();assert all(ord(c)<128 or c.isspace() for c in value)
 title=(d/'title.txt').read_text();assert not any(q['country_name'] in title for q in quiz['questions'])
 files=['q1_start.jpg','q1_countdown.jpg','q1_answer.jpg','cta.jpg']
 sheet=Image.new('RGB',(1080,1990),'#030F25');draw=ImageDraw.Draw(sheet)
 for k,name in enumerate(files):
  image=Image.open(d/'encoded_inspection'/name).convert('RGB').resize((540,960))
  x=(k%2)*540;y=(k//2)*995
  sheet.paste(image,(x,y+35));draw.text((x+15,y+6),f'Sample {i} / {name}',font=font,fill='white')
 sheet.save(d/'REVIEW_CONTACT_SHEET.jpg',quality=92)
 row['media']=json.loads((d/'MEDIA_REPORT.json').read_text());row['sha256']=hashlib.sha256((d/'video.mp4').read_bytes()).hexdigest()
 reports.append(row)
assert len(reports)==3
assert len(all_codes)==len(set(all_codes))==9
(root/'reports/ACTUAL_SAMPLE_QA.json').write_text(json.dumps({'samples':reports,'all_9_countries_distinct':True,'composition_signatures_distinct':len(signatures)==3,'correct_answers_verified_against_pinned_catalog':True,'flags_match_encoded_first_frames':True,'metadata_english_and_no_answer_in_titles':True,'manual_visual_review_pending':True},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([{'sample':x['sample'],'folder':x['folder'],'questions':x['questions']} for x in reports],ensure_ascii=False,indent=2))
