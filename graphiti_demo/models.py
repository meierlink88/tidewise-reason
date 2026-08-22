from pydantic import BaseModel


class IndustryChain(BaseModel):
    """A stable industry-chain analysis anchor."""


class ChainNode(BaseModel):
    """A stable business or technical stage in an industry chain."""


class Evidence(BaseModel):
    """An immutable source-addressable factual record, not an analytical conclusion."""


class ResearchEvent(BaseModel):
    """A time-scoped occurrence extracted from Evidence before downstream interpretation."""


class VariableSignal(BaseModel):
    """A derived, time-bounded directional change on a controlled variable of one chain node."""


class ContainsNode(BaseModel):
    """The IndustryChain includes the ChainNode."""


class ComponentOf(BaseModel):
    """A source ChainNode is a physical or functional component of a target ChainNode."""


class DependsOn(BaseModel):
    """A source ChainNode depends on the target ChainNode."""


class InputTo(BaseModel):
    """A source ChainNode supplies a product or capability used by the target ChainNode."""


class Supports(BaseModel):
    """Evidence supports the ResearchEvent without turning the event into a source fact."""


class ProducesSignal(BaseModel):
    """A ResearchEvent produces a derived VariableSignal."""


class AppliesTo(BaseModel):
    """A VariableSignal applies to one stable ChainNode."""


ENTITY_TYPES = {
    "IndustryChain": IndustryChain,
    "ChainNode": ChainNode,
    "Evidence": Evidence,
    "ResearchEvent": ResearchEvent,
    "VariableSignal": VariableSignal,
}

EDGE_TYPES = {
    "ContainsNode": ContainsNode,
    "ComponentOf": ComponentOf,
    "DependsOn": DependsOn,
    "InputTo": InputTo,
    "Supports": Supports,
    "ProducesSignal": ProducesSignal,
    "AppliesTo": AppliesTo,
}

EDGE_TYPE_MAP = {
    ("IndustryChain", "ChainNode"): ["ContainsNode"],
    ("ChainNode", "ChainNode"): ["ComponentOf", "DependsOn", "InputTo"],
    ("Evidence", "ResearchEvent"): ["Supports"],
    ("ResearchEvent", "VariableSignal"): ["ProducesSignal"],
    ("VariableSignal", "ChainNode"): ["AppliesTo"],
}


def ontology_catalog() -> dict:
    """Return the versioned extraction schema that reasoning receives with graph facts."""
    entities = {
        name: {
            "description": model.__doc__,
            "json_schema": model.model_json_schema(),
        }
        for name, model in ENTITY_TYPES.items()
    }
    relations = {}
    for (source, target), names in EDGE_TYPE_MAP.items():
        for name in names:
            relations[name] = {
                "source": source,
                "target": target,
                "description": EDGE_TYPES[name].__doc__,
                "json_schema": EDGE_TYPES[name].model_json_schema(),
            }
    return {"version": "liquid-cooling-demo/v1", "entities": entities, "relations": relations}
