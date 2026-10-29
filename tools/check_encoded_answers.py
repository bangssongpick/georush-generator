from pathlib import Path
import json
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1]
records=[]
for folder in sorted((root/'samples/GeoRush_Output').glob('GeoRush_*')):
 quiz=json.loads((folder/'quiz_data.json').read_text())
 for i,q in enumerate(quiz['questions'],1):
  image=np.asarray(Image.open(folder/f'encoded_inspection/q{i}_answer.jpg').convert('RGB'),dtype=np.int16)
  counts=[]
  for option in range(4):
   x=76+option%2*480;y=1255+option//2*178
   pixels=image[y:y+147,x:x+449]
   mask=(pixels[:,:,1]>pixels[:,:,0]+60)&(pixels[:,:,1]>pixels[:,:,2]+25)&(pixels[:,:,1]>140)
   counts.append(int(mask.sum()))
  winners=[j for j,v in enumerate(counts) if v>1000]
  assert winners==[q['correct_index']],(q,counts)
  records.append({'folder':folder.name,'question':i,'country':q['country_name'],'green_option_pixel_counts':counts,'correct_index':q['correct_index']})
report=root/'reports/ENCODED_ANSWER_CHECK.json'
report.write_text(json.dumps({'checks_passed':len(records),'records':records},ensure_ascii=False,indent=2))
print('Encoded answer highlight checks:',len(records),'PASS')
