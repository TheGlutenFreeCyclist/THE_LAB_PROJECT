"""INC125: assemble byte-for-byte NOVA R145 from committed R143 on TEST only."""
from pathlib import Path
import hashlib

BASE = '7fa531e1439816d112054e3cba9fbc1bf27ccecf4d56141c28326db65529f3fb'
TARGET = 'b088cbb962d2a5d2a8fdef9a3cdb3bd23d8e89b539ede63b0b1c2c5c9dab7474'


def assemble(source, fragment):
    def once(old, new):
        nonlocal source
        assert source.count(old) == 1, 'R145 anchor drift: '+old[:80]
        source = source.replace(old, new, 1)
    once('<span class="r143-cta-icon" aria-hidden="true">＋</span>',
         '<span class="r143-cta-icon" aria-hidden="true">📅</span>')
    once('.r143-cta-icon{display:grid;place-items:center;font-size:20px;',
         '.r143-cta-icon{display:grid;place-items:center;font-size:19px;')
    once('        # R196.9.16 shadow-only exact references in the already-fetched history.\n',
         "        # INC125: observe a saved athlete window versus verified completed work.\n"
         "        # This sidecar is built AFTER all hard decisions, without modifying them.\n"
         "        data['quality_intent_reconciliation'] = _r145_quality_intent_observation(\n"
         "            user['id'], previous_training_blocks, now=get_rome_now())\n"
         '        # R196.9.16 shadow-only exact references in the already-fetched history.\n')
    once('  <button type="button" class="r143-open-dialog" data-r143-open="r143-quality-dialog"',
         "  {% set r145_observation = data.quality_intent_reconciliation or {} %}\n"
         "  {% if r145_observation.state == 'OBSERVED_AFTER_SAVED_AVAILABILITY' %}\n"
         "  <p class=\"r143-planning-notice\" role=\"status\">Your {{ r145_observation.observed_duration_min|e }} min quality was recorded on {{ r145_observation.intent_local_date|e }} at {{ r145_observation.observed_local_time|e }}. Your earlier availability was saved; it was not Nova execution clearance. Your next quality is a separate coaching decision.</p>\n"
         '  {% endif %}\n'
         '  <button type="button" class="r143-open-dialog" data-r143-open="r143-quality-dialog"')
    once("app.jinja_env.parse(HOME_PAGE)\nAPP_VERSION = ('THE LAB · R196.9.143 · INC123 COMPACT QUALITY AVAILABILITY DIALOG '\n"
         "               '· R142 TRAINING ENGINE UNCHANGED · HEALTH OBSERVATIONAL · LAB TEST CANDIDATE')\n",
         fragment + '\n' +
         "app.jinja_env.parse(HOME_PAGE)\nAPP_VERSION = ('THE LAB · R196.9.145 · INC125 SAVED INTENT VS VERIFIED QUALITY AUDIT '\n"
         "               '· R144 CALENDAR ICON · SCIENCE AND CLEARANCE UNCHANGED · LAB CANDIDATE')\n")
    return source


if __name__ == '__main__':
    candidate = Path('the_lab_app.py')
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == BASE, 'Wrong baseline — do not overwrite'
    fragment = Path('qa/r145_quality_intent_observation.fragment').read_text(encoding='utf-8')
    generated = assemble(candidate.read_text(encoding='utf-8'), fragment)
    assert hashlib.sha256(generated.encode('utf-8')).hexdigest() == TARGET, 'Generated R145 differs from approved local candidate'
    candidate.write_text(generated, encoding='utf-8')
    print('INC125: exact R145 assembled:', TARGET)
