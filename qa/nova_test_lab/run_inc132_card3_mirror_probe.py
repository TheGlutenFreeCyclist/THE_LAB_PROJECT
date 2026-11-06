"""R150 real Jinja C07 regression in isolated TEST; does not certify science.

Build from actual R150 HOME_PAGE, do NOT mock its producer, issuer or source.
The production app is not modified by this probe.
"""
import json
import os
import sys
from pathlib import Path

for key in ('DATABASE_URL','THE_LAB_OWNER_DATABASE_URL','ICU_API_KEY',
            'ICU_ATHLETE_ID','GARMIN_EMAIL','GARMIN_PASSWORD',
            'ANTHROPIC_API_KEY','THE_LAB_STANDARD_AI_API_KEY',
            'THE_LAB_PLATFORM_AI_API_KEY'):
    os.environ[key] = ''
os.environ['THE_LAB_TEST_LAB_MODE'] = '1'
os.environ['PRODUCT_SECURITY_STRICT'] = '0'
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import the_lab_app as nova
from inc132_card3_mirror import apply_card3_mirror, Card3MirrorTemplateDrift


def run():
    assert nova.HOME_PAGE.count(nova._INC121_GREY_CARD) == 1, 'EXPECTED_R150_RED_NOT_REPRODUCED'
    page = apply_card3_mirror(nova.HOME_PAGE, nova._INC121_GREY_CARD)
    nova.app.jinja_env.parse(page)
    anchor = ('{% if is_quality_slot %}\n'
              '{% set card3 = data.nova_card3_workout_view or {} %}')
    assert page.count(anchor) == 1, 'SINGLE_CARD3_RENDERER_EXPECTED'
    start = page.index(anchor)
    stop = page.index('{% elif is_chronological_pending %}', start)
    segment = page[start:stop] + '{% endif %}'
    renderer = nova.app.jinja_env.from_string(segment)
    base = dict(verified_offer=False, verified_future_plan=True,
                title='CANONICAL TEST QUALITY', workout_id='P5_TEST_ID',
                personalized_watts='260–280 W',
                structure='3 x 10 min / 5 min easy',
                execution='not today', purpose='controlled progression',
                reason='future only', phases=[])

    def render(card, row_id):
        return renderer.render(
            is_quality_slot=True, is_chronological_pending=False,
            quality_already_shown=True, upcoming={'quality_index':0},
            data={'nova_card3_workout_view':card,
                  'next_sessions':[{'nova_workout_id':row_id,'title':'calendar row'}]})

    mirrored = render(base, 'P5_TEST_ID')
    assert 'CANONICAL TEST QUALITY' in mirrored
    assert '260–280 W' in mirrored
    assert 'Same canonical workout as Card 1' in mirrored
    assert mirrored.count('r1969104-single-workout') == 1
    assert 'Next quality already in your plan' not in mirrored

    unrelated = render(base, 'UNRELATED_HARD_CALENDAR_ID')
    assert 'CANONICAL TEST QUALITY' in unrelated
    assert 'Same canonical workout as Card 1' not in unrelated
    assert '260–280 W' in unrelated

    unproven = render(dict(title='GOAL_ONLY', verified_offer=False,
                            verified_future_plan=False), 'P5_TEST_ID')
    assert 'NO VERIFIED QUALITY WORKOUT' in unproven
    assert '260–280 W' not in unproven
    assert 'r1969104-single-workout' not in unproven
    try:
        apply_card3_mirror(page, nova._INC121_GREY_CARD)
        raise AssertionError('NON_IDEMPOTENT_TEMPLATE_PATCH_DID_NOT_FAIL_CLOSED')
    except Card3MirrorTemplateDrift:
        pass

    print(json.dumps({
        'suite':'INC132_BH001_C07_REAL_JINJA_OVERLAY',
        'status':'PASS_TEST_OVERLAY_ONLY',
        'original_r150_grey_branch':'RED_REPRODUCED',
        'canonical_card3_on_same_id':'RENDERED_ONE_PLAN',
        'canonical_card3_on_unrelated_calendar_hard':'PRESERVED',
        'incomplete_card3':'CLEARLY_NOT_VERIFIED',
        'template_parser':'PASS',
        'app_source_changed':False,
        'card2_quality':'NOT_IMPLEMENTED',
        'live_authenticated_e2e':'NOT_VERIFIED',
        'release':'NO_GO'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(run())
    except Exception as e:
        print(json.dumps({'suite':'INC132_BH001_C07_REAL_JINJA_OVERLAY',
            'status':'BLOCKED', 'error_class':type(e).__name__,
            'safe_error_code':str(e) if isinstance(e, Card3MirrorTemplateDrift) else 'OTHER',
            'release':'NO_GO'}))
        raise SystemExit(2)
