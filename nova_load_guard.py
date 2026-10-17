"""R196.8.4: conservative, corroborated marginal-load de-escalation.

The 1.18 boundary is a coaching heuristic rather than a physiological hard stop.
An isolated, slightly elevated acute/chronic ratio does not by itself prove
failure to recover; later quality timing, spacing and watt evidence still gate.
"""

def refine_training_state(state, metrics=None, feeling_trend=None, planning_context=None):
    if not isinstance(state, dict) or state.get('state') != 'RECOVERY':
        return state
    s = state
    if list(s.get('recovery_drivers') or []) != ['ACUTE_CHRONIC_LOAD']:
        return state
    p = planning_context if isinstance(planning_context, dict) else {}
    if p.get('health_override') or p.get('next_race'):
        return state
    m = metrics if isinstance(metrics, dict) else {}
    pb = m.get('personal_baselines') or {}
    hrv, rhr, sleep = (pb.get(k) or {} for k in ('hrv','rhr','sleep'))
    if (hrv.get('status') not in {'Within baseline', 'Above baseline'}
            or rhr.get('status') not in {'Within baseline', 'Below baseline'}
            or sleep.get('status') not in {'WITHIN HABITUAL', 'ABOVE HABITUAL'}
            or any((pb.get(k) or {}).get('color') in {'red','orange'} for k in ('hrv','rhr','sleep'))
            or m.get('sleep_quality') in (3,4)
            or (feeling_trend or {}).get('label') == 'TRENDING DOWN'):
        return state
    try:
        ratio=float(s.get('atl_ctl'))
        weekly=float(s.get('load_ratio'))
        growth=float(s.get('ctl_delta_28'))
        ramp=float(s.get('ramp_rate'))
    except (TypeError, ValueError, OverflowError):
        return state
    if not (1.18 <= ratio < 1.25 and 0 <= weekly <= 1.15
            and growth >= 1.5 and 0 <= ramp <= 5):
        return state
    out = dict(state)
    out.update({
        'state':'BUILD', 'state_class':'cyan', 'icon':'🏗️',
        'headline':'Continue a cautious build; recheck recovery before quality.',
        'why':('Only ATL/CTL is mildly elevated; weekly load is near the athlete’s prior '
               'baseline, chronic load is developing, and independent recovery markers '
               'are within habitual ranges. This is a watch condition, not proof of '
               'non-recovery. Hard work still needs a valid recovery window, dose and spacing.'),
        'load_caution_drivers':list(s.get('recovery_drivers') or []),
        'recovery_drivers':[],
        'load_gate_review':{
            'schema':'V4.9.95-R196.8.4-MARGINAL-LOAD-EVIDENCE-1',
            'state':'BORDERLINE_LOAD_WATCH_NOT_AUTOMATIC_HOLD',
            'atl_ctl':ratio,'load_ratio':weekly,
            'missing_sleep_quality_is_adverse':False,
            'hard_session_authorized':False,
            'rule':'Only one marginal load flag with corroborated recovery; downstream holds, workout evidence and quality spacing remain authoritative.'
        }
    })
    return out
