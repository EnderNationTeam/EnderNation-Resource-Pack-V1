#!/usr/bin/env python3
"""Deterministic Bedrock build from the active Java assets. No Java files are modified.

Compatibility frame conventions compared with the project's earlier Bedrock build,
GeyserMC/Rainbow and AZPixel-Team/Java2Bedrock. This is an independent implementation.
Visual acceptance on a Bedrock client remains mandatory.
"""
from pathlib import Path
import argparse,copy,hashlib,json,math,shutil,struct,zipfile
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
VIEWS=('firstperson_righthand','firstperson_lefthand','thirdperson_righthand','thirdperson_lefthand','head')
GENERATED={'ground':{'translation':[0,2,0],'scale':[.5]*3},'head':{'rotation':[0,180,0],'translation':[0,13,7]},
 'thirdperson_righthand':{'translation':[0,3,1],'scale':[.55]*3},
 'firstperson_righthand':{'rotation':[0,-90,25],'translation':[1.13,3.2,1.13],'scale':[.68]*3}}
HANDHELD={'thirdperson_righthand':{'rotation':[0,-90,55],'translation':[0,4,.5],'scale':[.85]*3},
 'thirdperson_lefthand':{'rotation':[0,90,-55],'translation':[0,4,.5],'scale':[.85]*3},
 'firstperson_righthand':{'rotation':[0,-90,25],'translation':[1.13,3.2,1.13],'scale':[.68]*3},
 'firstperson_lefthand':{'rotation':[0,90,-25],'translation':[1.13,3.2,1.13],'scale':[.68]*3}}
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def asset(ref,kind):
 ns,rel=ref.split(':',1) if ':' in ref else ('minecraft',ref)
 return ROOT/'assets'/ns/kind/(rel+('.png' if kind=='textures' else '.json'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def model(ref,chain=()):
 if ref in chain:raise ValueError('Cyclic model parent '+ref)
 d=read(asset(ref,'models'));parent=d.get('parent','')
 base={}
 if parent in ('item/generated','minecraft:item/generated','item/handheld','minecraft:item/handheld'):
  base={'display':copy.deepcopy(GENERATED),'generated':True}
  if 'handheld' in parent:base['display'].update(copy.deepcopy(HANDHELD))
 elif parent:base=model(parent,chain+(ref,))
 for key,value in d.items():
  if key in ('textures','display'):base[key]={**base.get(key,{}),**value}
  else:base[key]=value
 return base
def transform(d,view):
 source=d.get('display',{});v=source.get(view)
 if v is None and 'lefthand' in view:v=source.get(view.replace('lefthand','righthand'))
 v=v or {}
 return {k:v.get(k,default) for k,default in [('rotation',[0,0,0]),('translation',[0,0,0]),('scale',[1,1,1])]}
def animations(key,d):
 result={}
 for view in VIEWS:
  t=transform(d,view);rx,ry,rz=t['rotation'];x,y,z=t['translation'];scale=t['scale']
  first=view.startswith('first');left=view.endswith('lefthand');head=view=='head'
  frame={'rotation':[90,60,-40],'position':[4,10,4],'scale':1.5} if first else {'rotation':[90,0,0],'position':[0,13,-3],'scale':1}
  position=[x if left else -x,y,-z if first else z]
  if head:
   frame={'rotation':[0,0,0],'position':[0,19.9,0],'scale':1}
   position=[-.625*x,.625*y,.625*z];scale=[n*.625 for n in scale]
  result['animation.endernation.'+key+'.'+view]={'loop':True,'bones':{
   'anchor':frame,'display_x':{'rotation':[-rx,0,0],'position':position,'scale':scale},
   'display_y':{'rotation':[0,-ry,0]},'display_z':{'rotation':[0,0,rz]}}}
 result['animation.endernation.'+key+'.hide_head']={'loop':True,'bones':{'anchor':{'scale':0}}}
 return {'format_version':'1.8.0','animations':result}
def texture_ref(d,label):
 seen=set()
 while label.startswith('#'):
  if label in seen:raise ValueError('Cyclic texture '+label)
  seen.add(label);label=d['textures'][label[1:]]
 return label

def elements(d):
 if d.get('elements'):return copy.deepcopy(d['elements'])
 # Vanilla generated/handheld utilities: keep silhouette and one-pixel thickness.
 path=asset(texture_ref(d,'#layer0'),'textures');image=Image.open(path).convert('RGBA');w,h=image.size
 result=[]
 for y in range(h):
  for x in range(w):
   if image.getpixel((x,y))[3]<128:continue
   uv=[16*x/w,16*y/h,16*(x+1)/w,16*(y+1)/h]
   result.append({'from':[16*x/w,16*(h-y-1)/h,7.5],'to':[16*(x+1)/w,16*(h-y)/h,8.5],
    'faces':{face:{'uv':uv,'texture':'#layer0'} for face in ['north','south','east','west','up','down']}})
 return result

def geometry(key,d,items,output):
 refs=sorted({texture_ref(d,f['texture']) for e in items for f in e['faces'].values()})
 images={r:Image.open(asset(r,'textures')).convert('RGBA') for r in refs}
 # A single atlas per model also supports future models containing multiple textures.
 width=1;needed=sum(im.width for im in images.values());height=1
 while width<needed:width*=2
 while height<max(im.height for im in images.values()):height*=2
 atlas=Image.new('RGBA',(width,height));offset={};x=0
 for ref,im in images.items():atlas.paste(im,(x,0));offset[ref]=(x,0,im.width,im.height);x+=im.width
 tex='textures/endernation/generated/'+key
 (output/tex).parent.mkdir(parents=True,exist_ok=True);atlas.save(output/(tex+'.png'))
 bones=[{'name':'anchor','binding':"c.item_slot == 'head' ? 'head' : q.item_slot_to_bone_name(c.item_slot)",'pivot':[0,8,0]},
  {'name':'display_x','parent':'anchor','pivot':[0,8,0]},
  {'name':'display_y','parent':'display_x','pivot':[0,8,0]},
  {'name':'display_z','parent':'display_y','pivot':[0,8,0],'cubes':[]}]
 for i,e in enumerate(items):
  a,b=e['from'],e['to'];lo=[min(a[j],b[j]) for j in range(3)];hi=[max(a[j],b[j]) for j in range(3)]
  cube={'origin':[8-hi[0],lo[1],lo[2]-8],'size':[hi[j]-lo[j] for j in range(3)],'uv':{}}
  for face,f in e['faces'].items():
   if f.get('rotation',0)!=0:raise ValueError('Unsupported face UV rotation; never silently ignore it')
   u1,v1,u2,v2=f['uv'];ox,oy,w,h=offset[texture_ref(d,f['texture'])]
   if face in ('up','down'):u1,u2,v1,v2=u2,u1,v2,v1
   cube['uv'][face]={'uv':[ox+u1*w/16,oy+v1*h/16],'uv_size':[(u2-u1)*w/16,(v2-v1)*h/16]}
  rotation=e.get('rotation',{});angle=rotation.get('angle',0)
  if angle:
   if rotation.get('rescale',False):raise ValueError('Rescale must be baked explicitly')
   px,py,pz=rotation.get('origin',[8,8,8]);axis=rotation['axis'];angles=[0,0,0]
   angles['xyz'.index(axis)]=angle*(-1 if axis in 'xy' else 1)
   bones.append({'name':'element_'+str(i),'parent':'display_z','pivot':[8-px,py,pz-8],
    'rotation':angles,'cubes':[cube]})
  else:bones[3]['cubes'].append(cube)
 doc={'format_version':'1.16.0','minecraft:geometry':[{'description':{'identifier':'geometry.endernation.'+key,
  'texture_width':width,'texture_height':height,'visible_bounds_width':8,'visible_bounds_height':8,'visible_bounds_offset':[0,1,0]},'bones':bones}]}
 return doc,tex

def rotation_matrix(degrees):
 x,y,z=[math.radians(v) for v in degrees];cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
 return np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
FACES={'north':([0,1,0],[1,1,0],[1,0,0],[0,0,0]),'south':([1,1,1],[0,1,1],[0,0,1],[1,0,1]),
 'east':([1,1,0],[1,1,1],[1,0,1],[1,0,0]),'west':([0,1,1],[0,1,0],[0,0,0],[0,0,1]),
 'up':([0,1,1],[1,1,1],[1,1,0],[0,1,0]),'down':([0,0,0],[1,0,0],[1,0,1],[0,0,1])}
def render_icon(d,items,size=64):
 # Offline orthographic GUI preview, not a claim about Bedrock client rendering.
 pixels=np.zeros((size,size,4),dtype=np.uint8);depth=np.full((size,size),-np.inf)
 gui=transform(d,'gui');matrix=rotation_matrix(gui['rotation']);scale=np.array(gui['scale']);move=np.array(gui['translation'])
 cache={};quads=[]
 for e in items:
  lo=np.array(e['from'],float);hi=np.array(e['to'],float);r=e.get('rotation',{});angle=r.get('angle',0)
  er=[0,0,0]
  if angle:er['xyz'.index(r['axis'])]=angle
  em=rotation_matrix(er);pivot=np.array(r.get('origin',[8,8,8]),float)
  for face,f in e['faces'].items():
   points=lo+(hi-lo)*np.array(FACES[face],float)
   points=(points-pivot)@em.T+pivot;points=((points-8)*scale)@matrix.T+move
   points[:,0]=size/2+points[:,0]*(size/16);points[:,1]=size/2-points[:,1]*(size/16)
   tex=texture_ref(d,f['texture'])
   if tex not in cache:cache[tex]=np.array(Image.open(asset(tex,'textures')).convert('RGBA'))
   u1,v1,u2,v2=f['uv'];uv=np.array([[u1,v1],[u2,v1],[u2,v2],[u1,v2]],float)
   for tri in [(0,1,2),(0,2,3)]:
    v=points[list(tri)];t=uv[list(tri)];a=v[1,:2]-v[0,:2];b=v[2,:2]-v[0,:2];area=a[0]*b[1]-a[1]*b[0]
    if abs(area)<1e-8:continue
    x0=max(0,math.floor(v[:,0].min()));x1=min(size-1,math.ceil(v[:,0].max()));y0=max(0,math.floor(v[:,1].min()));y1=min(size-1,math.ceil(v[:,1].max()))
    if x0>x1 or y0>y1:continue
    xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
    w0=((v[1,0]-xx)*(v[2,1]-yy)-(v[1,1]-yy)*(v[2,0]-xx))/area
    w1=((v[2,0]-xx)*(v[0,1]-yy)-(v[2,1]-yy)*(v[0,0]-xx))/area;w2=1-w0-w1
    z=w0*v[0,2]+w1*v[1,2]+w2*v[2,2];tu=w0*t[0,0]+w1*t[1,0]+w2*t[2,0];tv=w0*t[0,1]+w1*t[1,1]+w2*t[2,1]
    im=cache[tex];iy=np.clip((tv*im.shape[0]/16).astype(int),0,im.shape[0]-1);ix=np.clip((tu*im.shape[1]/16).astype(int),0,im.shape[1]-1);color=im[iy,ix]
    mask=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)&(z>depth[y0:y1+1,x0:x1+1])&(color[:,:,3]>0)
    pixels[y0:y1+1,x0:x1+1][mask]=color[mask];depth[y0:y1+1,x0:x1+1][mask]=z[mask]
 return Image.fromarray(pixels)

def attachable(identifier,key,tex):
 names={v:'animation.endernation.'+key+'.'+v for v in VIEWS};names['hide_head']='animation.endernation.'+key+'.hide_head'
 conditions={v:("c.is_first_person" if v.startswith('first') else "!c.is_first_person")+" && c.item_slot == '"+('off_hand' if v.endswith('lefthand') else 'main_hand')+"'" for v in VIEWS if v!='head'}
 conditions['head']="!c.is_first_person && c.item_slot == 'head'";conditions['hide_head']="c.is_first_person && c.item_slot == 'head'"
 return {'format_version':'1.10.0','minecraft:attachable':{'description':{'identifier':identifier,
  'materials':{'default':'entity_alphatest_one_sided','enchanted':'entity_alphatest_glint'},
  'textures':{'default':tex,'enchanted':'textures/misc/enchanted_item_glint'},
  'geometry':{'default':'geometry.endernation.'+key},'animations':names,
  'scripts':{'animate':[{v:condition} for v,condition in conditions.items()]},'render_controllers':['controller.render.item_default']}}}

def sounds(output):
 definitions={};count=0
 for source in (ROOT/'assets').glob('*/sounds.json'):
  ns=source.parent.name
  for key,entry in read(source).items():
   entries=[]
   for sound in entry.get('sounds',[]):
    value={'name':sound} if isinstance(sound,str) else copy.deepcopy(sound)
    if value.get('type','file')!='file':continue
    name=value['name'];sns,rel=name.split(':',1) if ':' in name else (ns,name)
    file=ROOT/'assets'/sns/'sounds'/(rel+'.ogg')
    if not file.exists():raise ValueError('Missing sound '+str(file))
    dest=output/'sounds'/sns/(rel+'.ogg');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
    value['name']='sounds/'+sns+'/'+rel;value.pop('type',None);entries.append(value);count+=1
   definitions[ns+':'+key]={'category':'neutral','sounds':entries}
   if ns=='minecraft':definitions[key]=definitions[ns+':'+key]
 write(output/'sounds/sound_definitions.json',{'format_version':'1.14.0','sound_definitions':definitions})
 return count

def glyphs(output):
 pages={};count=0;cell=128
 for provider in read(ROOT/'assets/minecraft/font/default.json')['providers']:
  if provider.get('type')!='bitmap':continue
  ref=provider['file'];source=asset(ref,'textures') if ':' in ref else ROOT/'assets/minecraft/textures'/(ref if ref.endswith('.png') else ref+'.png')
  # Font references already contain the extension.
  if not source.exists() and source.suffix=='.png':source=Path(str(source).replace('.png.png','.png'))
  if not source.exists():raise ValueError('Missing font '+str(source))
  image=Image.open(source).convert('RGBA');rows=provider['chars'];cols=len(rows[0]);cw=image.width/cols;ch=image.height/len(rows)
  for row,line in enumerate(rows):
   for col,char in enumerate(line):
    cp=ord(char)
    if cp==0 or not 0xE000<=cp<=0xF8FF:continue
    sprite=image.crop((round(col*cw),round(row*ch),round((col+1)*cw),round((row+1)*ch)))
    bounds=sprite.getbbox()
    if not bounds:continue
    sprite=sprite.crop(bounds);factor=min(cell/sprite.width,cell/sprite.height)
    sprite=sprite.resize((max(1,round(sprite.width*factor)),max(1,round(sprite.height*factor))),Image.Resampling.NEAREST)
    page=pages.setdefault(cp>>8,Image.new('RGBA',(cell*16,cell*16)));x=(cp&15)*cell;y=((cp&255)>>4)*cell
    page.paste(sprite,(x,y+cell-sprite.height));count+=1
 for number,page in pages.items():
  p=output/'font'/('glyph_'+format(number,'02X')+'.png');p.parent.mkdir(exist_ok=True);page.save(p)
 return count

def pack_zip(source,target,files=None):
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(files or source.rglob('*')):
   if p.is_file():
    info=zipfile.ZipInfo(p.relative_to(source).as_posix(),(2026,10,16,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
    z.writestr(info,p.read_bytes())

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'dist/bedrock-compat-20261016');args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 output=ROOT/'bedrock';mapping={};icons={'resource_pack_name':'endernation','texture_name':'atlas.items','texture_data':{}};report={'items':[],'java_assets_changed':['assets/enderguns/models/ammo/rocket_launcher_ammo.json: corrected missing texture namespace'],'client_acceptance':'pending'}
 registry=read(ROOT/'geysermc/cmd_registry.json');entries=[]
 for base,values in registry.items():
  for cmd,key in values.items():entries.append((base,float(cmd),key,'enderguns:'+key))
 entries.append(('minecraft:paper',None,'trash_bin','endernation:trash_bin'))
 for base,cmd,key,item_model in entries:
  has_model=asset(item_model,'items').exists()
  definition=read(asset(item_model if has_model else base,'items'))['model']
  if definition.get('type','').endswith('range_dispatch'):
   eligible=[v for v in definition['entries'] if float(v['threshold'])<=cmd]
   definition=max(eligible,key=lambda v:float(v['threshold']))['model']
  ref=definition['model'];d=model(ref);items=elements(d)
  geo,tex=geometry(key,d,items,output);write(output/'models/entity/endernation/generated'/(key+'.geo.json'),geo)
  write(output/'animations/endernation'/(key+'.animation.json'),animations(key,d))
  icon='eg_'+key;iconpath=output/'textures/endernation/icons'/(key+'.png');iconpath.parent.mkdir(parents=True,exist_ok=True)
  if d.get('generated'):Image.open(asset(texture_ref(d,'#layer0'),'textures')).save(iconpath)
  else:render_icon(d,items).save(iconpath)
  icons['texture_data'][icon]={'textures':'textures/endernation/icons/'+key}
  options={'icon':icon,'allow_offhand':True,'display_handheld':False}
  ids=[]
  if cmd is not None:
   identifier='geyser_custom:eg_'+key;ids.append(identifier)
   mapping.setdefault(base,[]).append({'type':'legacy','custom_model_data':cmd,'bedrock_identifier':identifier,'bedrock_options':options})
  if has_model:
   identifier='endernation:'+key;ids.append(identifier)
   mapping.setdefault(base,[]).append({'type':'definition','model':item_model,'bedrock_identifier':identifier,'bedrock_options':options})
  for identifier in ids:
   path=output/'attachables/endernation/items'/((('eg_'+key) if identifier.startswith('geyser_custom:') else key+'_model')+'.attachable.json')
   write(path,attachable(identifier,key,tex))
  report['items'].append({'name':key,'base':base,'cmd':cmd,'item_model':item_model if has_model else None,'source_model':ref,'source_sha256':digest(asset(ref,'models')),
   'java_elements':len(d.get('elements',[])),'bedrock_cubes':len(items),'generated_sprite':bool(d.get('generated')),
   'views':{v:transform(d,v) for v in VIEWS},'identifiers':ids})
 write(output/'textures/item_texture.json',icons);write(ROOT/'geysermc/geyser_mappings.json',{'format_version':2,'items':mapping})
 manifest=read(output/'manifest.json');manifest['header']['version']=[1,21,12]
 for module in manifest['modules']:module['version']=[1,21,12]
 write(output/'manifest.json',manifest)
 report['sounds']=sounds(output);report['glyphs']=glyphs(output)
 report['geometry_count']=len(entries);report['mapping_definitions']=sum(len(v) for v in mapping.values())
 # Old flat geometry and textures remain as a reversible reference, but no active attachable uses them.
 pack_zip(output,args.output/'EnderNation-Bedrock-26.3.mcpack')
 pack_zip(ROOT/'geysermc',args.output/'EnderNation-Geyser-Mappings-26.3.zip',[ROOT/'geysermc/geyser_mappings.json'])
 report['artifacts']={p.name:{'sha256':digest(p),'size':p.stat().st_size} for p in args.output.glob('*') if p.is_file() and p.suffix in ('.mcpack','.zip')}
 write(args.output/'build-report.json',report)
 print(json.dumps({'status':'built_not_client_verified','models':len(entries),'definitions':report['mapping_definitions'],'sounds':report['sounds'],'glyphs':report['glyphs'],'output':str(args.output)},indent=2))
if __name__=='__main__':main()
