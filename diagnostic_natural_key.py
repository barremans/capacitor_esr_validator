# diagnostic_natural_key.py
from types import SimpleNamespace
from app.services.exchange.export_service import bereken_natural_key
from app.services.exchange.import_planner import ImportPlanner
from app.storage.models import MeasurementMethod, SampleState
from tests.test_exchange_import_planner import _chain, _detail_voor_chain, _StubHistory

chain = _chain()
detail = _detail_voor_chain(chain, measurement_id=1)

# Key 1: uit de keten (zoals de export hem heeft meegeschreven)
print("chain.natural_key =", chain.natural_key)

# Key 2: uit het detail, zoals de planner hem herberekent
planner = ImportPlanner(history_service=_StubHistory({}))
key_uit_detail = planner._natural_key_uit_detail(detail)
print("key_uit_detail   =", key_uit_detail)

# Toon de canonieke dicts
from app.services.exchange.export_service import (
    _COMPONENT_MODEL_FIELDS, _COMPONENT_SAMPLE_FIELDS,
    _MEASUREMENT_SESSION_FIELDS, _MEASUREMENT_FIELDS,
    _ASSESSMENT_FIELDS, _REFERENCE_FIELDS, _velden_uit_model,
)
print("chain.component_model    =", dict(chain.component_model))
print("detail.component_model   =", _velden_uit_model(detail["component_model"], _COMPONENT_MODEL_FIELDS))
print("chain.component_sample   =", dict(chain.component_sample))
print("detail.component_sample  =", _velden_uit_model(detail["component_sample"], _COMPONENT_SAMPLE_FIELDS))
print("chain.measurement_session=", dict(chain.measurement_session))
print("detail.measurement_session=", _velden_uit_model(detail["measurement_session"], _MEASUREMENT_SESSION_FIELDS))
print("chain.measurement        =", dict(chain.measurement))
print("detail.measurement       =", _velden_uit_model(detail["measurement"], _MEASUREMENT_FIELDS))