"""INC108 integrity proof: an HMAC by itself is not issuer authority.

Exercise unmodified R136 seal verifier and HMAC signer with entirely invented
records. No new science conclusions, owner data, snapshots or DB connection.
"""
import copy
import os
import unittest
from unittest.mock import patch

for key in ("DATABASE_URL","THE_LAB_OWNER_DATABASE_URL","ICU_API_KEY",
            "ICU_ATHLETE_ID","GARMIN_EMAIL","GARMIN_PASSWORD",
            "ANTHROPIC_API_KEY","THE_LAB_STANDARD_AI_API_KEY",
            "THE_LAB_PLATFORM_AI_API_KEY"):
    os.environ[key]=""
os.environ["PRODUCT_SECURITY_STRICT"]="0"
from test_inc106_integrity_fuel import fully_compiled_synthetic_offer, STAGE_KEY
import the_lab_app as nova


class Inc108ForgeryResistance(unittest.TestCase):
    def test_mac_alone_cannot_promote_fabricated_science(self):
        offer=fully_compiled_synthetic_offer()
        audit={"state":"PASS","science_origin":"FABRICATED_SYNTHETIC"}
        with patch.object(nova,"SECRET_KEY",STAGE_KEY):
            signature=nova._nova_inc080_issuer_mac(offer,"inc108-owner",audit)
            self.assertEqual(len(signature or ""),64)
            offer.update(inc080_schema=nova.INC080_SCHEMA,
                         inc080_issuer_mac=signature)
            audit.update(inc080_schema=nova.INC080_SCHEMA,
                         inc080_issuer_mac=signature)
            self.assertFalse(nova._nova_inc076_seal_ok(offer,audit,"inc108-owner"),
                "Raw MAC must never substitute for prior scientific evidence seals")
            self.assertFalse(nova._nova_inc076_seal_ok(offer,audit,"inc108-other"),
                "Raw MAC cannot transfer across owners")

    def test_tampered_status_and_audit_block_even_with_copied_signature(self):
        offer=fully_compiled_synthetic_offer()
        audit={"state":"PASS","science_origin":"SYNTHETIC_ONLY"}
        with patch.object(nova,"SECRET_KEY",STAGE_KEY):
            mac=nova._nova_inc080_issuer_mac(offer,"inc108-owner",audit)
            self.assertTrue(mac)
            offer.update(inc080_schema=nova.INC080_SCHEMA,
                         inc080_issuer_mac=mac)
            audit.update(inc080_schema=nova.INC080_SCHEMA,
                         inc080_issuer_mac=mac)
            for mutate in ("revoked","audit_fail","watts_changed","date_changed"):
                with self.subTest(mutate=mutate):
                    o,a=copy.deepcopy(offer),copy.deepcopy(audit)
                    if mutate=="revoked": o["offer_status"]="REVOKED"
                    if mutate=="audit_fail": a["state"]="FAIL"
                    if mutate=="watts_changed":
                        o["workout"]["power_prescription"]["high_watts"]+=1
                    if mutate=="date_changed":o["workout"]["date"]="2026-11-06"
                    self.assertFalse(nova._nova_inc076_seal_ok(o,a,"inc108-owner"))

    def test_no_production_key_required_and_unscheduled_intent(self):
        offer=fully_compiled_synthetic_offer()
        audit={"state":"PASS"}
        self.assertIsNone(offer["workout"].get("date"))
        with patch.object(nova,"SECRET_KEY",""):
            self.assertIsNone(nova._nova_inc080_issuer_mac(offer,"inc108-owner",audit))
        with patch.object(nova,"SECRET_KEY",STAGE_KEY):
            with patch.object(nova,"_nova_inc076_composition_digest",return_value=None):
                self.assertIsNone(nova._nova_inc080_issuer_mac(offer,"inc108-owner",audit))


if __name__=="__main__":
    unittest.main(verbosity=2)
