"""INC132/BH-001 isolated candidate: display canonical Card3 even on C07 mirror.

This ONLY transforms a Jinja template. The original producer, attestations,
Card3 data and issuer remain untouched. Not a new workout or training authority.
"""


class Card3MirrorTemplateDrift(ValueError):
    pass


def apply_card3_mirror(home_page, grey_card):
    if not isinstance(home_page, str) or not isinstance(grey_card, str):
        raise Card3MirrorTemplateDrift('MALFORMED_TEMPLATE')
    if not grey_card or home_page.count(grey_card) != 1:
        raise Card3MirrorTemplateDrift('C07_GREY_CARD_ANCHOR_DRIFT')
    # Preserve the original enclosing {% endif %}: it now wraps the real Card3,
    # not a disabled placeholder. The "true" constant never grants authority.
    updated = home_page.replace(grey_card, '{% if true %}\n', 1)
    begin = ('{% if is_quality_slot %}\n'
             '{% set card3 = data.nova_card3_workout_view or {} %}\n'
             '{% if quality_already_shown %}\n')
    next_branch = '{% elif card3.verified_offer or card3.verified_future_plan %}'
    if updated.count(begin) != 1:
        raise Card3MirrorTemplateDrift('CANONICAL_VIEW_BRANCH_DRIFT')
    start = updated.index(begin)
    stop = updated.find(next_branch, start)
    if stop < 0 or stop - start > 1300:
        raise Card3MirrorTemplateDrift('CANONICAL_VIEW_NEXT_BRANCH_DRIFT')
    updated = (updated[:start]
        + '{% if is_quality_slot %}\n'
          '{% set card3 = data.nova_card3_workout_view or {} %}\n'
          '{% if card3.verified_offer or card3.verified_future_plan %}'
        + updated[stop + len(next_branch):])
    # This label is conditional on the exact ID and carries no extra schedule,
    # ledger, watt or training dose. A nonmatching Calendar HARD is NOT a copy.
    title_anchor = '<h3>{{ card3.title|e }}</h3>'
    if updated.count(title_anchor) != 1:
        raise Card3MirrorTemplateDrift('CANONICAL_TITLE_DRIFT')
    same_id = ("\n{% if quality_already_shown and upcoming.quality_index is not none "
               "and data.next_sessions and "
               "data.next_sessions[upcoming.quality_index].nova_workout_id == card3.workout_id %}"
               "\n<div class=\"inc132-shared-id\" role=\"note\">Same canonical workout as "
               "Card {{ upcoming.quality_index + 1 }} · one plan, no additional session</div>"
               "\n{% endif %}")
    updated = updated.replace(title_anchor, title_anchor + same_id, 1)
    if ('nova-card3-grey-placeholder' in updated
            or 'CARD3_GREY' in updated):
        raise Card3MirrorTemplateDrift('GREY_BRANCH_STILL_PRESENT')
    css = '''<style id="inc132-card3-mirror-style">
.inc132-shared-id{margin:7px 0;padding:8px 10px;border-radius:8px;
  border:1px solid rgba(90,200,200,.38);background:rgba(90,200,200,.07);
  color:#bddfe6;font-size:11px;line-height:1.5;overflow-wrap:anywhere}
</style>'''
    if updated.count('</head>') != 1:
        raise Card3MirrorTemplateDrift('HEAD_ANCHOR_DRIFT')
    updated = updated.replace('</head>', css + '\n</head>', 1)
    return updated
