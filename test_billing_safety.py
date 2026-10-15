import tempfile,unittest
from toapis_tools.toapis_async import ToAPIsClient,normalize_origin,build_request
class BillingSafety(unittest.TestCase):
 def test_uncertain_post_is_not_submitted_twice(self):
  with tempfile.TemporaryDirectory() as folder:
   client=ToAPIsClient('test-only-key',state_dir=folder);calls=[]
   def lost(path,body=None,*args):calls.append(path);raise OSError('Response lost')
   client._json=lost
   for _ in range(2):
    with self.assertRaises(RuntimeError):client.generate(model='gpt-image-2-vip',prompt='test',size='1024x1024')
   self.assertEqual(calls,['images/generations'])
 def test_reject_foreign_or_insecure_key_destination(self):
  for url in ['http://toapis.com','https://other.example/v1','https://user@toapis.com','https://toapis.com/other']:
   with self.assertRaises(ValueError):normalize_origin(url)
 def test_no_silent_multi_image_or_mask_mapping(self):
  for options in [{'n':2},{'mask':b'input'}]:
   with self.assertRaises(ValueError):build_request({'model':'gpt-image-2-vip','prompt':'test','size':'1024x1024',**options})
 def test_model_specific_resolution_mapping(self):
  vip,_=build_request({'model':'gpt-image-2-vip','prompt':'test','size':'1024x1024'})
  flare,_=build_request({'model':'gpt-image-2.5-flare','prompt':'test','size':'1024x1024'})
  self.assertEqual(vip['resolution'],'1K');self.assertEqual(vip['quality'],'low')
  self.assertNotIn('resolution',flare);self.assertEqual(flare['metadata']['resolution'],'1K')
if __name__=='__main__':unittest.main()
