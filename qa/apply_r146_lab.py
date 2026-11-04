"""INC126: exact audited R145 -> R146 producer-sidecar correction on TEST."""
from pathlib import Path
import hashlib

BASE = 'b088cbb962d2a5d2a8fdef9a3cdb3bd23d8e89b539ede63b0b1c2c5c9dab7474'
TARGET = 'f9ad64dc7770ed3ad21b165e0b7bcdf1645da4d6db5bf772385396d92023142c'


def assemble(source):
    def once(old, new):
        nonlocal source
        assert source.count(old) == 1, 'INC126 anchor drift'
        source = source.replace(old, new, 1)
    once("        data['quality_intent_reconciliation'] = _r145_quality_intent_observation(\n"
         "            user['id'], previous_training_blocks, now=get_rome_now())\n",
         "        data['quality_intent_reconciliation'] = _r145_quality_intent_observation(\n"
         "            user['id'], previous_training_blocks, now=get_rome_now(),\n"
         "            latest_feedback=latest_activity_feedback)\n")
    once('def _r145_quality_intent_observation(owner_id, blocks, now=None):',
         'def _r145_quality_intent_observation(owner_id, blocks, now=None, latest_feedback=None):')
    once("                mechanics_ok = (rep.get('activity_truth_status') == 'RESOLVED'\n"
         "                    and rep.get('activity_truth_source') == 'ICU_INTERVALS_CANONICAL'\n"
         "                    and int(rep.get('reps') or 0) == int(template.get('reps') or 0)\n",
         "                # Earlier block surfaces expose provenance directly, whereas\n"
         "                # the latest completed-quality audit independently attests\n"
         "                # the canonical interval structure for the SAME activity ID.\n"
         "                verified = (rep.get('activity_truth_status') == 'RESOLVED'\n"
         "                    and rep.get('activity_truth_source') == 'ICU_INTERVALS_CANONICAL')\n"
         "                attested = (isinstance(latest_feedback, dict)\n"
         "                    and latest_feedback.get('activity_id') == activity_id\n"
         "                    and latest_feedback.get('structure_status') == 'VERIFIED'\n"
         "                    and block.get('quality_relevant') is True)\n"
         "                mechanics_ok = ((verified or attested)\n"
         "                    and (rep.get('source') == 'ICU_INTERVALS_CANONICAL'\n"
         "                         or rep.get('activity_truth_source') == 'ICU_INTERVALS_CANONICAL')\n"
         "                    and int(rep.get('reps') or 0) == int(template.get('reps') or 0)\n")
    once("APP_VERSION = ('THE LAB · R196.9.145 · INC125 SAVED INTENT VS VERIFIED QUALITY AUDIT '\n"
         "               '· R144 CALENDAR ICON · SCIENCE AND CLEARANCE UNCHANGED · LAB CANDIDATE')",
         "APP_VERSION = ('THE LAB · R196.9.146 · INC126 VERIFIED SAME-ACTIVITY INTENT RECONCILIATION '\n"
         "               '· R144 CALENDAR ICON · SCIENCE AND CLEARANCE UNCHANGED · LAB CANDIDATE')")
    return source


if __name__ == '__main__':
    p = Path('the_lab_app.py')
    assert hashlib.sha256(p.read_bytes()).hexdigest() == BASE, 'Unexpected TEST baseline — fail closed'
    result = assemble(p.read_text(encoding='utf-8'))
    assert hashlib.sha256(result.encode('utf-8')).hexdigest() == TARGET, 'INC126 candidate differs from verified local bytes'
    p.write_text(result, encoding='utf-8')
    print('INC126: SHA-verified full R146', TARGET)
