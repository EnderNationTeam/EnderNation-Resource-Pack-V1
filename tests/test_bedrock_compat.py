"""Server-side contract tests of actual generated resources, using only Python stdlib."""
from pathlib import Path
import hashlib,json,math,struct,unittest,zipfile,zlib
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def asset(ref,kind):
 ns,rel=ref.split(':',1) if ':' in ref else ('minecraft',ref)
 return ROOT/'assets'/ns/kind/(rel+'.json')
REPORT=read(ROOT/'dist/bedrock-compat-20261016/build-report.json')
ITEMS=REPORT['items'];BED=ROOT/'bedrock';MAPPING=read(ROOT/'geysermc/geyser_mappings.json')
def geom(item):return read(BED/'models/entity/endernation/generated'/(item['name']+'.geo.json'))['minecraft:geometry'][0]
def allcubes(item):return [c for b in geom(item)['bones'] for c in b.get('cubes',[])]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def rgba_rows(path):
 # Read the generated 8-bit RGBA PNGs without third-party server dependencies.
 data=path.read_bytes();pos=8;compressed=bytearray()
 while pos<len(data):
  n=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+n];pos+=n+12
  if kind==b'IHDR':w,h,depth,color,_,_,interlace=struct.unpack('>IIBBBBB',body)
  if kind==b'IDAT':compressed.extend(body)
 assert (depth,color,interlace)==(8,6,0)
 raw=zlib.decompress(compressed);stride=w*4;previous=bytearray(stride);rows=[];pos=0
 for _ in range(h):
  method=raw[pos];row=bytearray(raw[pos+1:pos+1+stride]);pos+=stride+1
  for x in range(stride):
   a=row[x-4] if x>=4 else 0;b=previous[x];c=previous[x-4] if x>=4 else 0
   if method==0:predict=0
   elif method==1:predict=a
   elif method==2:predict=b
   elif method==3:predict=(a+b)//2
   elif method==4:
    p=a+b-c;dist=[abs(p-a),abs(p-b),abs(p-c)];predict=[a,b,c][dist.index(min(dist))]
   else:raise AssertionError('Unsupported PNG filter')
   row[x]=(row[x]+predict)&255
  rows.append(row);previous=row
 return w,rows

class BedrockCompatibility(unittest.TestCase):
 def test_exact_current_item_set_and_no_missing_weapon(self):
  self.assertEqual(32,len(ITEMS));self.assertEqual(len(ITEMS),len({i['name'] for i in ITEMS}))
  for key in ['ak_47','striker','p90','m1014','m98b','bullet','trash_bin']:self.assertIn(key,{i['name'] for i in ITEMS})
 def test_java_sources_only_have_the_documented_texture_fix(self):
  lock=read(ROOT/'docs/bedrock-source-lock.json')
  changed=[name for name,old in lock['java_before_sha256'].items() if sha(ROOT/name)!=old]
  self.assertEqual(lock['expected_java_changes'],changed)
 def test_each_geometry_is_derived_from_its_locked_current_java_model(self):
  for i in ITEMS:self.assertEqual(i['source_sha256'],sha(asset(i['source_model'],'models')))
 def test_every_java_cuboid_survives_as_a_real_bedrock_cuboid(self):
  for i in ITEMS:
   cubes=allcubes(i);self.assertEqual(i['bedrock_cubes'],len(cubes),i['name'])
   if i['java_elements']:self.assertEqual(i['java_elements'],len(cubes),i['name'])
   if ':weapon/' in i['source_model']:self.assertGreater(len(cubes),30,i['name'])
 def test_cube_origins_sizes_and_rotation_pivots_preserve_source(self):
  for i in ITEMS:
   source=read(asset(i['source_model'],'models'))
   if not source.get('elements'):continue
   by_origin={(tuple(c['origin']),tuple(c['size'])) for c in allcubes(i)}
   for e in source['elements']:
    a,b=e['from'],e['to'];lo=[min(a[k],b[k]) for k in range(3)];hi=[max(a[k],b[k]) for k in range(3)]
    self.assertIn(((8-hi[0],lo[1],lo[2]-8),tuple(hi[k]-lo[k] for k in range(3))),by_origin)
   bones=geom(i)['bones']
   for index,e in enumerate(source['elements']):
    r=e.get('rotation',{});angle=r.get('angle',0)
    if not angle:continue
    bone=next(b for b in bones if b['name']=='element_'+str(index))
    px,py,pz=r['origin'];self.assertEqual([8-px,py,pz-8],bone['pivot'])
    self.assertEqual(angle*(-1 if r['axis'] in 'xy' else 1),bone['rotation']['xyz'.index(r['axis'])])
 def test_all_mapping_ids_are_unique_and_cover_both_item_protocols(self):
  definitions=[v for group in MAPPING['items'].values() for v in group];ids=[v['bedrock_identifier'] for v in definitions]
  self.assertEqual(2,MAPPING['format_version']);self.assertEqual(62,len(ids));self.assertEqual(len(ids),len(set(ids)))
  for i in ITEMS:
   actual=[v for v in MAPPING['items'][i['base']] if v['bedrock_identifier'] in i['identifiers']]
   if i['cmd'] is not None:self.assertTrue(any(v['type']=='legacy' and v['custom_model_data']==i['cmd'] for v in actual))
   if i['item_model']:self.assertTrue(any(v['type']=='definition' and v['model']==i['item_model'] for v in actual))
 def test_every_active_mapping_has_an_attachable(self):
  attachables={read(p)['minecraft:attachable']['description']['identifier']:read(p)['minecraft:attachable']['description'] for p in (BED/'attachables').rglob('*.json')}
  for i in ITEMS:
   for identifier in i['identifiers']:
    a=attachables[identifier];self.assertEqual('geometry.endernation.'+i['name'],a['geometry']['default'])
    self.assertNotIn('flat_item',a['geometry']['default']);self.assertTrue((BED/(a['textures']['default']+'.png')).exists())
 def test_icon_references_resolve_and_pngs_are_nonempty(self):
  atlas=read(BED/'textures/item_texture.json')['texture_data']
  for group in MAPPING['items'].values():
   for entry in group:
    p=BED/(atlas[entry['bedrock_options']['icon']]['textures']+'.png');data=p.read_bytes()
    self.assertEqual(b'\x89PNG\r\n\x1a\n',data[:8]);w,h=struct.unpack('>II',data[16:24]);self.assertGreater(w*h,0)
 def test_all_png_chunks_are_binary_intact_including_the_legacy_bullet(self):
  for path in BED.rglob('*.png'):
   data=path.read_bytes();self.assertEqual(b'\x89PNG\r\n\x1a\n',data[:8],str(path));pos=8;ended=False
   while pos<len(data):
    n=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+n]
    crc=struct.unpack('>I',data[pos+8+n:pos+12+n])[0]
    self.assertEqual(crc,zlib.crc32(kind+body)&0xffffffff,str(path));pos+=n+12
    if kind==b'IEND':ended=True;break
   self.assertTrue(ended,str(path));self.assertEqual(pos,len(data),str(path))
 def test_uv_coordinates_stay_inside_the_model_texture(self):
  for i in ITEMS:
   g=geom(i);w=g['description']['texture_width'];h=g['description']['texture_height']
   for c in allcubes(i):
    for face,uv in c['uv'].items():
     for n,limit in [(0,w),(1,h)]:
      for value in [uv['uv'][n],uv['uv'][n]+uv['uv_size'][n]]:
       self.assertGreaterEqual(value,-.0001,(i['name'],face,value));self.assertLessEqual(value,limit+.0001,(i['name'],face,value))
 def test_model_bone_hierarchy_has_no_cycles_or_missing_parents(self):
  for i in ITEMS:
   bones={b['name']:b for b in geom(i)['bones']}
   for b in bones.values():
    seen=set();current=b
    while 'parent' in current:
     parent=current['parent'];self.assertIn(parent,bones);self.assertNotIn(parent,seen);seen.add(parent);current=bones[parent]
 def test_all_five_views_keep_all_three_java_rotation_axes(self):
  for i in ITEMS:
   animations=read(BED/'animations/endernation'/(i['name']+'.animation.json'))['animations']
   for view,t in i['views'].items():
    b=animations['animation.endernation.'+i['name']+'.'+view]['bones'];x,y,z=t['rotation']
    manual=read(ROOT/'bedrock-view-adjustments.json').get(i['name'],{}).get(view,{}).get('pose')
    if manual:
     self.assertEqual(manual,b['anchor']);self.assertEqual(3,len(manual['rotation']))
     self.assertTrue(all(math.isfinite(v) for v in manual['rotation']));continue
    self.assertEqual([-x,0,0],b['display_x']['rotation']);self.assertEqual([0,-y,0],b['display_y']['rotation']);self.assertEqual([0,0,z],b['display_z']['rotation'])
 def test_ak_third_person_x_rotation_is_not_silently_dropped(self):
  animations=read(BED/'animations/endernation/ak_47.animation.json')['animations']
  self.assertEqual(-116.65,animations['animation.endernation.ak_47.thirdperson_righthand']['bones']['display_x']['rotation'][0])
  self.assertNotEqual(animations['animation.endernation.ak_47.thirdperson_righthand'],animations['animation.endernation.ak_47.thirdperson_lefthand'])
 def test_slot_specific_animations_and_head_hide_are_wired(self):
  for p in (BED/'attachables/endernation/items').glob('*.json'):
   d=read(p)['minecraft:attachable']['description'];conditions={k:v for o in d['scripts']['animate'] for k,v in o.items()}
   self.assertIn("off_hand",conditions['firstperson_lefthand']);self.assertIn("main_hand",conditions['firstperson_righthand'])
   self.assertIn('head',conditions['hide_head']);self.assertEqual(6,len(d['animations']))
 def test_existing_manifest_ids_are_kept_and_version_is_incremented(self):
  m=read(BED/'manifest.json');self.assertEqual([1,21,15],m['header']['version'])
  self.assertEqual('5d41b684-e430-4efc-9043-7639f0047c33',m['header']['uuid'])
  self.assertNotEqual(m['header']['uuid'],m['modules'][0]['uuid']);self.assertEqual(m['header']['version'],m['modules'][0]['version'])
 def test_sound_assets_preserve_the_current_half_volume(self):
  defs=read(BED/'sounds/sound_definitions.json')['sound_definitions'];count=0
  for entry in read(ROOT/'assets/minecraft/sounds.json').values():
   for sound in entry['sounds']:
    if isinstance(sound,dict) and 'volume' in sound:self.assertEqual(.5,sound['volume'])
  for key,entry in defs.items():
   if not key.startswith('minecraft:'):continue
   for sound in entry['sounds']:
    self.assertTrue((BED/(sound['name']+'.ogg')).exists());self.assertEqual(b'OggS',(BED/(sound['name']+'.ogg')).read_bytes()[:4]);count+=1
  self.assertEqual(32,count)
 def test_all_custom_font_codepoint_pages_exist(self):
  count=0
  for provider in read(ROOT/'assets/minecraft/font/default.json')['providers']:
   if provider.get('type')!='bitmap':continue
   for row in provider['chars']:
    for char in row:
     if 0xE000<=ord(char)<=0xF8FF:
      self.assertTrue((BED/'font'/('glyph_'+format(ord(char)>>8,'02X')+'.png')).exists());count+=1
  self.assertEqual(73,count)
 def test_scoreboard_font_pixels_stay_at_the_java_text_height(self):
  pages={};checked=0
  for provider in read(ROOT/'assets/minecraft/font/default.json')['providers']:
   if provider.get('type')!='bitmap' or 'scoreboard/' not in provider['file']:continue
   for line in provider['chars']:
    for char in line:
     cp=ord(char)
     if cp not in range(0xE000,0xF900):continue
     page=cp>>8
     if page not in pages:pages[page]=rgba_rows(BED/'font'/('glyph_'+format(page,'02X')+'.png'))
     width,rows=pages[page];cell=width//16;x=(cp&15)*cell;y=((cp&255)>>4)*cell
     occupied=[dy for dy in range(cell) if any(rows[y+dy][4*x+3:4*(x+cell):4])]
     self.assertTrue(occupied,provider['file'])
     self.assertLessEqual(max(occupied)-min(occupied)+1,provider.get('height',8),provider['file'])
     self.assertLessEqual(abs(min(occupied)-(cell//2-4)),8,provider['file']);checked+=1
  self.assertGreaterEqual(checked,10)
 def test_archives_have_root_manifests_valid_crc_and_no_registry_metadata(self):
  out=ROOT/'dist/bedrock-compat-20261016'
  with zipfile.ZipFile(out/'EnderNation-Bedrock-26.3.mcpack') as z:
   self.assertIsNone(z.testzip());self.assertIn('manifest.json',z.namelist());self.assertTrue(all(not n.startswith('/') and '..' not in n.split('/') for n in z.namelist()))
  with zipfile.ZipFile(out/'EnderNation-Geyser-Mappings-26.3.zip') as z:self.assertEqual(['geyser_mappings.json'],z.namelist())
 def test_artifact_hashes_match_the_build_report(self):
  for name,item in REPORT['artifacts'].items():self.assertEqual(item['sha256'],sha(ROOT/'dist/bedrock-compat-20261016'/name))
if __name__=='__main__':unittest.main(verbosity=2)
