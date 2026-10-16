"""R196.6 regression anchors. No real account or network access required."""
import ast, pathlib, unittest
p=pathlib.Path(__file__).resolve().parents[1]/'the_lab_app.py'
s=p.read_text(encoding='utf-8')
class PolicyAnchors(unittest.TestCase):
 def test_ftp_gate(self):
  self.assertIn('R1966_MIN_FTP_EFFORT_SECONDS = 1200',s)
  self.assertIn('secs >= R1966_MIN_FTP_EFFORT_SECONDS',s)
  self.assertIn('R1966_MIN_SUPPORTED_FTP_SECONDS = 1800',s)
 def test_exploratory_contract(self):
  self.assertIn('EXPLORATORY POWER TARGET',s)
  self.assertIn("'confidence': 'LOW', 'exploratory': True, 'non_punitive': True",s)
  self.assertIn("'state': 'EXPLORATORY_NOT_GRADED'",s)
 def test_checkpoint(self):
  self.assertIn('R1966_CHECKPOINT_FRESH_DAYS = 21',s)
  self.assertIn("'test_state': 'COMPLETED', 'test_due': False",s)
 def test_ui(self):
  self.assertIn('RECENT POWER BEST',s)
  self.assertIn('NO TEST-BACKED ESTIMATE',s)
 def test_compiles(self):
  compile(s,str(p),'exec')
if __name__=='__main__':unittest.main()
